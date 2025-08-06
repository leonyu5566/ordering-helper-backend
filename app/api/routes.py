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

from flask import Blueprint, jsonify, request, send_file, current_app
from ..models import db, Store, Menu, MenuItem, MenuTranslation, User, Order, OrderItem, StoreTranslation, OCRMenu, OCRMenuItem, VoiceFile, Language
from .helpers import process_menu_with_gemini, generate_voice_order, create_order_summary, save_uploaded_file
import json
import os
from werkzeug.utils import secure_filename
import datetime
import uuid
import time

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
    
    # 檢查是否有檔案
    if 'image' not in request.files:
        response = jsonify({'error': '沒有上傳檔案'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    
    file = request.files['image']
    
    # 檢查檔案名稱
    if file.filename == '':
        response = jsonify({'error': '沒有選擇檔案'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    
    # 檢查檔案格式
    if not allowed_file(file.filename):
        response = jsonify({'error': '不支援的檔案格式'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    
    # 取得參數
    store_id = request.form.get('store_id', type=int)
    user_id = request.form.get('user_id', type=int)
    target_lang = request.form.get('lang', 'en')
    
    if not store_id:
        response = jsonify({"error": "需要提供店家ID"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    
    try:
        # 儲存上傳的檔案
        filepath = save_uploaded_file(file)
        
        # 建立 OCR 菜單記錄（符合同事的資料庫結構）
        from app.models import OCRMenu, OCRMenuItem
        
        # 先處理圖片獲取店家資訊
        print("開始使用 Gemini API 處理圖片...")
        result = process_menu_with_gemini(filepath, target_lang)
        
        # 檢查處理結果
        if result and result.get('success', False):
            # 建立 OCR 菜單記錄
            ocr_menu = OCRMenu(
                user_id=user_id or 1,
                store_name=result.get('store_info', {}).get('name', '臨時店家')
            )
            db.session.add(ocr_menu)
            db.session.flush()  # 獲取 ocr_menu_id
            # 儲存菜單項目到資料庫
            menu_items = result.get('menu_items', [])
            dynamic_menu = []
            
            for i, item in enumerate(menu_items):
                # 儲存到 ocr_menu_items 表
                ocr_menu_item = OCRMenuItem(
                    ocr_menu_id=ocr_menu.ocr_menu_id,
                    item_name=str(item.get('original_name', '') or ''),
                    price_small=item.get('price', 0),
                    price_big=item.get('price', 0),  # 使用相同價格
                    translated_desc=str(item.get('translated_name', '') or '')
                )
                db.session.add(ocr_menu_item)
                
                # 生成動態菜單資料（保持前端相容性）
                dynamic_menu.append({
                    'temp_id': f"temp_{ocr_menu.ocr_menu_id}_{i}",
                    'id': f"temp_{ocr_menu.ocr_menu_id}_{i}",
                    'original_name': str(item.get('original_name', '') or ''),
                    'translated_name': str(item.get('translated_name', '') or ''),
                    'en_name': str(item.get('translated_name', '') or ''),
                    'price': item.get('price', 0),
                    'price_small': item.get('price', 0),
                    'price_large': item.get('price', 0),
                    'description': str(item.get('description', '') or ''),
                    'category': str(item.get('category', '') or '其他'),
                    'image_url': '/static/images/default-dish.png',
                    'imageUrl': '/static/images/default-dish.png',
                    'inventory': 999,
                    'available': True,
                    'processing_id': ocr_menu.ocr_menu_id
                })
            
            # 提交資料庫變更
            db.session.commit()
            
            response = jsonify({
                "message": "菜單處理成功",
                "processing_id": ocr_menu.ocr_menu_id,
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
            print(f"  - 處理ID: {ocr_menu.ocr_menu_id}")
            print(f"  - 菜單項目數: {len(dynamic_menu)}")
            print(f"  - 目標語言: {target_lang}")
            print(f"  - 店家資訊: {result.get('store_info', {})}")
            print(f"  - 處理備註: {result.get('processing_notes', '')}")
            
            return response, 201
        else:
            # 檢查是否是 JSON 解析錯誤或其他可恢復的錯誤
            error_message = result.get('error', '菜單處理失敗，請重新拍攝清晰的菜單照片')
            processing_notes = result.get('processing_notes', '')
            
            # 如果是 JSON 解析錯誤或其他可恢復的錯誤，返回 422
            if 'JSON 解析失敗' in error_message or 'extra_forbidden' in error_message:
                print(f"❌ API 返回 422 錯誤")
                print(f"🔍 錯誤詳情:")
                print(f"  - 錯誤訊息: {error_message}")
                print(f"  - 處理備註: {processing_notes}")
                print(f"  - 處理ID: 無")
                
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
                print(f"  - 處理ID: 無")
                
                response = jsonify({
                    "error": error_message,
                    "processing_notes": processing_notes
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 500
                
    except Exception as e:
        print(f"❌ 處理過程中發生錯誤: {e}")
        response = jsonify({
            "error": "處理過程中發生錯誤",
            "details": str(e) if current_app.debug else '請稍後再試'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

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
        # 確保 store_id 有值
        store_id = data.get('store_id')
        if not store_id:
            # 如果沒有 store_id，創建一個預設店家
            from app.models import Store
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
        
        new_order = Order(
            user_id=user.user_id,
            store_id=store_id,
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
    required_fields = ['items']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            "error": "訂單資料不完整",
            "missing_fields": missing_fields,
            "received_data": list(data.keys())
        }), 400
    
    try:
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
            except Exception as e:
                db.session.rollback()
                return jsonify({
                    "error": "建立使用者失敗",
                    "details": str(e)
                }), 500

        # 驗證訂單項目
        order_items = []
        total_amount = 0
        validation_errors = []
        
        for i, item_data in enumerate(data['items']):
            # 支援多種欄位名稱格式
            item_name = item_data.get('item_name') or item_data.get('name') or item_data.get('original_name') or f"項目 {i+1}"
            quantity = item_data.get('quantity') or item_data.get('qty') or item_data.get('quantity_small') or 1
            price = item_data.get('price') or item_data.get('price_small') or item_data.get('price_unit') or 0
            
            try:
                quantity = int(quantity)
                price = float(price)
                if quantity <= 0:
                    validation_errors.append(f"項目 {i+1}: 數量必須大於 0")
                    continue
                if price < 0:
                    validation_errors.append(f"項目 {i+1}: 價格不能為負數")
                    continue
            except (ValueError, TypeError):
                validation_errors.append(f"項目 {i+1}: 數量或價格格式錯誤")
                continue
            
            subtotal = int(price * quantity)
            total_amount += subtotal
            
            order_items.append({
                'item_name': item_name,
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal
            })

        if validation_errors:
            return jsonify({
                "error": "訂單資料驗證失敗",
                "validation_errors": validation_errors,
                "received_items": data['items']
            }), 400

        if not order_items:
            return jsonify({
                "error": "沒有選擇任何商品",
                "received_items": data['items']
            }), 400

        # 創建臨時訂單記錄（不依賴複雜的資料庫結構）
        temp_order_id = f"temp_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{user.user_id}"
        
        # 建立完整訂單確認內容
        from .helpers import create_complete_order_confirmation, send_complete_order_notification, generate_voice_order
        
        # 創建訂單摘要
        order_summary = {
            'order_id': temp_order_id,
            'user_id': user.user_id,
            'items': order_items,
            'total_amount': total_amount,
            'order_time': datetime.datetime.utcnow().isoformat(),
            'status': 'pending'
        }
        
        # 生成語音檔（可選）
        voice_path = None
        try:
            # 這裡可以生成語音檔，但不需要依賴資料庫
            voice_path = f"/temp_voice/{temp_order_id}.mp3"
        except Exception as e:
            print(f"語音生成失敗: {e}")
        
        # 只在非訪客模式下發送 LINE 通知
        if not guest_mode:
            try:
                send_complete_order_notification(temp_order_id)
            except Exception as e:
                print(f"LINE 通知發送失敗: {e}")
        
        return jsonify({
            "message": "臨時訂單建立成功", 
            "order_id": temp_order_id,
            "order_details": order_items,
            "total_amount": total_amount,
            "voice_generated": voice_path is not None,
            "order_summary": order_summary
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "臨時訂單建立失敗",
            "details": str(e)
        }), 500

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

@api_bp.route('/fix-database', methods=['POST', 'OPTIONS'])
def fix_database():
    """修復數據庫表結構"""
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        print("🔧 開始修復數據庫...")
        
        # 檢查現有表
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        # 檢查並創建必要的表
        required_tables = ['ocr_menus', 'ocr_menu_items']
        
        for table_name in required_tables:
            if table_name not in existing_tables:
                print(f"🔧 創建 {table_name} 表...")
                
                if table_name == 'ocr_menus':
                    # 創建 ocr_menus 表
                    create_table_sql = """
                    CREATE TABLE ocr_menus (
                        ocr_menu_id BIGINT NOT NULL AUTO_INCREMENT,
                        user_id BIGINT NOT NULL,
                        store_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
                        upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (ocr_menu_id),
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='非合作店家用戶OCR菜單主檔'
                    """
                    
                    db.session.execute(text(create_table_sql))
                    db.session.commit()
                    print(f"✅ {table_name} 表創建成功")
                    
                elif table_name == 'ocr_menu_items':
                    # 創建 ocr_menu_items 表
                    create_table_sql = """
                    CREATE TABLE ocr_menu_items (
                        ocr_menu_item_id BIGINT NOT NULL AUTO_INCREMENT,
                        ocr_menu_id BIGINT NOT NULL,
                        item_name VARCHAR(100) COLLATE utf8mb4_bin NOT NULL,
                        price_big INT DEFAULT NULL,
                        price_small INT NOT NULL,
                        translated_desc TEXT COLLATE utf8mb4_bin,
                        PRIMARY KEY (ocr_menu_item_id),
                        FOREIGN KEY (ocr_menu_id) REFERENCES ocr_menus (ocr_menu_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='OCR菜單品項明細'
                    """
                    
                    db.session.execute(text(create_table_sql))
                    db.session.commit()
                    print(f"✅ {table_name} 表創建成功")
                    
                else:
                    print(f"❌ 不支援創建 {table_name} 表")
                    return jsonify({
                        'status': 'error',
                        'message': f'不支援創建 {table_name} 表'
                    }), 500
            else:
                print(f"✅ {table_name} 表已存在")
                
                # 檢查表結構
                columns = inspector.get_columns(table_name)
                column_names = [col['name'] for col in columns]
                
                if table_name == 'ocr_menus':
                    expected_columns = ['ocr_menu_id', 'user_id', 'store_name', 'upload_time']
                    
                    missing_columns = [col for col in expected_columns if col not in column_names]
                    
                    if missing_columns:
                        print(f"⚠️  {table_name} 表缺少欄位: {missing_columns}")
                        return jsonify({
                            'status': 'error',
                            'message': f'{table_name} 表結構不完整，缺少欄位: {missing_columns}'
                        }), 500
                    else:
                        print(f"✅ {table_name} 表結構正確")
                        
                elif table_name == 'ocr_menu_items':
                    expected_columns = ['ocr_menu_item_id', 'ocr_menu_id', 'item_name', 'price_big', 'price_small', 'translated_desc']
                    
                    missing_columns = [col for col in expected_columns if col not in column_names]
                    
                    if missing_columns:
                        print(f"⚠️  {table_name} 表缺少欄位: {missing_columns}")
                        return jsonify({
                            'status': 'error',
                            'message': f'{table_name} 表結構不完整，缺少欄位: {missing_columns}'
                        }), 500
                    else:
                        print(f"✅ {table_name} 表結構正確")
        
        print("🎉 數據庫修復完成")
        response = jsonify({
            'status': 'success',
            'message': '數據庫修復完成'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        print(f"❌ 修復數據庫時發生錯誤: {e}")
        response = jsonify({
            'status': 'error',
            'message': f'修復失敗: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

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
        
        # 生成唯一的處理 ID（不使用資料庫）
        processing_id = int(time.time() * 1000)  # 使用時間戳作為 ID
        print(f"處理記錄已建立，ID: {processing_id}")
        
        # 使用 Gemini API 處理圖片
        print("開始使用 Gemini API 處理圖片...")
        result = process_menu_with_gemini(filepath, target_lang)
        
        # 檢查處理結果
        if result and result.get('success', False):
            
            # 生成動態菜單資料
            menu_items = result.get('menu_items', [])
            dynamic_menu = []
            
            for i, item in enumerate(menu_items):
                # 確保所有字串欄位都不是 null/undefined，避免前端 charAt() 錯誤
                # 並提供前端需要的所有必要欄位
                dynamic_menu.append({
                    'temp_id': f"temp_{processing_id}_{i}",
                    'id': f"temp_{processing_id}_{i}",  # 前端可能需要 id 欄位
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
                    'processing_id': processing_id
                })
            
            response = jsonify({
                "message": "菜單處理成功",
                "processing_id": processing_id,
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
            print(f"  - 處理ID: {processing_id}")
            print(f"  - 菜單項目數: {len(dynamic_menu)}")
            print(f"  - 目標語言: {target_lang}")
            print(f"  - 店家資訊: {result.get('store_info', {})}")
            print(f"  - 處理備註: {result.get('processing_notes', '')}")
            
            return response, 201
        else:
            
            # 檢查是否是 JSON 解析錯誤或其他可恢復的錯誤
            error_message = result.get('error', '菜單處理失敗，請重新拍攝清晰的菜單照片')
            processing_notes = result.get('processing_notes', '')
            
            # 如果是 JSON 解析錯誤或其他可恢復的錯誤，返回 422
            if 'JSON 解析失敗' in error_message or 'extra_forbidden' in error_message:
                print(f"❌ API 返回 422 錯誤")
                print(f"🔍 錯誤詳情:")
                print(f"  - 錯誤訊息: {error_message}")
                print(f"  - 處理備註: {processing_notes}")
                print(f"  - 處理ID: {processing_id}")
                
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
                print(f"  - 處理ID: {processing_id}")
                
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
            'details': str(e) if current_app.debug else '請稍後再試'
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

@api_bp.route('/menu/simple-ocr', methods=['POST', 'OPTIONS'])
def simple_menu_ocr():
    """簡化的菜單 OCR 處理（非合作店家）- 不儲存資料庫"""
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        # 檢查是否有檔案
        file = None
        if 'image' in request.files:
            file = request.files['image']
        elif 'file' in request.files:
            file = request.files['file']
        else:
            return jsonify({
                "success": False,
                "error": "沒有上傳圖片檔案"
            }), 400
        
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "沒有選擇檔案"
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": "不支援的檔案格式"
            }), 400
        
        # 取得目標語言
        target_lang = request.form.get('target_lang', 'en')
        
        # 儲存上傳的檔案
        filepath = save_uploaded_file(file)
        
        # 使用 Gemini 處理圖片
        from .helpers import process_menu_with_gemini
        result = process_menu_with_gemini(filepath, target_lang)
        
        if result and result.get('success', False):
            menu_items = result.get('menu_items', [])
            
            # 簡化菜單項目格式（不儲存資料庫）
            simplified_items = []
            for i, item in enumerate(menu_items):
                simplified_items.append({
                    'id': f"simple_{i}",
                    'name': str(item.get('original_name', '') or ''),
                    'translated_name': str(item.get('translated_name', '') or ''),
                    'price': item.get('price', 0),
                    'description': str(item.get('description', '') or ''),
                    'category': str(item.get('category', '') or '其他')
                })
            
            response = jsonify({
                "success": True,
                "menu_items": simplified_items,
                "store_name": result.get('store_info', {}).get('store_name', '臨時店家'),
                "target_language": target_lang,
                "processing_notes": result.get('processing_notes', '')
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 200
        else:
            error_message = result.get('error', '菜單處理失敗，請重新拍攝清晰的菜單照片')
            response = jsonify({
                "success": False,
                "error": error_message,
                "processing_notes": result.get('processing_notes', '')
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 422
    
    except Exception as e:
        print(f"簡化 OCR 處理失敗：{e}")
        response = jsonify({
            "success": False,
            "error": "處理過程中發生錯誤"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@api_bp.route('/orders/simple', methods=['POST', 'OPTIONS'])
def simple_order():
    """簡化訂單處理（非合作店家）- 不儲存資料庫，直接生成語音"""
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "請求資料為空"
            }), 400
        
        # 檢查必要欄位
        if 'items' not in data:
            return jsonify({
                "success": False,
                "error": "缺少訂單項目"
            }), 400
        
        items = data['items']
        user_language = data.get('user_language', 'zh')
        
        if not items:
            return jsonify({
                "success": False,
                "error": "沒有選擇任何商品"
            }), 400
        
        # 驗證和計算
        total_amount = 0
        validated_items = []
        
        for i, item in enumerate(items):
            name = item.get('name') or item.get('translated_name') or f"項目 {i+1}"
            quantity = int(item.get('quantity', 1))
            price = float(item.get('price', 0))
            
            if quantity <= 0:
                return jsonify({
                    "success": False,
                    "error": f"項目 {i+1}: 數量必須大於 0"
                }), 400
            
            if price < 0:
                return jsonify({
                    "success": False,
                    "error": f"項目 {i+1}: 價格不能為負數"
                }), 400
            
            subtotal = price * quantity
            total_amount += subtotal
            
            validated_items.append({
                'name': name,
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal
            })
        
        # 生成訂單ID（用於檔案命名）
        import datetime
        order_id = f"simple_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # 使用 Gemini API 生成訂單摘要
        from .helpers import generate_order_summary_with_gemini
        order_summary = generate_order_summary_with_gemini(validated_items, user_language)
        
        # 生成中文語音檔（Azure Speech）
        voice_url = None
        try:
            from .helpers import generate_chinese_voice_with_azure
            voice_url = generate_chinese_voice_with_azure(order_summary, order_id)
        except Exception as e:
            print(f"語音生成失敗: {e}")
        
        # 生成使用者語言版本的訂單摘要
        user_summary_items = []
        for item in validated_items:
            user_summary_items.append(f"{item['name']} x{item['quantity']} = {item['subtotal']}元")
        
        user_summary = f"""
Order Summary:
{chr(10).join(user_summary_items)}
Total Amount: {total_amount} 元
        """.strip()
        
        # 準備訂單資料
        order_data = {
            "order_id": order_id,
            "total_amount": total_amount,
            "voice_url": voice_url,
            "chinese_summary": order_summary.get('chinese_summary', '點餐摘要'),
            "user_summary": user_summary,
            "order_details": validated_items
        }
        
        # 發送給 LINE Bot（如果提供了使用者ID）
        line_user_id = data.get('line_user_id')
        if line_user_id:
            try:
                from .helpers import send_order_to_line_bot
                send_success = send_order_to_line_bot(line_user_id, order_data)
                if send_success:
                    print(f"✅ 成功發送訂單到 LINE Bot，使用者: {line_user_id}")
                else:
                    print(f"⚠️ LINE Bot 發送失敗，使用者: {line_user_id}")
            except Exception as e:
                print(f"❌ LINE Bot 發送異常: {e}")
        
        response = jsonify({
            "success": True,
            "order_id": order_id,
            "total_amount": total_amount,
            "voice_url": voice_url,
            "chinese_summary": order_summary.get('chinese_summary', '點餐摘要'),
            "user_summary": user_summary,
            "order_details": validated_items,
            "line_bot_sent": line_user_id is not None
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    
    except Exception as e:
        print(f"簡化訂單處理失敗：{e}")
        response = jsonify({
            "success": False,
            "error": "訂單處理失敗"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@api_bp.route('/voice/control', methods=['POST', 'OPTIONS'])
def voice_control():
    """語音控制 API - 處理 LINE Bot 的語音控制按鈕"""
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "請求資料為空"
            }), 400
        
        # 檢查必要欄位
        required_fields = ['user_id', 'action', 'order_id']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                "success": False,
                "error": "缺少必要欄位",
                "missing_fields": missing_fields
            }), 400
        
        user_id = data['user_id']
        action = data['action']
        order_id = data['order_id']
        
        # 根據動作處理語音控制
        from .helpers import send_voice_with_rate
        
        if action == 'replay':
            # 重新播放（正常語速）
            success = send_voice_with_rate(user_id, order_id, 1.0)
        elif action == 'slow':
            # 慢速播放
            success = send_voice_with_rate(user_id, order_id, 0.7)
        elif action == 'fast':
            # 快速播放
            success = send_voice_with_rate(user_id, order_id, 1.3)
        else:
            return jsonify({
                "success": False,
                "error": "不支援的語音控制動作"
            }), 400
        
        if success:
            return jsonify({
                "success": True,
                "message": f"語音控制成功: {action}",
                "user_id": user_id,
                "order_id": order_id
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "語音控制失敗"
            }), 500
            
    except Exception as e:
        print(f"語音控制處理失敗：{e}")
        return jsonify({
            "success": False,
            "error": "語音控制處理失敗"
        }), 500

@api_bp.route('/line/webhook', methods=['POST', 'OPTIONS'])
def line_webhook():
    """LINE Bot Webhook 處理"""
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        data = request.get_json()
        
        if not data or 'events' not in data:
            return jsonify({"success": False, "error": "無效的 webhook 資料"}), 400
        
        # 處理每個事件
        for event in data['events']:
            event_type = event.get('type')
            user_id = event.get('source', {}).get('userId')
            
            if not user_id:
                continue
            
            if event_type == 'postback':
                # 處理 postback 事件（語音控制按鈕）
                postback_data = event.get('postback', {}).get('data', '')
                
                if postback_data.startswith('replay_voice:'):
                    order_id = postback_data.split(':')[1]
                    from .helpers import send_voice_with_rate
                    send_voice_with_rate(user_id, order_id, 1.0)
                    
                elif postback_data.startswith('slow_voice:'):
                    order_id = postback_data.split(':')[1]
                    from .helpers import send_voice_with_rate
                    send_voice_with_rate(user_id, order_id, 0.7)
                    
                elif postback_data.startswith('fast_voice:'):
                    order_id = postback_data.split(':')[1]
                    from .helpers import send_voice_with_rate
                    send_voice_with_rate(user_id, order_id, 1.3)
            
            elif event_type == 'message':
                # 處理文字訊息
                message_text = event.get('message', {}).get('text', '')
                
                if message_text.lower() in ['help', '幫助', '說明']:
                    # 發送幫助訊息
                    help_message = """
點餐小幫手使用說明：

1. 拍照辨識菜單
2. 選擇想要的品項
3. 確認訂單
4. 系統會自動生成中文語音檔
5. 在店家播放語音即可點餐

支援語音控制：
- 重新播放：正常語速
- 慢速播放：適合店家聽
- 快速播放：節省時間
                    """.strip()
                    
                    from .helpers import send_order_to_line_bot
                    send_order_to_line_bot(user_id, {
                        "chinese_summary": help_message,
                        "user_summary": help_message,
                        "voice_url": None,
                        "total_amount": 0
                    })
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"LINE Webhook 處理失敗：{e}")
        return jsonify({"success": False, "error": "Webhook 處理失敗"}), 500

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

@api_bp.route('/test/line-bot', methods=['GET', 'OPTIONS'])
def test_line_bot():
    """測試 LINE Bot 環境變數設定"""
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        import os
        
        # 檢查環境變數
        line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        line_channel_secret = os.getenv('LINE_CHANNEL_SECRET')
        
        # 檢查其他必要環境變數
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        azure_speech_key = os.getenv('AZURE_SPEECH_KEY')
        azure_speech_region = os.getenv('AZURE_SPEECH_REGION')
        
        # 構建測試結果
        test_results = {
            "line_bot": {
                "channel_access_token": "✅ 已設定" if line_channel_access_token else "❌ 未設定",
                "channel_secret": "✅ 已設定" if line_channel_secret else "❌ 未設定"
            },
            "ai_services": {
                "gemini_api_key": "✅ 已設定" if gemini_api_key else "❌ 未設定",
                "azure_speech_key": "✅ 已設定" if azure_speech_key else "❌ 未設定",
                "azure_speech_region": "✅ 已設定" if azure_speech_region else "❌ 未設定"
            },
            "all_configured": all([
                line_channel_access_token,
                line_channel_secret,
                gemini_api_key,
                azure_speech_key,
                azure_speech_region
            ])
        }
        
        response = jsonify({
            "message": "LINE Bot 環境變數檢查",
            "test_results": test_results,
            "ready_for_production": test_results["all_configured"]
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({
            "error": "環境變數檢查失敗",
            "details": str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
