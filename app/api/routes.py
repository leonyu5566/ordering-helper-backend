# =============================================================================
# 檔案名稱：app/api/routes.py
# 功能描述：定義所有 API 端點，處理 LIFF 前端的 HTTP 請求
# 主要職責：
# - 提供店家查詢 API
# - 處理菜單資料請求
# - 處理圖片上傳和 OCR
# - 處理訂單建立
# - 處理使用者註冊
# 支援功能：
# - 多語言菜單顯示
# - 鄰近店家查詢
# - 菜單圖片 OCR 處理
# - 訂單語音生成
# =============================================================================

from flask import Blueprint, jsonify, request
from ..models import db, Store, Menu, MenuItem, MenuTranslation, User, Order, OrderItem, StoreTranslation, GeminiProcessing, VoiceFile
from .helpers import process_menu_with_gemini, generate_voice_order, create_order_summary, save_uploaded_file
import json
import os
from werkzeug.utils import secure_filename

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

@api_bp.route('/stores/nearby', methods=['GET'])
def get_nearby_stores():
    """根據 GPS 座標取得鄰近店家"""
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    lang = request.args.get('lang', 'zh')
    
    if not lat or not lng:
        return jsonify({"error": "需要提供緯度和經度"}), 400
    
    # 簡單的距離計算（實際應用中應該使用更精確的算法）
    stores = Store.query.all()
    nearby_stores = []
    
    for store in stores:
        if store.latitude and store.longitude:
            # 計算距離（簡化版）
            distance = ((lat - store.latitude) ** 2 + (lng - store.longitude) ** 2) ** 0.5
            if distance < 0.1:  # 約 10km 範圍內
                store_data = {
                    "store_id": store.store_id,
                    "store_name": store.store_name,
                    "partner_level": store.partner_level,
                    "distance": distance,
                    "photo_url": store.store_photo_url
                }
                
                # 取得翻譯資訊
                translation = StoreTranslation.query.filter_by(
                    store_id=store.store_id, 
                    lang_code=lang
                ).first()
                
                if translation:
                    store_data["description"] = translation.description_trans
                    store_data["reviews"] = translation.reviews
                else:
                    store_data["description"] = store.description
                    store_data["reviews"] = ""
                
                nearby_stores.append(store_data)
    
    return jsonify({"stores": nearby_stores})

@api_bp.route('/menus/<int:store_id>', methods=['GET'])
def get_menu(store_id):
    lang = request.args.get('lang', 'zh')
    store = Store.query.get_or_404(store_id)
    latest_menu = Menu.query.filter_by(store_id=store.store_id).order_by(Menu.version.desc()).first()

    if not latest_menu:
        return jsonify({"error": "找不到此店家的菜單"}), 404

    menu_items_data = []
    for item in latest_menu.items:
        # 預設使用中文菜名
        display_name = item.item_name
        description = ""

        # 如果語言不是中文，嘗試尋找翻譯
        if lang != 'zh':
            translation = MenuTranslation.query.filter_by(
                menu_item_id=item.menu_item_id, 
                lang_code=lang
            ).first()
            if translation:
                display_name = translation.item_name_trans or item.item_name
                description = translation.description or ""
        
        item_data = {
            "menu_item_id": item.menu_item_id,
            "item_name": display_name,
            "description": description,
            "price_small": item.price_small,
        }
        menu_items_data.append(item_data)

    response = {
        "store_name": store.store_name,
        "items": menu_items_data
    }
    return jsonify(response)

@api_bp.route('/upload-menu-image', methods=['POST'])
def upload_menu_image():
    """上傳菜單圖片並進行 OCR 處理"""
    if 'image' not in request.files:
        return jsonify({"error": "沒有上傳檔案"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "沒有選擇檔案"}), 400
    
    if file and allowed_file(file.filename):
        # 儲存上傳的檔案
        filepath = save_uploaded_file(file)
        
        # 取得使用者語言偏好
        user_id = request.form.get('user_id', type=int)
        store_id = request.form.get('store_id', type=int)
        target_lang = request.form.get('lang', 'en')
        
        # 建立 Gemini 處理記錄
        processing = GeminiProcessing(
            user_id=user_id,
            store_id=store_id,
            image_url=filepath,
            status='processing'
        )
        db.session.add(processing)
        db.session.commit()
        
        # 使用 Gemini API 處理圖片
        result = process_menu_with_gemini(filepath, target_lang)
        
        if result:
            # 更新處理狀態
            processing.status = 'completed'
            processing.ocr_result = json.dumps(result, ensure_ascii=False)
            processing.structured_menu = json.dumps(result, ensure_ascii=False)
            db.session.commit()
            
            return jsonify({
                "message": "菜單處理成功",
                "processing_id": processing.processing_id,
                "menu_data": result
            }), 201
        else:
            # 處理失敗
            processing.status = 'failed'
            db.session.commit()
            
            return jsonify({
                "error": "菜單處理失敗"
            }), 500
    
    return jsonify({"error": "不支援的檔案格式"}), 400

@api_bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data or 'line_user_id' not in data or 'store_id' not in data or 'items' not in data:
        return jsonify({"error": "訂單資料不完整"}), 400

    user = User.query.filter_by(line_user_id=data['line_user_id']).first()
    if not user:
        # 實務上應引導使用者註冊，這裡我們先簡化處理
        return jsonify({"error": "找不到使用者"}), 404

    total_amount = 0
    order_items_to_create = []
    
    for item_data in data['items']:
        menu_item = MenuItem.query.get(item_data['menu_item_id'])
        if not menu_item: continue
        
        quantity = int(item_data.get('quantity', 0))
        subtotal = menu_item.price_small * quantity
        total_amount += subtotal
        
        order_items_to_create.append(OrderItem(
            menu_item_id=menu_item.menu_item_id,
            quantity_small=quantity,
            subtotal=subtotal
        ))

    new_order = Order(
        user_id=user.user_id,
        store_id=data['store_id'],
        total_amount=total_amount,
        items=order_items_to_create
    )
    
    db.session.add(new_order)
    db.session.commit()
    
    # 生成語音檔案
    voice_path = generate_voice_order(new_order.order_id)
    
    if voice_path:
        # 儲存語音檔案記錄
        voice_file = VoiceFile(
            order_id=new_order.order_id,
            file_url=voice_path,
            file_type='wav',
            speech_rate=1.0
        )
        db.session.add(voice_file)
        db.session.commit()
    
    # 建立訂單摘要
    order_summary = create_order_summary(new_order.order_id, user.preferred_lang)
    
    # TODO: 觸發 LINE Push Message 發送語音和文字訊息
    
    return jsonify({
        "message": "訂單建立成功", 
        "order_id": new_order.order_id,
        "voice_file": voice_path,
        "summary": order_summary
    }), 201

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

@api_bp.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'API is working!'}) #LIFF 前端呼叫的接口。

# =============================================================================
# LIFF 前端 API 端點
# 功能：為 LIFF 網頁提供必要的 API 服務
# =============================================================================

@api_bp.route('/stores', methods=['GET'])
def get_stores():
    """取得所有店家列表"""
    try:
        stores = Store.query.all()
        stores_data = []
        
        for store in stores:
            store_data = {
                'store_id': store.store_id,
                'store_name': store.store_name,
                'partner_level': store.partner_level,
                'address': store.address,
                'description': store.description
            }
            stores_data.append(store_data)
        
        return jsonify(stores_data)
        
    except Exception as e:
        return jsonify({'error': '無法載入店家資料'}), 500

@api_bp.route('/stores/<int:store_id>', methods=['GET'])
def get_store(store_id):
    """取得特定店家資訊"""
    try:
        store = Store.query.get_or_404(store_id)
        
        store_data = {
            'store_id': store.store_id,
            'store_name': store.store_name,
            'partner_level': store.partner_level,
            'address': store.address,
            'description': store.description
        }
        
        return jsonify(store_data)
        
    except Exception as e:
        return jsonify({'error': '無法載入店家資訊'}), 500

@api_bp.route('/process-voice', methods=['POST'])
def process_voice():
    """處理語音指令"""
    try:
        data = request.get_json()
        store_id = data.get('store_id')
        voice_text = data.get('voice_text')
        language = data.get('language', 'zh-TW')
        
        if not store_id or not voice_text:
            return jsonify({'success': False, 'message': '缺少必要參數'}), 400
        
        # 這裡應該實作語音辨識和自然語言處理
        # 目前先回傳模擬資料
        order_items = [
            {
                'name': '牛肉麵',
                'description': '招牌牛肉麵',
                'quantity': 1,
                'price': 120
            }
        ]
        
        return jsonify({
            'success': True,
            'message': '已加入牛肉麵',
            'order_items': order_items
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': '處理語音指令失敗'}), 500

@api_bp.route('/orders', methods=['POST'])
def create_order_from_liff():
    """從 LIFF 建立訂單"""
    try:
        data = request.get_json()
        store_id = data.get('store_id')
        items = data.get('items', [])
        language = data.get('language', 'zh-TW')
        
        if not store_id or not items:
            return jsonify({'error': '缺少必要參數'}), 400
        
        # 計算總金額
        total_amount = sum(item['price'] * item['quantity'] for item in items)
        
        # 建立訂單（簡化版）
        # 實際應用中需要更完整的訂單處理邏輯
        order_id = f"ORDER_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'total_amount': total_amount,
            'message': '訂單建立成功'
        })
        
    except Exception as e:
        return jsonify({'error': '建立訂單失敗'}), 500
