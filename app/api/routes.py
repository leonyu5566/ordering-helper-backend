# =============================================================================
# 檔案名稱：app/api/routes.py
# 功能描述：定義所有 API 端點，處理 LIFF 前端的 HTTP 請求
# 主要職責：
# - 提供店家資料查詢 API（合作店家）
# - 處理菜單圖片 OCR 和翻譯（非合作店家）
# - 處理訂單建立
# - 處理使用者註冊
# 支援功能：
# - 多語言菜單顯示
# - 菜單圖片 OCR 處理
# - 訂單語音生成
# =============================================================================

from flask import Blueprint, jsonify, request, send_file
from ..models import db, Store, Menu, MenuItem, MenuTranslation, User, Order, OrderItem, StoreTranslation, GeminiProcessing, VoiceFile, Language
from .helpers import process_menu_with_gemini, generate_voice_order, create_order_summary, save_uploaded_file
import json
import os
from werkzeug.utils import secure_filename
import datetime
import uuid

# =============================================================================
# CORS 處理函數
# 功能：統一處理 OPTIONS 預檢請求
# =============================================================================
def handle_cors_preflight():
    """處理 CORS 預檢請求"""
    response = jsonify({'message': 'OK'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response, 200

# =============================================================================
# Blueprint 建立區塊
# 功能：建立 API Blueprint，用於組織所有 API 路由
# 作用：將所有 API 端點統一註冊到 /api 路徑下
# =============================================================================
api_bp = Blueprint('api', __name__)

# =============================================================================
# 檔案上傳設定區塊
# 功能：定義檔案上傳的相關設定
# 包含：
# - UPLOAD_FOLDER：上傳檔案的儲存目錄
# - ALLOWED_EXTENSIONS：允許上傳的檔案格式
# - allowed_file()：檢查檔案格式是否合法的函數
# 用途：用於菜單圖片上傳功能
# =============================================================================
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =============================================================================
# 核心 API 端點
# 功能：提供 LIFF 前端所需的核心功能
# =============================================================================

@api_bp.route('/stores/<int:store_id>', methods=['GET'])
def get_store(store_id):
    """取得店家資訊（支援多語言翻譯）"""
    try:
        # 取得使用者語言偏好
        user_language = request.args.get('lang', 'zh')
        
        store = Store.query.get(store_id)
        if not store:
            return jsonify({"error": "找不到店家"}), 404
        
        # 使用新的翻譯功能（優先使用資料庫翻譯）
        from .helpers import translate_store_info_with_db_fallback
        translated_store = translate_store_info_with_db_fallback(store, user_language)
        
        return jsonify({
            "store_id": store.store_id,
            "user_language": user_language,
            "store_info": translated_store
        })
        
    except Exception as e:
        return jsonify({'error': '無法載入店家資訊'}), 500

@api_bp.route('/menu/<int:store_id>', methods=['GET'])
def get_menu(store_id):
    """取得店家菜單（支援多語言翻譯，優先使用資料庫翻譯）"""
    try:
        # 取得使用者語言偏好
        user_language = request.args.get('lang', 'zh')
        
        # 先檢查店家是否存在
        store = Store.query.get(store_id)
        if not store:
            return jsonify({"error": "找不到店家"}), 404
        
        # 嘗試查詢菜單項目
        try:
            menu_items = MenuItem.query.filter_by(store_id=store_id).all()
        except Exception as e:
            # 如果表格不存在，返回友好的錯誤訊息
            return jsonify({
                "error": "此店家目前沒有菜單資料",
                "store_id": store_id,
                "store_name": store.store_name,
                "message": "請使用菜單圖片上傳功能來建立菜單"
            }), 404
        
        if not menu_items:
            return jsonify({
                "error": "此店家目前沒有菜單項目",
                "store_id": store_id,
                "store_name": store.store_name,
                "message": "請使用菜單圖片上傳功能來建立菜單"
            }), 404
        
        # 使用新的翻譯功能（優先使用資料庫翻譯）
        from .helpers import translate_menu_items_with_db_fallback
        translated_menu = translate_menu_items_with_db_fallback(menu_items, user_language)
        
        # 統計翻譯來源
        db_translations = sum(1 for item in translated_menu if item['translation_source'] == 'database')
        ai_translations = sum(1 for item in translated_menu if item['translation_source'] == 'ai')
        
        return jsonify({
            "store_id": store_id,
            "user_language": user_language,
            "menu_items": translated_menu,
            "translation_stats": {
                "database_translations": db_translations,
                "ai_translations": ai_translations,
                "total_items": len(translated_menu)
            }
        })
        
    except Exception as e:
        return jsonify({'error': '無法載入菜單'}), 500

@api_bp.route('/stores/check-partner-status', methods=['GET'])
def check_partner_status():
    """檢查店家合作狀態"""
    store_id = request.args.get('store_id', type=int)
    if not store_id:
        return jsonify({"error": "需要提供店家ID"}), 400
    
    try:
        store = Store.query.get(store_id)
        if not store:
            return jsonify({"error": "找不到店家"}), 404
        
        return jsonify({
            "store_id": store.store_id,
            "store_name": store.store_name,
            "partner_level": store.partner_level,
            "is_partner": store.partner_level > 0,
            "has_menu": bool(store.menus and len(store.menus) > 0)
        })
        
    except Exception as e:
        return jsonify({'error': '無法檢查店家狀態'}), 500

@api_bp.route('/menu/process-ocr', methods=['POST', 'OPTIONS'])
def process_menu_ocr():
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    """處理菜單圖片 OCR 並生成動態菜單（非合作店家）"""
    # 檢查是否有檔案（支援 'file' 和 'image' 參數）
    file = None
    if 'file' in request.files:
        file = request.files['file']
        print("使用 'file' 參數")
    elif 'image' in request.files:
        file = request.files['image']
        print("使用 'image' 參數")
    else:
        print("錯誤：沒有找到 'file' 或 'image' 欄位")
        print(f"可用的檔案欄位: {list(request.files.keys())}")
        return jsonify({
            "error": "沒有上傳檔案",
            "message": "請使用 'file' 或 'image' 參數上傳檔案",
            "available_fields": list(request.files.keys())
        }), 400
    if file.filename == '':
        return jsonify({"error": "沒有選擇檔案"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "不支援的檔案格式"}), 400
    
    # 取得參數
    store_id = request.form.get('store_id', type=int)
    user_id = request.form.get('user_id', type=int)
    target_lang = request.form.get('lang', 'en')
    
    if not store_id:
        return jsonify({"error": "需要提供店家ID"}), 400
    
    try:
        # 儲存上傳的檔案
        filepath = save_uploaded_file(file)
        
        # 建立 Gemini 處理記錄
        processing = GeminiProcessing(
            user_id=user_id or 1,  # 如果沒有使用者ID，使用預設值
            store_id=store_id,
            image_url=filepath,
            status='processing'
        )
        db.session.add(processing)
        db.session.commit()
        
        # 使用 Gemini API 處理圖片
        print("開始使用 Gemini API 處理圖片...")
        result = process_menu_with_gemini(filepath, target_lang)
        
        # 檢查處理結果
        if result and result.get('success', False):
            # 更新處理狀態
            processing.status = 'completed'
            processing.ocr_result = json.dumps(result, ensure_ascii=False)
            processing.structured_menu = json.dumps(result, ensure_ascii=False)
            db.session.commit()
            
            # 生成動態菜單資料
            menu_items = result.get('menu_items', [])
            dynamic_menu = []
            
            for i, item in enumerate(menu_items):
                # 確保所有字串欄位都不是 null/undefined，避免前端 charAt() 錯誤
                # 並提供前端需要的所有必要欄位
                dynamic_menu.append({
                    'temp_id': f"temp_{processing.processing_id}_{i}",
                    'id': f"temp_{processing.processing_id}_{i}",  # 前端可能需要 id 欄位
                    'original_name': str(item.get('original_name', '') or ''),
                    'translated_name': str(item.get('translated_name', '') or ''),
                    'en_name': str(item.get('translated_name', '') or ''),  # 英語名稱
                    'price': item.get('price', 0),
                    'price_small': item.get('price', 0),  # 小份價格
                    'price_large': item.get('price', 0),  # 大份價格
                    'description': str(item.get('description', '') or ''),
                    'category': str(item.get('category', '') or '其他'),
                    'image_url': '/static/images/default-dish.png',  # 預設圖片
                    'imageUrl': '/static/images/default-dish.png',  # 前端可能用這個欄位名
                    'inventory': 999,  # 庫存數量
                    'available': True,  # 是否可購買
                    'processing_id': processing.processing_id
                })
            
            response = jsonify({
                "message": "菜單處理成功",
                "processing_id": processing.processing_id,
                "store_info": result.get('store_info', {}),
                "menu_items": dynamic_menu,
                "total_items": len(dynamic_menu),
                "target_language": target_lang,
                "processing_notes": result.get('processing_notes', '')
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            
            # 加入 API 回應的除錯 log
            print(f"🎉 API 成功回應 201 Created")
            print(f"📊 回應統計:")
            print(f"  - 處理ID: {processing.processing_id}")
            print(f"  - 菜單項目數: {len(dynamic_menu)}")
            print(f"  - 目標語言: {target_lang}")
            print(f"  - 店家資訊: {result.get('store_info', {})}")
            print(f"  - 處理備註: {result.get('processing_notes', '')}")
            
            return response, 201
        else:
            # 處理失敗 - 只有在真正的錯誤時才返回 422
            processing.status = 'failed'
            db.session.commit()
            
            # 檢查是否是 JSON 解析錯誤或其他可恢復的錯誤
            error_message = result.get('error', '菜單處理失敗，請重新拍攝清晰的菜單照片')
            processing_notes = result.get('processing_notes', '')
            
            # 如果是 JSON 解析錯誤或其他可恢復的錯誤，返回 422
            if 'JSON 解析失敗' in error_message or 'extra_forbidden' in error_message:
                print(f"❌ API 返回 422 錯誤")
                print(f"🔍 錯誤詳情:")
                print(f"  - 錯誤訊息: {error_message}")
                print(f"  - 處理備註: {processing_notes}")
                print(f"  - 處理ID: {processing.processing_id}")
                
                response = jsonify({
                    "error": error_message,
                    "processing_notes": processing_notes
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 422
            else:
                # 其他錯誤返回 500
                print(f"❌ API 返回 500 錯誤")
                print(f"🔍 錯誤詳情:")
                print(f"  - 錯誤訊息: {error_message}")
                print(f"  - 處理備註: {processing_notes}")
                print(f"  - 處理ID: {processing.processing_id}")
                
                response = jsonify({
                    "error": error_message,
                    "processing_notes": processing_notes
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 500
    
    except Exception as e:
        print(f"OCR處理失敗：{e}")
        return jsonify({"error": "處理過程中發生錯誤"}), 500

@api_bp.route('/orders', methods=['POST', 'OPTIONS'])
def create_order():
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    """建立訂單（合作店家）"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "請求資料為空"}), 400
    
    # 檢查必要欄位
    required_fields = ['store_id', 'items']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            "error": "訂單資料不完整",
            "missing_fields": missing_fields,
            "received_data": list(data.keys())
        }), 400

    # 處理 line_user_id（可選）
    line_user_id = data.get('line_user_id')
    if not line_user_id:
        # 為非 LINE 入口生成臨時 ID
        import uuid
        line_user_id = f"guest_{uuid.uuid4().hex[:8]}"
        guest_mode = True
    else:
        guest_mode = False

    # 查找或創建使用者
    user = User.query.filter_by(line_user_id=line_user_id).first()
    if not user:
        try:
            # 檢查語言是否存在，如果不存在就使用預設語言
            preferred_lang = data.get('language', 'zh')
            language = Language.query.get(preferred_lang)
            if not language:
                # 如果指定的語言不存在，使用中文作為預設
                preferred_lang = 'zh'
                language = Language.query.get(preferred_lang)
                if not language:
                    # 如果連中文都不存在，創建基本語言資料
                    from tools.manage_translations import init_languages
                    init_languages()
            
            # 為訪客創建臨時使用者
            user = User(
                line_user_id=line_user_id,
                preferred_lang=preferred_lang,
                created_at=datetime.datetime.utcnow()
            )
            db.session.add(user)
            db.session.flush()  # 先產生 user_id，但不提交
            # 注意：這裡不需要 commit，因為後面會一起提交訂單
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "error": "建立使用者失敗",
                "details": str(e)
            }), 500

    total_amount = 0
    order_items_to_create = []
    order_details = []
    validation_errors = []
    
    for i, item_data in enumerate(data['items']):
        # 支援多種欄位名稱格式
        menu_item_id = item_data.get('menu_item_id') or item_data.get('id') or item_data.get('menu_item_id')
        quantity = item_data.get('quantity') or item_data.get('qty') or item_data.get('quantity_small')
        
        if not menu_item_id:
            validation_errors.append(f"項目 {i+1}: 缺少 menu_item_id 或 id 欄位")
            continue
            
        if not quantity:
            validation_errors.append(f"項目 {i+1}: 缺少 quantity 或 qty 欄位")
            continue
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                validation_errors.append(f"項目 {i+1}: 數量必須大於 0")
                continue
        except (ValueError, TypeError):
            validation_errors.append(f"項目 {i+1}: 數量格式錯誤，必須是整數")
            continue
        
        # 檢查是否為臨時菜單項目（以 temp_ 開頭）
        if menu_item_id.startswith('temp_'):
            # 處理臨時菜單項目
            price = item_data.get('price') or item_data.get('price_small') or item_data.get('price_unit') or 0
            item_name = item_data.get('item_name') or item_data.get('name') or item_data.get('original_name') or f"項目 {i+1}"
            
            try:
                price = float(price)
                if price < 0:
                    validation_errors.append(f"項目 {i+1}: 價格不能為負數")
                    continue
            except (ValueError, TypeError):
                validation_errors.append(f"項目 {i+1}: 價格格式錯誤，必須是數字")
                continue
            
            subtotal = int(price * quantity)
            total_amount += subtotal
            
            # 為臨時項目創建一個臨時的 MenuItem 記錄
            try:
                # 檢查是否已經有對應的臨時菜單項目
                temp_menu_item = MenuItem.query.filter_by(item_name=item_name).first()
                
                if not temp_menu_item:
                    # 創建新的臨時菜單項目
                    from app.models import Menu, Store
                    
                    # 確保店家存在，如果不存在則創建預設店家
                    store_id = data.get('store_id')
                    if not store_id:
                        # 如果沒有 store_id，創建一個預設店家
                        default_store = Store.query.filter_by(store_name='預設店家').first()
                        if not default_store:
                            default_store = Store(
                                store_name='預設店家',
                                partner_level=0,  # 非合作店家
                                created_at=datetime.datetime.utcnow()
                            )
                            db.session.add(default_store)
                            db.session.flush()
                        store_id = default_store.store_id
                        # 更新請求資料中的 store_id
                        data['store_id'] = store_id
                    
                    # 找到或創建一個臨時菜單
                    temp_menu = Menu.query.filter_by(store_id=store_id).first()
                    if not temp_menu:
                        temp_menu = Menu(store_id=store_id, version=1)
                        db.session.add(temp_menu)
                        db.session.flush()
                    
                    temp_menu_item = MenuItem(
                        menu_id=temp_menu.menu_id,
                        item_name=item_name,
                        price_small=int(price),
                        price_big=int(price)  # 使用相同價格
                    )
                    db.session.add(temp_menu_item)
                    db.session.flush()  # 獲取 menu_item_id
                
                # 使用臨時菜單項目的 ID
                order_items_to_create.append(OrderItem(
                    menu_item_id=temp_menu_item.menu_item_id,
                    quantity_small=quantity,
                    subtotal=subtotal
                ))
                
                # 建立訂單明細供確認
                order_details.append({
                    'menu_item_id': temp_menu_item.menu_item_id,
                    'item_name': item_name,
                    'quantity': quantity,
                    'price': price,
                    'subtotal': subtotal,
                    'is_temp': True
                })
                
            except Exception as e:
                validation_errors.append(f"項目 {i+1}: 創建臨時菜單項目失敗 - {str(e)}")
                continue
        else:
            # 處理正式菜單項目
            menu_item = MenuItem.query.get(menu_item_id)
            if not menu_item:
                validation_errors.append(f"項目 {i+1}: 找不到菜單項目 ID {menu_item_id}")
                continue
            
            subtotal = menu_item.price_small * quantity
            total_amount += subtotal
            
            order_items_to_create.append(OrderItem(
                menu_item_id=menu_item.menu_item_id,
                quantity_small=quantity,
                subtotal=subtotal
            ))
            
            # 建立訂單明細供確認
            order_details.append({
                'menu_item_id': menu_item.menu_item_id,
                'item_name': menu_item.item_name,
                'quantity': quantity,
                'price': menu_item.price_small,
                'subtotal': subtotal,
                'is_temp': False
            })

    if validation_errors:
        return jsonify({
            "error": "訂單資料驗證失敗",
            "validation_errors": validation_errors,
            "received_items": data['items']
        }), 400

    if not order_items_to_create:
        return jsonify({
            "error": "沒有選擇任何商品",
            "received_items": data['items']
        }), 400

    try:
        new_order = Order(
            user_id=user.user_id,
            store_id=data['store_id'],
            total_amount=total_amount,
            items=order_items_to_create
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        # 建立完整訂單確認內容
        from .helpers import create_complete_order_confirmation, send_complete_order_notification, generate_voice_order
        
        order_confirmation = create_complete_order_confirmation(new_order.order_id, user.preferred_lang)
        
        # 生成中文語音檔
        voice_path = generate_voice_order(new_order.order_id)
        
        # 只在非訪客模式下發送 LINE 通知
        if not guest_mode:
            send_complete_order_notification(new_order.order_id)
        
        return jsonify({
            "message": "訂單建立成功", 
            "order_id": new_order.order_id,
            "order_details": order_details,
            "total_amount": total_amount,
            "confirmation": order_confirmation,
            "voice_generated": voice_path is not None
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "訂單建立失敗",
            "details": str(e)
        }), 500

@api_bp.route('/orders/temp', methods=['POST', 'OPTIONS'])
def create_temp_order():
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    """建立臨時訂單（非合作店家）"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "請求資料為空"}), 400
    
    # 檢查必要欄位
    required_fields = ['processing_id', 'items']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            "error": "訂單資料不完整",
            "missing_fields": missing_fields,
            "received_data": list(data.keys())
        }), 400
    
    try:
        # 取得處理記錄
        processing = GeminiProcessing.query.get(data['processing_id'])
        if not processing:
            return jsonify({"error": "找不到處理記錄"}), 404
        
        # 計算總金額和建立訂單明細
        total_amount = 0
        order_details = []
        validation_errors = []
        
        for i, item in enumerate(data['items']):
            # 支援多種欄位名稱格式
            quantity = item.get('quantity') or item.get('qty') or item.get('quantity_small')
            price = item.get('price_small') or item.get('price') or item.get('price_unit')
            original_name = item.get('original_name') or item.get('item_name') or item.get('name')
            
            if not quantity:
                validation_errors.append(f"項目 {i+1}: 缺少 quantity 或 qty 欄位")
                continue
                
            if not price:
                validation_errors.append(f"項目 {i+1}: 缺少 price 或 price_small 欄位")
                continue
                
            if not original_name:
                validation_errors.append(f"項目 {i+1}: 缺少 original_name 或 item_name 欄位")
                continue
            
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    validation_errors.append(f"項目 {i+1}: 數量必須大於 0")
                    continue
            except (ValueError, TypeError):
                validation_errors.append(f"項目 {i+1}: 數量格式錯誤，必須是整數")
                continue
                
            try:
                price = float(price)
                if price < 0:
                    validation_errors.append(f"項目 {i+1}: 價格不能為負數")
                    continue
            except (ValueError, TypeError):
                validation_errors.append(f"項目 {i+1}: 價格格式錯誤，必須是數字")
                continue
            
            subtotal = price * quantity
            
            if quantity > 0:
                total_amount += subtotal
                order_details.append({
                    'temp_id': item.get('temp_id') or item.get('id'),
                    'original_name': original_name,
                    'translated_name': item.get('translated_name') or original_name,
                    'quantity': quantity,
                    'price': price,
                    'price_small': price,  # 確保前端需要的欄位存在
                    'subtotal': subtotal
                })
        
        if validation_errors:
            return jsonify({
                "error": "訂單資料驗證失敗",
                "validation_errors": validation_errors,
                "received_items": data['items']
            }), 400
        
        if not order_details:
            return jsonify({
                "error": "沒有選擇任何商品",
                "received_items": data['items']
            }), 400
        
        # 建立臨時訂單記錄
        temp_order = {
            "processing_id": data['processing_id'],
            "store_id": processing.store_id,
            "items": order_details,
            "total_amount": total_amount,
            "order_time": datetime.datetime.now().isoformat()
        }
        
        # 生成中文語音檔（基於原始中文菜名）
        from .helpers import generate_voice_from_temp_order, send_temp_order_notification
        voice_path = generate_voice_from_temp_order(temp_order)
        
        # 發送 LINE Bot 通知（如果使用者ID存在）
        user_id = data.get('user_id')
        user_language = data.get('lang', 'zh')
        
        if user_id:
            # 這裡需要根據使用者ID取得 LINE user ID
            # 暫時使用處理記錄中的使用者ID
            from ..models import User
            user = User.query.get(processing.user_id)
            if user:
                send_temp_order_notification(temp_order, user.line_user_id, user.preferred_lang)
        
        return jsonify({
            "message": "臨時訂單建立成功",
            "order_data": temp_order,
            "voice_generated": voice_path is not None
        }), 201
        
    except Exception as e:
        return jsonify({"error": "建立訂單失敗"}), 500

@api_bp.route('/orders/<int:order_id>/confirm', methods=['GET'])
def get_order_confirmation(order_id):
    """取得訂單確認資訊"""
    try:
        from ..models import Order, OrderItem, MenuItem, Store, User
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "找不到訂單"}), 404
        
        store = Store.query.get(order.store_id)
        user = User.query.get(order.user_id)
        
        # 建立訂單明細
        order_details = []
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                order_details.append({
                    'item_name': menu_item.item_name,
                    'quantity': item.quantity_small,
                    'price': menu_item.price_small,
                    'subtotal': item.subtotal
                })
        
        # 建立完整訂單確認內容
        from .helpers import create_complete_order_confirmation
        confirmation = create_complete_order_confirmation(order_id, user.preferred_lang)
        
        return jsonify({
            "order_id": order.order_id,
            "store_name": store.store_name,
            "order_details": order_details,
            "total_amount": order.total_amount,
            "order_time": order.order_time.isoformat(),
            "confirmation": confirmation
        })
        
    except Exception as e:
        return jsonify({"error": "取得訂單確認資訊失敗"}), 500

@api_bp.route('/orders/<int:order_id>/voice', methods=['GET'])
def get_order_voice(order_id):
    """取得訂單語音檔"""
    try:
        from .helpers import generate_voice_order
        
        # 檢查訂單是否存在
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "找不到訂單"}), 404
        
        # 取得語速參數
        speech_rate = request.args.get('rate', 1.0, type=float)
        speech_rate = max(0.5, min(2.0, speech_rate))  # 限制語速範圍 0.5-2.0
        
        # 生成語音檔
        voice_path = generate_voice_order(order_id, speech_rate)
        
        if voice_path and os.path.exists(voice_path):
            return send_file(voice_path, as_attachment=True, download_name=f"order_{order_id}.wav")
        else:
            return jsonify({"error": "語音檔生成失敗"}), 500
            
    except Exception as e:
        return jsonify({"error": "取得語音檔失敗"}), 500

@api_bp.route('/orders/history', methods=['GET'])
def get_order_history():
    """取得使用者訂單記錄"""
    try:
        line_user_id = request.args.get('line_user_id')
        if not line_user_id:
            return jsonify({"error": "需要提供使用者ID"}), 400
        
        # 查詢使用者
        user = User.query.filter_by(line_user_id=line_user_id).first()
        if not user:
            return jsonify({"error": "找不到使用者"}), 404
        
        # 查詢訂單記錄（最近20筆）
        orders = Order.query.filter_by(user_id=user.user_id).order_by(Order.order_time.desc()).limit(20).all()
        
        order_history = []
        for order in orders:
            store = Store.query.get(order.store_id)
            
            # 取得訂單項目
            order_items = []
            for item in order.items:
                menu_item = MenuItem.query.get(item.menu_item_id)
                if menu_item:
                    order_items.append({
                        'item_name': menu_item.item_name,
                        'quantity': item.quantity_small,
                        'price': menu_item.price_small,
                        'subtotal': item.subtotal
                    })
            
            order_data = {
                'order_id': order.order_id,
                'store_name': store.store_name if store else "Unknown Store",
                'store_id': order.store_id,
                'order_time': order.order_time.isoformat(),
                'total_amount': order.total_amount,
                'status': order.status,
                'items': order_items,
                'item_count': len(order_items)
            }
            order_history.append(order_data)
        
        return jsonify({
            'user_id': user.user_id,
            'line_user_id': user.line_user_id,
            'preferred_language': user.preferred_lang,
            'total_orders': len(order_history),
            'orders': order_history
        })
        
    except Exception as e:
        return jsonify({"error": "查詢訂單記錄失敗"}), 500

@api_bp.route('/orders/<int:order_id>/details', methods=['GET'])
def get_order_details(order_id):
    """取得訂單詳細資訊"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "找不到訂單"}), 404
        
        store = Store.query.get(order.store_id)
        user = User.query.get(order.user_id)
        
        # 取得訂單項目
        order_items = []
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                order_items.append({
                    'item_name': menu_item.item_name,
                    'quantity': item.quantity_small,
                    'price': menu_item.price_small,
                    'subtotal': item.subtotal
                })
        
        # 建立完整訂單確認內容
        from .helpers import create_complete_order_confirmation
        confirmation = create_complete_order_confirmation(order_id, user.preferred_lang)
        
        order_details = {
            'order_id': order.order_id,
            'store_name': store.store_name if store else "Unknown Store",
            'store_id': order.store_id,
            'order_time': order.order_time.isoformat(),
            'total_amount': order.total_amount,
            'status': order.status,
            'items': order_items,
            'item_count': len(order_items),
            'user_language': user.preferred_lang,
            'confirmation': confirmation
        }
        
        return jsonify(order_details)
        
    except Exception as e:
        return jsonify({"error": "取得訂單詳細資訊失敗"}), 500

@api_bp.route('/voice/generate', methods=['POST'])
def generate_custom_voice():
    """生成自定義語音檔"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "缺少文字內容"}), 400
        
        text = data['text']
        speech_rate = data.get('rate', 1.0, type=float)
        voice_name = data.get('voice', 'zh-TW-HsiaoChenNeural')
        
        # 限制語速範圍
        speech_rate = max(0.5, min(2.0, speech_rate))
        
        from .helpers import generate_voice_with_custom_rate
        voice_path = generate_voice_with_custom_rate(text, speech_rate, voice_name)
        
        if voice_path and os.path.exists(voice_path):
            return send_file(voice_path, as_attachment=True, download_name=f"custom_voice_{uuid.uuid4()}.wav")
        else:
            return jsonify({"error": "語音檔生成失敗"}), 500
            
    except Exception as e:
        return jsonify({"error": "生成語音檔失敗"}), 500

@api_bp.route('/users/register', methods=['POST'])
def register_user():
    """使用者註冊"""
    data = request.get_json()
    
    if not data or 'line_user_id' not in data or 'preferred_lang' not in data:
        return jsonify({"error": "註冊資料不完整"}), 400
    
    # 檢查使用者是否已存在
    existing_user = User.query.filter_by(line_user_id=data['line_user_id']).first()
    if existing_user:
        # 更新語言偏好
        existing_user.preferred_lang = data['preferred_lang']
        db.session.commit()
        return jsonify({"message": "使用者語言偏好已更新", "user_id": existing_user.user_id})
    
    # 建立新使用者
    new_user = User(
        line_user_id=data['line_user_id'],
        preferred_lang=data['preferred_lang']
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "使用者註冊成功", "user_id": new_user.user_id}), 201

@api_bp.route('/test', methods=['GET', 'POST', 'OPTIONS'])
def test():
    """API 連線測試"""
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    if request.method == 'POST':
        # 測試 POST 請求
        data = request.get_json() or {}
        response = jsonify({
            'message': 'POST 請求測試成功',
            'received_data': data,
            'content_type': request.content_type,
            'method': request.method
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
    # GET 請求
    response = jsonify({
        'message': 'API is working!',
        'method': request.method,
        'endpoints': {
            'upload_menu': '/api/upload-menu-image (POST)',
            'test': '/api/test (GET/POST)',
            'health': '/api/health (GET)'
        }
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@api_bp.route('/test-upload', methods=['GET', 'POST', 'OPTIONS'])
def test_upload():
    """檔案上傳測試端點"""
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    if request.method == 'GET':
        response = jsonify({
            'message': '檔案上傳測試端點',
            'usage': '請使用 POST 方法上傳檔案',
            'supported_fields': ['file', 'image'],
            'example': {
                'file': '檔案對象',
                'store_id': '店家ID (數字)',
                'lang': '目標語言 (可選，預設: en)'
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
    # POST 請求
    try:
        print(f"收到測試上傳請求，Content-Type: {request.content_type}")
        print(f"請求表單資料: {list(request.form.keys())}")
        print(f"請求檔案: {list(request.files.keys())}")
        
        # 檢查檔案
        file = None
        if 'file' in request.files:
            file = request.files['file']
            print("使用 'file' 參數")
        elif 'image' in request.files:
            file = request.files['image']
            print("使用 'image' 參數")
        else:
            response = jsonify({
                'error': '沒有找到檔案',
                'available_fields': list(request.files.keys()),
                'message': '請使用 "file" 或 "image" 參數'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # 檢查檔案信息
        file_info = {
            'filename': file.filename,
            'content_type': file.content_type,
            'size': len(file.read())
        }
        file.seek(0)  # 重置檔案指標
        
        # 檢查參數
        store_id = request.form.get('store_id', type=int)
        lang = request.form.get('lang', 'en')
        
        response = jsonify({
            'message': '檔案上傳測試成功',
            'file_info': file_info,
            'parameters': {
                'store_id': store_id,
                'lang': lang
            },
            'method': request.method,
            'content_type': request.content_type
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({
            'error': '檔案上傳測試失敗',
            'message': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

# =============================================================================
# 新增缺失的 API 端點
# 功能：為 LIFF 前端提供必要的 API 端點
# =============================================================================

@api_bp.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    """健康檢查端點"""
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    response = jsonify({
        'status': 'healthy',
        'message': 'API is running',
        'timestamp': datetime.datetime.now().isoformat()
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@api_bp.route('/stores', methods=['GET', 'OPTIONS'])
def get_all_stores():
    """取得所有店家列表"""
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        stores = Store.query.all()
        store_list = []
        
        for store in stores:
            store_list.append({
                'store_id': store.store_id,
                'store_name': store.store_name,
                'store_address': store.store_address,
                'store_phone': store.store_phone,
                'store_description': store.store_description,
                'is_partner': store.is_partner
            })
        
        response = jsonify({
            'stores': store_list,
            'total_count': len(store_list)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({'error': '無法載入店家列表'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@api_bp.route('/upload-menu-image', methods=['GET', 'POST', 'OPTIONS'])
def upload_menu_image():
    """上傳菜單圖片並進行 OCR 處理"""
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    # 處理 GET 請求（提供錯誤訊息）
    if request.method == 'GET':
        response = jsonify({
            'error': '此端點只接受 POST 請求',
            'message': '請使用 POST 方法上傳菜單圖片',
            'supported_methods': ['POST', 'OPTIONS']
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 405
    
    try:
        print(f"收到上傳請求，Content-Type: {request.content_type}")
        print(f"請求表單資料: {list(request.form.keys())}")
        print(f"請求檔案: {list(request.files.keys())}")
        
        # 檢查是否有檔案（支援 'file' 和 'image' 參數）
        file = None
        if 'file' in request.files:
            file = request.files['file']
            print("使用 'file' 參數")
        elif 'image' in request.files:
            file = request.files['image']
            print("使用 'image' 參數")
        else:
            print("錯誤：沒有找到 'file' 或 'image' 欄位")
            print(f"可用的檔案欄位: {list(request.files.keys())}")
            response = jsonify({
                'error': '沒有上傳檔案',
                'message': '請使用 "file" 或 "image" 參數上傳檔案',
                'available_fields': list(request.files.keys())
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        print(f"檔案名稱: {file.filename}")
        print(f"檔案大小: {len(file.read())} bytes")
        file.seek(0)  # 重置檔案指標
        
        # 檢查檔案名稱
        if file.filename == '':
            print("錯誤：檔案名稱為空")
            response = jsonify({'error': '沒有選擇檔案'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # 檢查檔案格式
        if not allowed_file(file.filename):
            print(f"錯誤：不支援的檔案格式 {file.filename}")
            response = jsonify({'error': '不支援的檔案格式'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # 取得參數
        store_id = request.form.get('store_id', type=int)
        user_id = request.form.get('user_id', type=int)
        target_lang = request.form.get('lang', 'en')
        
        print(f"店家ID: {store_id}")
        print(f"使用者ID: {user_id}")
        print(f"目標語言: {target_lang}")
        
        if not store_id:
            print("錯誤：沒有提供店家ID")
            response = jsonify({"error": "需要提供店家ID"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # 儲存上傳的檔案
        print("開始儲存檔案...")
        filepath = save_uploaded_file(file)
        print(f"檔案已儲存到: {filepath}")
        
        # 建立 Gemini 處理記錄
        print("建立處理記錄...")
        processing = GeminiProcessing(
            user_id=user_id or 1,  # 如果沒有使用者ID，使用預設值
            store_id=store_id,
            image_url=filepath,
            status='processing'
        )
        db.session.add(processing)
        db.session.commit()
        print(f"處理記錄已建立，ID: {processing.processing_id}")
        
        # 使用 Gemini API 處理圖片
        print("開始使用 Gemini API 處理圖片...")
        result = process_menu_with_gemini(filepath, target_lang)
        
        # 檢查處理結果
        if result and result.get('success', False):
            # 更新處理狀態
            processing.status = 'completed'
            processing.ocr_result = json.dumps(result, ensure_ascii=False)
            processing.structured_menu = json.dumps(result, ensure_ascii=False)
            db.session.commit()
            
            # 生成動態菜單資料
            menu_items = result.get('menu_items', [])
            dynamic_menu = []
            
            for i, item in enumerate(menu_items):
                # 確保所有字串欄位都不是 null/undefined，避免前端 charAt() 錯誤
                # 並提供前端需要的所有必要欄位
                dynamic_menu.append({
                    'temp_id': f"temp_{processing.processing_id}_{i}",
                    'id': f"temp_{processing.processing_id}_{i}",  # 前端可能需要 id 欄位
                    'original_name': str(item.get('original_name', '') or ''),
                    'translated_name': str(item.get('translated_name', '') or ''),
                    'en_name': str(item.get('translated_name', '') or ''),  # 英語名稱
                    'price': item.get('price', 0),
                    'price_small': item.get('price', 0),  # 小份價格
                    'price_large': item.get('price', 0),  # 大份價格
                    'description': str(item.get('description', '') or ''),
                    'category': str(item.get('category', '') or '其他'),
                    'image_url': '/static/images/default-dish.png',  # 預設圖片
                    'imageUrl': '/static/images/default-dish.png',  # 前端可能用這個欄位名
                    'inventory': 999,  # 庫存數量
                    'available': True,  # 是否可購買
                    'processing_id': processing.processing_id
                })
            
            response = jsonify({
                "message": "菜單處理成功",
                "processing_id": processing.processing_id,
                "store_info": result.get('store_info', {}),
                "menu_items": dynamic_menu,
                "total_items": len(dynamic_menu),
                "target_language": target_lang,
                "processing_notes": result.get('processing_notes', '')
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            
            # 加入 API 回應的除錯 log
            print(f"🎉 API 成功回應 201 Created")
            print(f"📊 回應統計:")
            print(f"  - 處理ID: {processing.processing_id}")
            print(f"  - 菜單項目數: {len(dynamic_menu)}")
            print(f"  - 目標語言: {target_lang}")
            print(f"  - 店家資訊: {result.get('store_info', {})}")
            print(f"  - 處理備註: {result.get('processing_notes', '')}")
            
            return response, 201
        else:
            # 處理失敗 - 只有在真正的錯誤時才返回 422
            processing.status = 'failed'
            db.session.commit()
            
            # 檢查是否是 JSON 解析錯誤或其他可恢復的錯誤
            error_message = result.get('error', '菜單處理失敗，請重新拍攝清晰的菜單照片')
            processing_notes = result.get('processing_notes', '')
            
            # 如果是 JSON 解析錯誤或其他可恢復的錯誤，返回 422
            if 'JSON 解析失敗' in error_message or 'extra_forbidden' in error_message:
                print(f"❌ API 返回 422 錯誤")
                print(f"🔍 錯誤詳情:")
                print(f"  - 錯誤訊息: {error_message}")
                print(f"  - 處理備註: {processing_notes}")
                print(f"  - 處理ID: {processing.processing_id}")
                
                response = jsonify({
                    "error": error_message,
                    "processing_notes": processing_notes
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 422
            else:
                # 其他錯誤返回 500
                print(f"❌ API 返回 500 錯誤")
                print(f"🔍 錯誤詳情:")
                print(f"  - 錯誤訊息: {error_message}")
                print(f"  - 處理備註: {processing_notes}")
                print(f"  - 處理ID: {processing.processing_id}")
                
                response = jsonify({
                    "error": error_message,
                    "processing_notes": processing_notes
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 500
            
    except Exception as e:
        print(f"OCR處理失敗：{e}")
        response = jsonify({
            'error': '檔案處理失敗',
            'details': str(e) if app.debug else '請稍後再試'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 422

@api_bp.route('/debug/order-data', methods=['POST', 'OPTIONS'])
def debug_order_data():
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    """除錯訂單資料格式"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "請求資料為空"}), 400
    
    analysis = {
        "data_type": type(data).__name__,
        "received_data": data,
        "top_level_keys": list(data.keys()) if isinstance(data, dict) else [],
        "validation_results": {
            "required_fields": {
                "present": [],
                "missing": []
            },
            "store": {"found": False, "store_name": None},
            "user": {"found": False, "user_id": None}
        }
    }
    
    # 檢查必要欄位
    required_fields = ['store_id', 'items']
    if isinstance(data, dict):
        for field in required_fields:
            if field in data:
                analysis["validation_results"]["required_fields"]["present"].append(field)
            else:
                analysis["validation_results"]["required_fields"]["missing"].append(field)
    
    # 檢查店家
    if isinstance(data, dict) and 'store_id' in data:
        try:
            store = Store.query.get(data['store_id'])
            if store:
                analysis["validation_results"]["store"]["found"] = True
                analysis["validation_results"]["store"]["store_name"] = store.store_name
        except Exception as e:
            analysis["validation_results"]["store"]["error"] = str(e)
    
    # 檢查使用者
    if isinstance(data, dict) and 'line_user_id' in data:
        try:
            user = User.query.filter_by(line_user_id=data['line_user_id']).first()
            if user:
                analysis["validation_results"]["user"]["found"] = True
                analysis["validation_results"]["user"]["user_id"] = user.user_id
        except Exception as e:
            analysis["validation_results"]["user"]["error"] = str(e)
    
    # 分析 items 陣列
    if isinstance(data, dict) and 'items' in data and isinstance(data['items'], list):
        analysis["validation_results"]["items"] = []
        for i, item in enumerate(data['items']):
            item_analysis = {
                "index": i,
                "item_type": type(item).__name__,
                "keys": list(item.keys()) if isinstance(item, dict) else [],
                "values": item if isinstance(item, dict) else item,
                "field_check": {}
            }
            
            if isinstance(item, dict):
                for field in ['menu_item_id', 'id', 'quantity', 'qty', 'price', 'price_small']:
                    if field in item:
                        item_analysis["field_check"][field] = {
                            "type": type(item[field]).__name__,
                            "value": item[field]
                        }
            
            analysis["validation_results"]["items"].append(item_analysis)
    
    suggestions = []
    if analysis["validation_results"]["required_fields"]["missing"]:
        suggestions.append("如果缺少必要欄位，請檢查前端發送的資料格式")
    if not analysis["validation_results"]["items"]:
        suggestions.append("如果 items 陣列格式不正確，請確保每個項目都有 menu_item_id 和 quantity")
    if not analysis["validation_results"]["store"]["found"]:
        suggestions.append("如果找不到使用者或店家，請檢查 ID 是否正確")
    
    return jsonify({
        "message": "訂單資料分析完成",
        "analysis": analysis,
        "suggestions": suggestions
    }), 200

@api_bp.route('/admin/migrate-database', methods=['POST', 'OPTIONS'])
def migrate_database():
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    """執行資料庫遷移（僅限管理員）"""
    try:
        # 檢查是否為管理員（這裡可以添加更嚴格的驗證）
        # 暫時允許所有請求，但建議添加適當的認證
        
        from tools.migrate_order_items import migrate_order_items, verify_migration
        
        print("🔄 開始執行資料庫遷移...")
        
        # 執行遷移
        success = migrate_order_items()
        
        if success:
            # 驗證遷移
            verify_success = verify_migration()
            
            if verify_success:
                return jsonify({
                    "message": "資料庫遷移成功",
                    "status": "success",
                    "details": "OrderItem 表結構已更新，支援臨時項目"
                }), 200
            else:
                return jsonify({
                    "message": "遷移完成但驗證失敗",
                    "status": "warning",
                    "details": "請檢查資料庫結構"
                }), 200
        else:
            return jsonify({
                "message": "資料庫遷移失敗",
                "status": "error",
                "details": "請檢查錯誤日誌"
            }), 500
            
    except Exception as e:
        return jsonify({
            "message": "遷移過程中發生錯誤",
            "status": "error",
            "details": str(e)
        }), 500

# =============================================================================
# 根路徑處理
# 功能：處理根路徑的請求
# =============================================================================

def handle_root_path():
    """處理根路徑請求"""
    return jsonify({
        'message': '點餐小幫手後端 API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health',
            'stores': '/api/stores',
            'menu': '/api/menu/{store_id}',
            'upload': '/api/upload-menu-image',
            'orders': '/api/orders',
            'test': '/api/test'
        }
    })
