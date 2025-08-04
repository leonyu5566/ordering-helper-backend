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
from ..models import db, Store, Menu, MenuItem, MenuTranslation, User, Order, OrderItem, StoreTranslation, GeminiProcessing, VoiceFile
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
    if 'image' not in request.files:
        return jsonify({"error": "沒有上傳檔案"}), 400
    
    file = request.files['image']
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
        result = process_menu_with_gemini(filepath, target_lang)
        
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
                dynamic_menu.append({
                    'temp_id': f"temp_{processing.processing_id}_{i}",
                    'original_name': item.get('original_name', ''),
                    'translated_name': item.get('translated_name', ''),
                    'price': item.get('price', 0),
                    'description': item.get('description', ''),
                    'category': item.get('category', ''),
                    'processing_id': processing.processing_id
                })
            
            return jsonify({
                "message": "菜單處理成功",
                "processing_id": processing.processing_id,
                "store_info": result.get('store_info', {}),
                "menu_items": dynamic_menu,
                "total_items": len(dynamic_menu),
                "target_language": target_lang
            }), 201
        else:
            # 處理失敗
            processing.status = 'failed'
            db.session.commit()
            
            return jsonify({
                "error": "菜單處理失敗，請重新拍攝清晰的菜單照片"
            }), 500
    
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
    if not data or 'line_user_id' not in data or 'store_id' not in data or 'items' not in data:
        return jsonify({"error": "訂單資料不完整"}), 400

    user = User.query.filter_by(line_user_id=data['line_user_id']).first()
    if not user:
        # 實務上應引導使用者註冊，這裡我們先簡化處理
        return jsonify({"error": "找不到使用者"}), 404

    total_amount = 0
    order_items_to_create = []
    order_details = []
    
    for item_data in data['items']:
        menu_item = MenuItem.query.get(item_data['menu_item_id'])
        if not menu_item: continue
        
        quantity = int(item_data.get('quantity', 0))
        if quantity <= 0: continue
        
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
            'subtotal': subtotal
        })

    if not order_items_to_create:
        return jsonify({"error": "沒有選擇任何商品"}), 400

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
    
    # 觸發完整的訂單確認通知（包含語音、中文紀錄、使用者語言紀錄）
    send_complete_order_notification(new_order.order_id)
    
    return jsonify({
        "message": "訂單建立成功", 
        "order_id": new_order.order_id,
        "order_details": order_details,
        "total_amount": total_amount,
        "confirmation": order_confirmation,
        "voice_generated": voice_path is not None
    }), 201

@api_bp.route('/orders/temp', methods=['POST', 'OPTIONS'])
def create_temp_order():
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    """建立臨時訂單（非合作店家）"""
    data = request.get_json()
    
    if not data or 'processing_id' not in data or 'items' not in data:
        return jsonify({"error": "訂單資料不完整"}), 400
    
    try:
        # 取得處理記錄
        processing = GeminiProcessing.query.get(data['processing_id'])
        if not processing:
            return jsonify({"error": "找不到處理記錄"}), 404
        
        # 計算總金額和建立訂單明細
        total_amount = 0
        order_details = []
        
        for item in data['items']:
            quantity = item.get('quantity', 1)
            price = item.get('price', 0)
            subtotal = price * quantity
            
            if quantity > 0:
                total_amount += subtotal
                order_details.append({
                    'temp_id': item.get('temp_id'),
                    'original_name': item.get('original_name', ''),
                    'translated_name': item.get('translated_name', ''),
                    'quantity': quantity,
                    'price': price,
                    'subtotal': subtotal
                })
        
        if not order_details:
            return jsonify({"error": "沒有選擇任何商品"}), 400
        
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

@api_bp.route('/test', methods=['GET', 'OPTIONS'])
def test():
    """API 連線測試"""
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    response = jsonify({'message': 'API is working!'}) #LIFF 前端呼叫的接口。
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

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

@api_bp.route('/upload-menu-image', methods=['POST', 'OPTIONS'])
def upload_menu_image():
    """上傳菜單圖片並進行 OCR 處理"""
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        print(f"收到上傳請求，Content-Type: {request.content_type}")
        print(f"請求表單資料: {list(request.form.keys())}")
        print(f"請求檔案: {list(request.files.keys())}")
        
        # 檢查是否有檔案
        if 'file' not in request.files:
            print("錯誤：沒有找到 'file' 欄位")
            response = jsonify({'error': '沒有上傳檔案'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        file = request.files['file']
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
                dynamic_menu.append({
                    'temp_id': f"temp_{processing.processing_id}_{i}",
                    'original_name': item.get('original_name', ''),
                    'translated_name': item.get('translated_name', ''),
                    'price': item.get('price', 0),
                    'description': item.get('description', ''),
                    'category': item.get('category', ''),
                    'processing_id': processing.processing_id
                })
            
            response = jsonify({
                "message": "菜單處理成功",
                "processing_id": processing.processing_id,
                "store_info": result.get('store_info', {}),
                "menu_items": dynamic_menu,
                "total_items": len(dynamic_menu),
                "target_language": target_lang
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 201
        else:
            # 處理失敗
            processing.status = 'failed'
            db.session.commit()
            
            response = jsonify({
                "error": "菜單處理失敗，請重新拍攝清晰的菜單照片"
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 500
            
    except Exception as e:
        print(f"OCR處理失敗：{e}")
        response = jsonify({'error': '檔案處理失敗'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

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
