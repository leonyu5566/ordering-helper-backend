# =============================================================================
# 檔案名稱：app/models.py
# 功能描述：定義所有資料庫模型，包含整個點餐系統的資料結構
# 主要職責：
# - 定義資料庫表格結構
# - 建立模型之間的關聯關係
# - 提供資料庫操作的 ORM 介面
# 包含模型：
# - 使用者管理：User, Language
# - 店家管理：Store, StoreTranslation
# - 菜單管理：Menu, MenuItem, MenuTranslation
# - 訂單管理：Order, OrderItem
# - 語音檔案：VoiceFile
# - AI 處理：GeminiProcessing
# =============================================================================

from flask_sqlalchemy import SQLAlchemy
import datetime

# =============================================================================
# SQLAlchemy 資料庫物件建立區塊
# 功能：建立 SQLAlchemy 資料庫物件，用於所有資料庫操作
# 作用：提供 ORM（物件關聯對應）功能，讓 Python 程式碼可以直接操作資料庫
# =============================================================================
db = SQLAlchemy()

# =============================================================================
# 語言設定模型區塊
# 功能：定義系統支援的語言設定
# 用途：管理多語言支援，包含中文、英文、日文、韓文等
# 欄位：
# - lang_code：語言代碼（如 'zh', 'en', 'ja', 'ko'）
# - lang_name：語言名稱（如 '中文', 'English', '日本語'）
# =============================================================================
class Language(db.Model):
    __tablename__ = 'languages'
    lang_code = db.Column(db.String(5), primary_key=True)
    lang_name = db.Column(db.String(50), nullable=False)

# =============================================================================
# 使用者模型區塊
# 功能：定義 LINE Bot 使用者的資料結構
# 用途：儲存使用者的基本資訊和偏好設定
# 欄位：
# - user_id：使用者唯一識別碼
# - line_user_id：LINE 平台的使用者 ID
# - preferred_lang：使用者偏好的語言（關聯到 Language 模型）
# - created_at：帳號建立時間
# 關聯：與 Language 模型建立外鍵關聯
# =============================================================================
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.BigInteger, primary_key=True)
    line_user_id = db.Column(db.String(100), unique=True, nullable=False)
    preferred_lang = db.Column(db.String(5), db.ForeignKey('languages.lang_code'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# =============================================================================
# 店家模型區塊
# 功能：定義合作店家的資料結構
# 用途：儲存店家的基本資訊、位置、合作等級等
# 欄位：
# - store_id：店家唯一識別碼
# - store_name：店家名稱
# - partner_level：合作等級（0=非合作, 1=合作, 2=VIP）
# - gps_lat/gps_lng：店家 GPS 座標
# - place_id：Google Places ID
# - review_summary：評論摘要
# - top_dish_1-5：熱門菜色
# - main_photo_url：店家招牌照片 URL
# - created_at：店家資料建立時間
# 關聯：與 Menu 模型建立一對多關聯（一個店家可以有多個菜單）
# =============================================================================
class Store(db.Model):
    __tablename__ = 'stores'
    store_id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(100), nullable=False)
    partner_level = db.Column(db.SmallInteger, nullable=False, default=0)  # 0=非合作, 1=合作, 2=VIP
    gps_lat = db.Column(db.Float)  # 店家緯度
    gps_lng = db.Column(db.Float)  # 店家經度
    place_id = db.Column(db.String(100))  # Google Places ID
    review_summary = db.Column(db.Text)  # 評論摘要
    top_dish_1 = db.Column(db.String(100))  # 熱門菜色1
    top_dish_2 = db.Column(db.String(100))  # 熱門菜色2
    top_dish_3 = db.Column(db.String(100))  # 熱門菜色3
    top_dish_4 = db.Column(db.String(100))  # 熱門菜色4
    top_dish_5 = db.Column(db.String(100))  # 熱門菜色5
    main_photo_url = db.Column(db.String(255))  # 店家招牌照片
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    # 新增的欄位（用於向後相容）
    latitude = db.Column(db.Float)  # 店家緯度（向後相容）
    longitude = db.Column(db.Float)  # 店家經度（向後相容）
    menus = db.relationship('Menu', backref='store', lazy=True)

class StoreTranslation(db.Model):
    __tablename__ = 'store_translations'
    store_translation_id = db.Column(db.BigInteger, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=False)
    lang_code = db.Column(db.String(5), db.ForeignKey('languages.lang_code'), nullable=False)
    description_trans = db.Column(db.Text)  # 翻譯後的店家簡介
    reviews = db.Column(db.Text)  # 翻譯後的評論

class Menu(db.Model):
    __tablename__ = 'menus'
    menu_id = db.Column(db.BigInteger, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    items = db.relationship('MenuItem', backref='menu', lazy=True, cascade="all, delete-orphan")

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    menu_item_id = db.Column(db.BigInteger, primary_key=True)
    menu_id = db.Column(db.BigInteger, db.ForeignKey('menus.menu_id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False) # 這是中文菜品名
    price_big = db.Column(db.Integer)
    price_small = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    translations = db.relationship('MenuTranslation', backref='menu_item', lazy=True, cascade="all, delete-orphan")

class MenuTranslation(db.Model):
    __tablename__ = 'menu_translations'
    menu_translation_id = db.Column(db.BigInteger, primary_key=True)
    menu_item_id = db.Column(db.BigInteger, db.ForeignKey('menu_items.menu_item_id'), nullable=False)
    lang_code = db.Column(db.String(5), db.ForeignKey('languages.lang_code'), nullable=False)
    item_name_trans = db.Column(db.String(100)) # 翻譯後的菜品名
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=False)
    order_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    total_amount = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    voice_files = db.relationship('VoiceFile', backref='order', lazy=True, cascade="all, delete-orphan")

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    order_item_id = db.Column(db.BigInteger, primary_key=True)
    order_id = db.Column(db.BigInteger, db.ForeignKey('orders.order_id'), nullable=False)
    menu_item_id = db.Column(db.BigInteger, db.ForeignKey('menu_items.menu_item_id'), nullable=False)
    quantity_small = db.Column(db.Integer, nullable=False, default=0)
    subtotal = db.Column(db.Integer, nullable=False)

class VoiceFile(db.Model):
    __tablename__ = 'voice_files'
    voice_file_id = db.Column(db.BigInteger, primary_key=True)
    order_id = db.Column(db.BigInteger, db.ForeignKey('orders.order_id'), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)  # 語音檔案 URL
    file_type = db.Column(db.String(10), default='mp3')  # mp3, wav
    speech_rate = db.Column(db.Float, default=1.0)  # 語速倍率
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class GeminiProcessing(db.Model):
    __tablename__ = 'gemini_processing'
    processing_id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)  # 上傳的菜單圖片 URL
    ocr_result = db.Column(db.Text)  # OCR 辨識結果
    structured_menu = db.Column(db.Text)  # 結構化後的菜單 (JSON)
    status = db.Column(db.String(20), default='processing')  # processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
