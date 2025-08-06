#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復資料庫相容性問題
功能：確保 ordering-helper-backend 與同事的 GCP MySQL 資料庫結構匹配
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db
from sqlalchemy import text

def check_and_fix_database_compatibility():
    """檢查並修復資料庫相容性問題"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 檢查資料庫相容性...")
            
            # 檢查必要的表是否存在
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            required_tables = [
                'users', 'languages', 'stores', 'menus', 'menu_items', 
                'menu_translations', 'orders', 'order_items', 'voice_files',
                'gemini_processing', 'simple_orders', 'simple_menu_processings',
                'store_translations'
            ]
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                print(f"❌ 缺少以下表: {missing_tables}")
                print("正在創建缺失的表...")
                
                # 創建所有表
                db.create_all()
                
                # 再次檢查
                inspector = db.inspect(db.engine)
                updated_tables = inspector.get_table_names()
                
                still_missing = [table for table in required_tables if table not in updated_tables]
                
                if still_missing:
                    print(f"❌ 仍有表創建失敗: {still_missing}")
                    return False
                else:
                    print("✅ 所有表創建成功")
            else:
                print("✅ 所有必要的表都已存在")
            
            # 檢查 store_translations 表結構
            print("🔍 檢查 store_translations 表結構...")
            if 'store_translations' in existing_tables:
                columns = inspector.get_columns('store_translations')
                column_names = [col['name'] for col in columns]
                
                # 檢查是否符合同事的資料庫結構
                expected_columns = ['id', 'store_id', 'lang_code', 'description', 'translated_summary']
                missing_columns = [col for col in expected_columns if col not in column_names]
                
                if missing_columns:
                    print(f"⚠️  store_translations 表缺少欄位: {missing_columns}")
                    print("建議重新創建表...")
                    
                    # 刪除舊表並重新創建
                    db.session.execute(text("DROP TABLE IF EXISTS store_translations"))
                    db.session.commit()
                    
                    # 使用 SQLAlchemy 模型重新創建表
                    from app.models import StoreTranslation
                    db.create_all()
                    print("✅ store_translations 表已重新創建")
                else:
                    print("✅ store_translations 表結構正確")
            
            # 檢查並插入預設語言資料
            print("🔍 檢查語言資料...")
            languages = db.session.execute(text("SELECT * FROM languages")).fetchall()
            
            if not languages:
                print("正在插入預設語言資料...")
                default_languages = [
                    ('zh', '中文'),
                    ('en', 'English'),
                    ('ja', '日本語'),
                    ('ko', '한국어'),
                    ('th', 'ไทย'),
                    ('vi', 'Tiếng Việt')
                ]
                
                for lang_code, lang_name in default_languages:
                    db.session.execute(
                        text("INSERT INTO languages (lang_code, lang_name) VALUES (:code, :name)"),
                        {'code': lang_code, 'name': lang_name}
                    )
                
                db.session.commit()
                print("✅ 預設語言資料已插入")
            else:
                print(f"✅ 語言資料已存在 ({len(languages)} 筆)")
            
            # 檢查環境變數配置
            print("🔍 檢查環境變數配置...")
            required_env_vars = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_DATABASE']
            missing_env_vars = [var for var in required_env_vars if not os.getenv(var)]
            
            if missing_env_vars:
                print(f"⚠️  缺少環境變數: {missing_env_vars}")
                print("請確保 Cloud Run 環境變數設定正確")
            else:
                print("✅ 環境變數配置正確")
            
            return True
            
        except Exception as e:
            print(f"❌ 修復過程中發生錯誤: {e}")
            import traceback
            print(f"詳細錯誤: {traceback.format_exc()}")
            return False

def test_database_connection():
    """測試資料庫連接"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 測試資料庫連接...")
            
            # 執行簡單查詢
            result = db.session.execute(text("SELECT 1")).fetchone()
            
            if result:
                print("✅ 資料庫連接正常")
                return True
            else:
                print("❌ 資料庫連接失敗")
                return False
                
        except Exception as e:
            print(f"❌ 資料庫連接測試失敗: {e}")
            return False

if __name__ == "__main__":
    print("🚀 開始修復資料庫相容性...")
    
    # 測試連接
    if not test_database_connection():
        print("❌ 資料庫連接失敗，無法繼續修復")
        sys.exit(1)
    
    # 修復相容性
    if check_and_fix_database_compatibility():
        print("🎉 資料庫相容性修復完成！")
    else:
        print("❌ 修復失敗")
        sys.exit(1) 