# =============================================================================
# 檔案名稱：app/__init__.py
# 功能描述：Flask 應用程式的工廠函數，負責建立和設定整個應用程式
# 主要職責：
# - 建立 Flask 應用程式實例
# - 設定資料庫連線
# - 註冊所有 Blueprint（API、Webhook、Admin）
# - 設定 CORS 和後台管理介面
# - 整合錯誤處理和日誌系統
# =============================================================================

from flask import Flask, redirect, url_for
from flask_cors import CORS
from .models import db
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from .errors import setup_logging, errors
from dotenv import load_dotenv
import os

def create_app():
    # 確保環境變數被載入（開發環境使用 notebook.env，生產環境使用系統環境變數）
    if os.path.exists('notebook.env'):
        load_dotenv('notebook.env', override=True)
    
    # 除錯：檢查環境變數
    print(f"🔍 除錯 - DB_HOST: {os.getenv('DB_HOST')}")
    print(f"🔍 除錯 - DB_USERNAME: {os.getenv('DB_USERNAME')}")
    print(f"🔍 除錯 - DB_NAME: {os.getenv('DB_NAME')}")
    print(f"🔍 除錯 - 當前工作目錄: {os.getcwd()}")
    print(f"🔍 除錯 - notebook.env 檔案存在: {os.path.exists('notebook.env')}")
    
    # =============================================================================
    # Flask 應用程式建立區塊
    # 功能：建立 Flask 應用程式實例並設定基本配置
    # 參數：
    # - instance_relative_config=True：允許從 instance 資料夾載入設定
    # =============================================================================
    app = Flask(__name__)
    
    # =============================================================================
    # 根路由設定區塊
    # 功能：當用戶訪問根路徑時，重定向到後台管理系統
    # =============================================================================
    @app.route('/')
    def index():
        """根路由 - 重定向到後台管理系統"""
        return redirect(url_for('admin_panel.dashboard'))
    
    @app.route('/liff/<path:filename>')
    def liff_static(filename):
        """LIFF 靜態檔案路由"""
        try:
            return app.send_static_file(f'liff/{filename}')
        except Exception as e:
            return f'<h1>404 - 頁面不存在</h1><p>檔案 {filename} 不存在</p>', 404
    
    # =============================================================================
    # 資料庫連線字串建立區塊
    # 功能：組合 MySQL 資料庫連線字串
    # 格式：mysql+pymysql://使用者:密碼@主機:埠號/資料庫名稱?charset=utf8mb4
    # 注意：所有連線資訊都從環境變數中讀取
    # =============================================================================
    
    # 檢查環境變數
    db_username = os.getenv('DB_USERNAME')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    
    print(f"🔍 除錯 - DB_USERNAME: {db_username}")
    print(f"🔍 除錯 - DB_PASSWORD: {'*' * len(db_password) if db_password else 'None'}")
    print(f"🔍 除錯 - DB_HOST: {db_host}")
    print(f"🔍 除錯 - DB_NAME: {db_name}")
    
    if not all([db_username, db_password, db_host, db_name]):
        print("❌ 錯誤：環境變數不完整")
        raise ValueError("資料庫環境變數不完整")
    
    db_uri = f"mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_name}?charset=utf8mb4"
    print(f"🔍 除錯 - DB_URI: {db_uri}")
    
    # =============================================================================
    # 應用程式配置區塊
    # 功能：設定 Flask 應用程式的各種配置參數
    # 包含：
    # - SECRET_KEY：用於 session 加密（開發環境使用 'dev'）
    # - SQLALCHEMY_DATABASE_URI：資料庫連線字串
    # - SQLALCHEMY_TRACK_MODIFICATIONS：關閉 SQLAlchemy 的修改追蹤
    # =============================================================================
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            'connect_args': {
                'ssl': {'ssl': {}},
                'server_public_key': True
            }
        }
    )

    # =============================================================================
    # CORS 設定區塊
    # 功能：設定跨域資源共享，允許前端網頁存取 API
    # 設定：允許 Azure 靜態網站和其他來源存取 /api/* 路徑
    # 注意：正式環境應該限制特定網域
    # =============================================================================
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "https://*.azurestaticapps.net",  # Azure Static Web Apps
                "https://*.azurewebsites.net",    # Azure Web Apps
                "http://localhost:3000",          # 本地開發
                "http://127.0.0.1:3000",         # 本地開發
                "*"                              # 開發階段允許所有來源
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # =============================================================================
    # 資料庫初始化區塊
    # 功能：將 SQLAlchemy 資料庫物件與 Flask 應用程式綁定
    # 作用：讓資料庫操作可以在應用程式上下文中執行
    # =============================================================================
    db.init_app(app)

    # =============================================================================
    # Blueprint 註冊區塊
    # 功能：註冊所有功能模組的 Blueprint
    # 包含：
    # - API Blueprint：處理 LIFF 前端的 API 請求
    # - Webhook Blueprint：處理 LINE Bot 的 webhook 請求
    # - Admin Blueprint：處理後台管理系統的請求
    # - Errors Blueprint：處理全域錯誤
    # =============================================================================
    
    from .api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from .webhook.routes import webhook_bp
    app.register_blueprint(webhook_bp)

    # --- 註冊後台管理系統 ---
    from .admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin', name='admin_panel')

    # =============================================================================
    # 錯誤處理和日誌系統設定區塊
    # 功能：
    # - 註冊全域錯誤處理 Blueprint
    # - 設定應用程式日誌系統
    # 作用：提供統一的錯誤處理和日誌記錄功能
    # =============================================================================
    
    # --- 註冊錯誤處理 ---
    app.register_blueprint(errors)

    # --- 設定日誌系統 ---
    setup_logging(app)

    # =============================================================================
    # 後台管理介面設定區塊
    # 功能：建立 Flask-Admin 後台管理介面
    # 設定：
    # - name：後台管理系統的名稱
    # - template_mode：使用 Bootstrap 4 模板
    # =============================================================================
    admin = Admin(app, name='點餐傳聲筒後台', template_mode='bootstrap4')
    
    # =============================================================================
    # 資料庫模型匯入區塊
    # 功能：匯入所有資料庫模型類別
    # 包含：使用者、店家、菜單、訂單、語音檔案、AI 處理等模型
    # =============================================================================
    from .models import User, Store, Menu, MenuItem, MenuTranslation, Order, OrderItem, Language, StoreTranslation, VoiceFile, GeminiProcessing
    
    # =============================================================================
    # 後台管理模型註冊區塊
    # 功能：將所有資料庫模型註冊到後台管理介面
    # 作用：讓管理員可以透過網頁介面管理資料庫內容
    # 包含：
    # - 使用者管理：查看和管理使用者資料
    # - 店家管理：管理合作店家資訊
    # - 菜單管理：管理店家菜單內容
    # - 訂單管理：查看訂單記錄
    # - 語音檔案：管理生成的語音檔案
    # - AI 處理：查看 Gemini API 處理記錄
    # =============================================================================
    admin.add_view(ModelView(User, db.session, name='使用者管理'))
    admin.add_view(ModelView(Store, db.session, name='店家管理'))
    admin.add_view(ModelView(StoreTranslation, db.session, name='店家翻譯'))
    admin.add_view(ModelView(Menu, db.session, name='菜單管理'))
    admin.add_view(ModelView(MenuItem, db.session, name='品項管理'))
    admin.add_view(ModelView(MenuTranslation, db.session, name='翻譯管理'))
    admin.add_view(ModelView(Order, db.session, name='訂單總覽'))
    admin.add_view(ModelView(OrderItem, db.session, name='訂單明細'))
    admin.add_view(ModelView(VoiceFile, db.session, name='語音檔案'))
    admin.add_view(ModelView(GeminiProcessing, db.session, name='Gemini處理'))
    admin.add_view(ModelView(Language, db.session, name='語言管理'))

    # =============================================================================
    # 應用程式回傳區塊
    # 功能：回傳完整設定的 Flask 應用程式實例
    # 包含：所有 Blueprint、資料庫、後台管理、錯誤處理等
    # =============================================================================
    return app



