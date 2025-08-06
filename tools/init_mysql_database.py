#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 資料庫初始化腳本
功能：使用同事的資料庫結構創建所有必要的表
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db
from sqlalchemy import text

def init_mysql_database():
    """初始化 MySQL 資料庫"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🚀 開始初始化 MySQL 資料庫...")
            
            # 檢查是否為 MySQL 環境
            database_url = app.config['SQLALCHEMY_DATABASE_URI']
            if 'mysql' not in database_url:
                print("⚠️  當前不是 MySQL 環境，跳過 MySQL 特定初始化")
                return True
            
            print("✅ 檢測到 MySQL 環境")
            
            # 創建所有表（使用 SQLAlchemy 模型）
            print("🔍 創建資料庫表...")
            db.create_all()
            
            # 檢查表是否創建成功
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            required_tables = [
                'languages', 'stores', 'users', 'orders', 'order_items',
                'menus', 'menu_items', 'menu_translations', 'store_translations',
                'ocr_menus', 'ocr_menu_items', 'voice_files', 'simple_orders', 'simple_menu_processings'
            ]
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                print(f"❌ 缺少以下表: {missing_tables}")
                return False
            else:
                print("✅ 所有表創建成功")
            
            # 插入預設資料
            print("🔍 插入預設資料...")
            
            # 插入語言資料
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
            
            # 插入範例店家資料
            stores = db.session.execute(text("SELECT * FROM stores")).fetchall()
            if not stores:
                print("正在插入範例店家資料...")
                
                sample_stores = [
                    {
                        'store_id': 1,
                        'store_name': '測試合作店家',
                        'partner_level': 1,
                        'gps_lat': 25.0330,
                        'gps_lng': 121.5654,
                        'place_id': 'test_place_id_1',
                        'review_summary': '這是一個合作店家',
                        'top_dish_1': '招牌菜1',
                        'top_dish_2': '招牌菜2',
                        'top_dish_3': '招牌菜3',
                        'top_dish_4': '招牌菜4',
                        'top_dish_5': '招牌菜5',
                        'main_photo_url': 'https://example.com/photo1.jpg'
                    },
                    {
                        'store_id': 2,
                        'store_name': '測試非合作店家',
                        'partner_level': 0,
                        'gps_lat': 25.0331,
                        'gps_lng': 121.5655,
                        'place_id': 'test_place_id_2',
                        'review_summary': '這是一個非合作店家',
                        'top_dish_1': '特色菜1',
                        'top_dish_2': '特色菜2',
                        'top_dish_3': '特色菜3',
                        'top_dish_4': '特色菜4',
                        'top_dish_5': '特色菜5',
                        'main_photo_url': 'https://example.com/photo2.jpg'
                    }
                ]
                
                for store_data in sample_stores:
                    db.session.execute(text("""
                        INSERT INTO stores (
                            store_id, store_name, partner_level, gps_lat, gps_lng, 
                            place_id, review_summary, top_dish_1, top_dish_2, top_dish_3, 
                            top_dish_4, top_dish_5, main_photo_url
                        ) VALUES (
                            :store_id, :store_name, :partner_level, :gps_lat, :gps_lng,
                            :place_id, :review_summary, :top_dish_1, :top_dish_2, :top_dish_3,
                            :top_dish_4, :top_dish_5, :main_photo_url
                        )
                    """), store_data)
                
                db.session.commit()
                print("✅ 範例店家資料已插入")
            else:
                print(f"✅ 店家資料已存在 ({len(stores)} 筆)")
            
            # 插入範例菜單資料
            menus = db.session.execute(text("SELECT * FROM menus")).fetchall()
            if not menus:
                print("正在插入範例菜單資料...")
                
                # 為合作店家創建菜單
                sample_menu_data = {
                    'menu_id': 1,
                    'store_id': 1,
                    'version': 1
                }
                
                db.session.execute(text("""
                    INSERT INTO menus (menu_id, store_id, version, effective_date, created_at)
                    VALUES (:menu_id, :store_id, :version, NOW(), NOW())
                """), sample_menu_data)
                
                # 插入菜單項目
                sample_menu_items = [
                    {
                        'menu_item_id': 1,
                        'menu_id': 1,
                        'item_name': '紅燒肉',
                        'price_big': 120,
                        'price_small': 80
                    },
                    {
                        'menu_item_id': 2,
                        'menu_id': 1,
                        'item_name': '宮保雞丁',
                        'price_big': 100,
                        'price_small': 70
                    },
                    {
                        'menu_item_id': 3,
                        'menu_id': 1,
                        'item_name': '麻婆豆腐',
                        'price_big': 80,
                        'price_small': 60
                    }
                ]
                
                for item_data in sample_menu_items:
                    db.session.execute(text("""
                        INSERT INTO menu_items (menu_item_id, menu_id, item_name, price_big, price_small, created_at)
                        VALUES (:menu_item_id, :menu_id, :item_name, :price_big, :price_small, NOW())
                    """), item_data)
                
                db.session.commit()
                print("✅ 範例菜單資料已插入")
            else:
                print(f"✅ 菜單資料已存在 ({len(menus)} 筆)")
            
            print("🎉 MySQL 資料庫初始化完成！")
            return True
            
        except Exception as e:
            print(f"❌ 初始化過程中發生錯誤: {e}")
            import traceback
            print(f"詳細錯誤: {traceback.format_exc()}")
            return False

def check_mysql_connection():
    """檢查 MySQL 連接"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 檢查 MySQL 連接...")
            
            # 執行簡單查詢
            result = db.session.execute(text("SELECT 1")).fetchone()
            
            if result:
                print("✅ MySQL 連接正常")
                return True
            else:
                print("❌ MySQL 連接失敗")
                return False
                
        except Exception as e:
            print(f"❌ MySQL 連接測試失敗: {e}")
            return False

if __name__ == "__main__":
    print("🚀 開始 MySQL 資料庫初始化...")
    
    # 檢查連接
    if not check_mysql_connection():
        print("❌ MySQL 連接失敗，無法繼續初始化")
        sys.exit(1)
    
    # 初始化資料庫
    if init_mysql_database():
        print("🎉 MySQL 資料庫初始化成功！")
    else:
        print("❌ MySQL 資料庫初始化失敗")
        sys.exit(1) 