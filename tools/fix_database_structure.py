#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復資料庫結構以符合同事的資料庫設計
功能：將 GeminiProcessing 改為使用 ocr_menus 和 ocr_menu_items 表
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db
from sqlalchemy import text

def create_ocr_tables():
    """創建 ocr_menus 和 ocr_menu_items 表"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 檢查 ocr 相關表...")
            
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # 檢查 ocr_menus 表
            if 'ocr_menus' not in existing_tables:
                print("❌ ocr_menus 表不存在，正在創建...")
                
                # 使用 SQLAlchemy 模型創建表
                from app.models import OCRMenu, OCRMenuItem
                db.create_all()
                print("✅ ocr_menus 表創建成功")
            else:
                print("✅ ocr_menus 表已存在")
            
            # 檢查 ocr_menu_items 表
            if 'ocr_menu_items' not in existing_tables:
                print("❌ ocr_menu_items 表不存在，正在創建...")
                
                # 使用 SQLAlchemy 模型創建表
                from app.models import OCRMenu, OCRMenuItem
                db.create_all()
                print("✅ ocr_menu_items 表創建成功")
            else:
                print("✅ ocr_menu_items 表已存在")
            
            # 檢查其他必要的表
            required_tables = [
                'languages', 'stores', 'users', 'orders', 'order_items',
                'menus', 'menu_items', 'menu_translations', 'store_translations'
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
            
            return True
            
        except Exception as e:
            print(f"❌ 創建表時發生錯誤: {e}")
            import traceback
            print(f"詳細錯誤: {traceback.format_exc()}")
            return False

def check_ocr_tables():
    """檢查 OCR 相關表"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 檢查 OCR 相關表...")
            
            # 檢查是否有 ocr_menus 和 ocr_menu_items 表
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'ocr_menus' in existing_tables and 'ocr_menu_items' in existing_tables:
                print("✅ OCR 相關表已存在")
                return True
            else:
                print("⚠️  OCR 相關表不存在，建議創建")
                return False
            
        except Exception as e:
            print(f"❌ 檢查 OCR 表時發生錯誤: {e}")
            return False

def insert_sample_data():
    """插入範例資料"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 檢查範例資料...")
            
            # 檢查語言資料
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
            
            # 檢查店家資料
            stores = db.session.execute(text("SELECT * FROM stores")).fetchall()
            
            if not stores:
                print("正在插入範例店家資料...")
                
                # 使用字典格式插入資料
                sample_store_data = {
                    'store_id': 1,
                    'store_name': '測試店家',
                    'partner_level': 0,
                    'gps_lat': 25.0330,
                    'gps_lng': 121.5654,
                    'place_id': 'test_place_id',
                    'review_summary': '這是一個測試店家',
                    'top_dish_1': '測試菜色1',
                    'top_dish_2': '測試菜色2',
                    'top_dish_3': '測試菜色3',
                    'top_dish_4': '測試菜色4',
                    'top_dish_5': '測試菜色5',
                    'main_photo_url': 'https://example.com/photo.jpg'
                }
                
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
                """), sample_store_data)
                
                db.session.commit()
                print("✅ 範例店家資料已插入")
            else:
                print(f"✅ 店家資料已存在 ({len(stores)} 筆)")
            
            return True
            
        except Exception as e:
            print(f"❌ 插入範例資料時發生錯誤: {e}")
            return False

if __name__ == "__main__":
    print("🚀 開始修復資料庫結構...")
    
    # 創建 ocr 表
    if not create_ocr_tables():
        print("❌ 創建 ocr 表失敗")
        sys.exit(1)
    
    # 檢查 OCR 表
    if not check_ocr_tables():
        print("❌ 檢查 OCR 表失敗")
        sys.exit(1)
    
    # 插入範例資料
    if not insert_sample_data():
        print("❌ 插入範例資料失敗")
        sys.exit(1)
    
    print("🎉 資料庫結構修復完成！")
    print("\n📋 下一步：")
    print("1. 修改代碼以使用 ocr_menus 和 ocr_menu_items 表")
    print("2. 更新 API 路由以符合同事的資料庫結構")
    print("3. 測試部署到 Cloud Run") 