#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
強制本地開發使用 Cloud MySQL 資料庫工具

功能：
1. 強制設定環境變數指向 Cloud MySQL
2. 驗證資料庫連線
3. 檢查資料庫結構
4. 防止本地開發時的欄位錯誤

使用方法：
python3 tools/force_cloud_mysql_local.py
"""

import os
import sys
import subprocess
from datetime import datetime

def set_cloud_mysql_env():
    """設定 Cloud MySQL 環境變數"""
    print("🔧 設定 Cloud MySQL 環境變數...")
    
    # Cloud MySQL 連線資訊
    cloud_mysql_config = {
        'DB_USER': 'gae252g1usr',
        'DB_PASSWORD': 'gae252g1PSWD!',
        'DB_HOST': '35.201.153.17',
        'DB_DATABASE': 'gae252g1_db'
    }
    
    # 設定環境變數
    for key, value in cloud_mysql_config.items():
        os.environ[key] = value
        print(f"✅ 設定 {key} = {value}")
    
    # 設定完整的 DATABASE_URL
    database_url = f"mysql+pymysql://{cloud_mysql_config['DB_USER']}:{cloud_mysql_config['DB_PASSWORD']}@{cloud_mysql_config['DB_HOST']}/{cloud_mysql_config['DB_DATABASE']}?ssl={{'ssl': {{}}}}&ssl_verify_cert=false"
    os.environ['DATABASE_URL'] = database_url
    print(f"✅ 設定 DATABASE_URL = {database_url}")
    
    return True

def test_database_connection():
    """測試資料庫連線"""
    print("\n🔍 測試 Cloud MySQL 連線...")
    
    try:
        import pymysql
        from sqlalchemy import create_engine, text
        
        # 建立連線
        engine = create_engine(os.environ['DATABASE_URL'])
        
        # 測試連線
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ 資料庫連線成功")
            
            # 檢查資料庫版本
            version_result = conn.execute(text("SELECT VERSION()"))
            version = version_result.fetchone()[0]
            print(f"📊 MySQL 版本: {version}")
            
            return True
            
    except Exception as e:
        print(f"❌ 資料庫連線失敗: {e}")
        return False

def check_database_structure():
    """檢查資料庫結構"""
    print("\n🔍 檢查資料庫結構...")
    
    try:
        from sqlalchemy import create_engine, text, inspect
        
        engine = create_engine(os.environ['DATABASE_URL'])
        inspector = inspect(engine)
        
        # 檢查重要表格
        important_tables = [
            'users', 'stores', 'menu_items', 'orders', 'order_items',
            'languages', 'menu_translations', 'store_translations',
            'ocr_menus', 'ocr_menu_items'
        ]
        
        existing_tables = inspector.get_table_names()
        print(f"📊 資料庫中共有 {len(existing_tables)} 個表格")
        
        for table in important_tables:
            if table in existing_tables:
                print(f"✅ {table} 表格存在")
                
                # 檢查表格結構
                columns = inspector.get_columns(table)
                print(f"   📋 欄位數量: {len(columns)}")
                
                # 顯示前幾個欄位
                for i, column in enumerate(columns[:3]):
                    print(f"   - {column['name']}: {column['type']}")
                if len(columns) > 3:
                    print(f"   ... 還有 {len(columns) - 3} 個欄位")
            else:
                print(f"❌ {table} 表格不存在")
        
        return True
        
    except Exception as e:
        print(f"❌ 檢查資料庫結構失敗: {e}")
        return False

def create_env_file():
    """建立 .env 檔案"""
    print("\n📝 建立 .env 檔案...")
    
    env_content = """# Cloud MySQL 資料庫連線設定
DB_USER=gae252g1usr
DB_PASSWORD=gae252g1PSWD!
DB_HOST=35.201.153.17
DB_DATABASE=gae252g1_db

# 完整的資料庫 URL
DATABASE_URL=mysql+pymysql://gae252g1usr:gae252g1PSWD%21@35.201.153.17:3306/gae252g1_db?ssl={'ssl': {}}&ssl_verify_cert=false

# 其他環境變數（請根據實際情況修改）
GEMINI_API_KEY=your_gemini_api_key
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=australiaeast

# 強制使用 Cloud MySQL（防止欄位錯誤）
FORCE_CLOUD_MYSQL=true
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ .env 檔案已建立")
        print("📝 請根據您的實際 API 金鑰更新 .env 檔案")
        return True
    except Exception as e:
        print(f"❌ 建立 .env 檔案失敗: {e}")
        return False

def update_app_config():
    """更新應用程式設定"""
    print("\n🔧 更新應用程式設定...")
    
    # 讀取 app/__init__.py
    init_file = 'app/__init__.py'
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否已經強制使用 Cloud MySQL
        if 'FORCE_CLOUD_MYSQL' in content:
            print("✅ 應用程式已設定強制使用 Cloud MySQL")
            return True
        
        # 修改資料庫連線邏輯
        old_pattern = """    # 設定資料庫
    # 從個別環境變數構建資料庫 URL
    db_username = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_DATABASE')
    
    if all([db_username, db_password, db_host, db_name]):
        # 使用 MySQL 連線，添加 SSL 參數
        database_url = f"mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_name}?ssl={{'ssl': {{}}}}&ssl_verify_cert=false"
    else:
        # 回退到 SQLite
        database_url = 'sqlite:///app.db'"""
        
        new_pattern = """    # 設定資料庫
    # 強制使用 Cloud MySQL 以防止欄位錯誤
    force_cloud_mysql = os.getenv('FORCE_CLOUD_MYSQL', 'false').lower() == 'true'
    
    if force_cloud_mysql:
        # 強制使用 Cloud MySQL
        db_username = 'gae252g1usr'
        db_password = 'gae252g1PSWD!'
        db_host = '35.201.153.17'
        db_name = 'gae252g1_db'
        database_url = f"mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_name}?ssl={{'ssl': {{}}}}&ssl_verify_cert=false"
        print("🔧 強制使用 Cloud MySQL 資料庫")
    else:
        # 從個別環境變數構建資料庫 URL
        db_username = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_DATABASE')
        
        if all([db_username, db_password, db_host, db_name]):
            # 使用 MySQL 連線，添加 SSL 參數
            database_url = f"mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_name}?ssl={{'ssl': {{}}}}&ssl_verify_cert=false"
        else:
            # 回退到 SQLite
            database_url = 'sqlite:///app.db'"""
        
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ 應用程式設定已更新")
            return True
        else:
            print("⚠️ 無法找到需要修改的程式碼區塊")
            return False
            
    except Exception as e:
        print(f"❌ 更新應用程式設定失敗: {e}")
        return False

def run_application_test():
    """執行應用程式測試"""
    print("\n🧪 執行應用程式測試...")
    
    try:
        # 設定環境變數
        os.environ['FORCE_CLOUD_MYSQL'] = 'true'
        
        # 添加專案根目錄到 Python 路徑
        import sys
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, project_root)
        
        # 匯入並測試應用程式
        from app import create_app
        
        app = create_app()
        
        with app.app_context():
            # 測試資料庫連線
            from app.models import db
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            print("✅ 應用程式資料庫連線正常")
            
            # 測試模型載入
            from app.models import User, Store, Order
            print("✅ 資料庫模型載入正常")
            
        return True
        
    except Exception as e:
        print(f"❌ 應用程式測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 強制本地開發使用 Cloud MySQL 資料庫")
    print("=" * 50)
    
    # 記錄開始時間
    start_time = datetime.now()
    
    # 執行步驟
    steps = [
        ("設定環境變數", set_cloud_mysql_env),
        ("測試資料庫連線", test_database_connection),
        ("檢查資料庫結構", check_database_structure),
        ("建立 .env 檔案", create_env_file),
        ("更新應用程式設定", update_app_config),
        ("執行應用程式測試", run_application_test)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"\n📋 步驟: {step_name}")
        print("-" * 30)
        
        try:
            if step_func():
                success_count += 1
                print(f"✅ {step_name} 完成")
            else:
                print(f"❌ {step_name} 失敗")
        except Exception as e:
            print(f"❌ {step_name} 發生錯誤: {e}")
    
    # 總結
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 50)
    print(f"📊 執行結果: {success_count}/{len(steps)} 項成功")
    print(f"⏱️ 執行時間: {duration:.2f} 秒")
    
    if success_count == len(steps):
        print("\n🎉 所有步驟都成功完成！")
        print("✅ 本地開發現在強制使用 Cloud MySQL 資料庫")
        print("✅ 這將防止欄位錯誤和資料不一致問題")
        print("\n📝 使用說明:")
        print("1. 設定 FORCE_CLOUD_MYSQL=true 環境變數")
        print("2. 重新啟動應用程式")
        print("3. 所有資料庫操作都會使用 Cloud MySQL")
    else:
        print("\n⚠️ 部分步驟失敗，請檢查錯誤訊息")
        print("建議檢查網路連線和資料庫權限")

if __name__ == "__main__":
    main()
