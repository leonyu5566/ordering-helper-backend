#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
創建缺少的資料庫表格
功能：為您的 MySQL 資料庫創建缺少的表格
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def create_missing_tables():
    """創建缺少的資料庫表格"""
    
    # 資料庫連線字串
    DATABASE_URL = "mysql+aiomysql://gae252g1usr:gae252g1PSWD%21@35.201.153.17:3306/gae252g1_db"
    pymysql_url = DATABASE_URL.replace("mysql+aiomysql://", "mysql+pymysql://")
    
    print("🔧 開始創建缺少的資料庫表格...")
    
    try:
        engine = create_engine(pymysql_url)
        with engine.connect() as connection:
            
            # 1. 創建 orders 表格
            print("\n📋 創建 orders 表格...")
            create_orders_sql = """
            CREATE TABLE IF NOT EXISTS orders (
                order_id BIGINT NOT NULL AUTO_INCREMENT,
                user_id BIGINT NOT NULL,
                store_id INT NOT NULL,
                order_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_amount INT NOT NULL DEFAULT 0,
                status VARCHAR(20) DEFAULT 'pending',
                PRIMARY KEY (order_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (store_id) REFERENCES stores (store_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='訂單主檔'
            """
            connection.execute(text(create_orders_sql))
            print("✅ orders 表格創建成功")
            
            # 2. 創建 order_items 表格
            print("\n📋 創建 order_items 表格...")
            create_order_items_sql = """
            CREATE TABLE IF NOT EXISTS order_items (
                order_item_id BIGINT NOT NULL AUTO_INCREMENT,
                order_id BIGINT NOT NULL,
                menu_item_id BIGINT NOT NULL,
                quantity_small INT NOT NULL DEFAULT 0,
                subtotal INT NOT NULL,
                PRIMARY KEY (order_item_id),
                FOREIGN KEY (order_id) REFERENCES orders (order_id),
                FOREIGN KEY (menu_item_id) REFERENCES menu_items (menu_item_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='訂單項目'
            """
            connection.execute(text(create_order_items_sql))
            print("✅ order_items 表格創建成功")
            
            # 3. 創建 voice_files 表格
            print("\n📋 創建 voice_files 表格...")
            create_voice_files_sql = """
            CREATE TABLE IF NOT EXISTS voice_files (
                voice_file_id BIGINT NOT NULL AUTO_INCREMENT,
                order_id BIGINT NOT NULL,
                file_url VARCHAR(500) NOT NULL,
                file_type VARCHAR(10) DEFAULT 'mp3',
                speech_rate FLOAT DEFAULT 1.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (voice_file_id),
                FOREIGN KEY (order_id) REFERENCES orders (order_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='語音檔案'
            """
            connection.execute(text(create_voice_files_sql))
            print("✅ voice_files 表格創建成功")
            
            # 4. 創建 store_translations 表格
            print("\n📋 創建 store_translations 表格...")
            create_store_translations_sql = """
            CREATE TABLE IF NOT EXISTS store_translations (
                id INT NOT NULL AUTO_INCREMENT,
                store_id INT NOT NULL,
                language_code VARCHAR(10) NOT NULL,
                description TEXT,
                translated_summary TEXT,
                PRIMARY KEY (id),
                FOREIGN KEY (store_id) REFERENCES stores (store_id),
                FOREIGN KEY (language_code) REFERENCES languages (lang_code)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='店家翻譯'
            """
            connection.execute(text(create_store_translations_sql))
            print("✅ store_translations 表格創建成功")
            
            # 提交變更
            connection.commit()
            print("\n✅ 所有缺少的表格創建完成！")
            
            # 驗證表格創建
            print("\n🔍 驗證表格創建...")
            tables_result = connection.execute(text("SHOW TABLES"))
            tables = [row[0] for row in tables_result.fetchall()]
            
            required_tables = [
                'users', 'languages', 'stores', 'menus', 'menu_items', 
                'menu_translations', 'orders', 'order_items', 'voice_files',
                'ocr_menus', 'ocr_menu_items', 'store_translations'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"❌ 仍有缺少的表格: {missing_tables}")
                return False
            else:
                print("✅ 所有必要表格都已存在")
                return True
                
    except SQLAlchemyError as e:
        print(f"❌ 創建表格失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        return False

def update_app_config():
    """更新應用程式設定以使用新的資料庫連線"""
    print("\n🔧 更新應用程式設定...")
    
    # 創建環境變數設定檔案
    env_content = """# 資料庫連線設定
DB_USER=gae252g1usr
DB_PASSWORD=gae252g1PSWD!
DB_HOST=35.201.153.17
DB_DATABASE=gae252g1_db

# 或者使用完整的 DATABASE_URL
DATABASE_URL=mysql+pymysql://gae252g1usr:gae252g1PSWD%21@35.201.153.17:3306/gae252g1_db

# 其他環境變數
GEMINI_API_KEY=your_gemini_api_key
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_azure_region
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ .env 檔案已創建")
    print("📝 請根據您的實際 API 金鑰更新 .env 檔案")

if __name__ == "__main__":
    print("🚀 資料庫表格創建工具")
    print("=" * 50)
    
    if create_missing_tables():
        update_app_config()
        print("\n🎉 資料庫設定完成！")
        print("\n📋 下一步：")
        print("1. 更新 .env 檔案中的 API 金鑰")
        print("2. 執行 python3 tools/init_mysql_database.py 初始化資料")
        print("3. 啟動應用程式：python3 run.py")
    else:
        print("\n❌ 表格創建失敗，請檢查錯誤訊息")
    
    print("\n" + "=" * 50)
    print("🏁 完成")
