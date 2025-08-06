#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
創建 OCR 相關表（符合同事的資料庫結構）
功能：創建 ocr_menus 和 ocr_menu_items 表
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, OCRMenu, OCRMenuItem
from sqlalchemy import text

def create_ocr_tables():
    """創建 OCR 相關表"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 檢查 OCR 相關表...")
            
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # 檢查 ocr_menus 表
            if 'ocr_menus' not in existing_tables:
                print("❌ ocr_menus 表不存在，正在創建...")
                
                # 使用 SQL 創建表（符合同事的結構）
                create_ocr_menus_sql = """
                CREATE TABLE ocr_menus (
                    ocr_menu_id BIGINT NOT NULL AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    store_name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
                    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (ocr_menu_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='非合作店家用戶OCR菜單主檔'
                """
                
                db.session.execute(text(create_ocr_menus_sql))
                db.session.commit()
                print("✅ ocr_menus 表創建成功")
            else:
                print("✅ ocr_menus 表已存在")
            
            # 檢查 ocr_menu_items 表
            if 'ocr_menu_items' not in existing_tables:
                print("❌ ocr_menu_items 表不存在，正在創建...")
                
                # 使用 SQL 創建表（符合同事的結構）
                create_ocr_menu_items_sql = """
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
                
                db.session.execute(text(create_ocr_menu_items_sql))
                db.session.commit()
                print("✅ ocr_menu_items 表創建成功")
            else:
                print("✅ ocr_menu_items 表已存在")
            
            # 檢查表結構
            print("🔍 檢查表結構...")
            
            # 檢查 ocr_menus 表結構
            if 'ocr_menus' in existing_tables:
                columns = inspector.get_columns('ocr_menus')
                column_names = [col['name'] for col in columns]
                
                expected_columns = ['ocr_menu_id', 'user_id', 'store_name', 'upload_time']
                missing_columns = [col for col in expected_columns if col not in column_names]
                
                if missing_columns:
                    print(f"⚠️  ocr_menus 表缺少欄位: {missing_columns}")
                else:
                    print("✅ ocr_menus 表結構正確")
            
            # 檢查 ocr_menu_items 表結構
            if 'ocr_menu_items' in existing_tables:
                columns = inspector.get_columns('ocr_menu_items')
                column_names = [col['name'] for col in columns]
                
                expected_columns = ['ocr_menu_item_id', 'ocr_menu_id', 'item_name', 'price_big', 'price_small', 'translated_desc']
                missing_columns = [col for col in expected_columns if col not in column_names]
                
                if missing_columns:
                    print(f"⚠️  ocr_menu_items 表缺少欄位: {missing_columns}")
                else:
                    print("✅ ocr_menu_items 表結構正確")
            
            print("🎉 OCR 表創建完成！")
            return True
            
        except Exception as e:
            print(f"❌ 創建 OCR 表時發生錯誤: {e}")
            import traceback
            print(f"詳細錯誤: {traceback.format_exc()}")
            return False

def test_ocr_tables():
    """測試 OCR 表功能"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🧪 測試 OCR 表功能...")
            
            # 創建測試資料
            test_ocr_menu = OCRMenu(
                user_id=1,
                store_name="測試店家"
            )
            db.session.add(test_ocr_menu)
            db.session.flush()
            
            # 創建測試菜單項目
            test_item = OCRMenuItem(
                ocr_menu_id=test_ocr_menu.ocr_menu_id,
                item_name="測試菜品",
                price_small=100,
                price_big=150,
                translated_desc="Test Dish"
            )
            db.session.add(test_item)
            db.session.commit()
            
            print(f"✅ 測試資料創建成功")
            print(f"  - OCR 菜單 ID: {test_ocr_menu.ocr_menu_id}")
            print(f"  - 菜單項目 ID: {test_item.ocr_menu_item_id}")
            
            # 清理測試資料
            db.session.delete(test_ocr_menu)
            db.session.commit()
            print("✅ 測試資料清理完成")
            
            return True
            
        except Exception as e:
            print(f"❌ 測試 OCR 表功能時發生錯誤: {e}")
            return False

if __name__ == "__main__":
    print("🚀 開始創建 OCR 相關表...")
    
    if create_ocr_tables():
        print("✅ OCR 表創建成功")
        
        # 測試表功能
        if test_ocr_tables():
            print("✅ OCR 表功能測試通過")
        else:
            print("❌ OCR 表功能測試失敗")
    else:
        print("❌ OCR 表創建失敗")
        sys.exit(1) 