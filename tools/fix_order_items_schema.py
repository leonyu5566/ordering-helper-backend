#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫遷移腳本：修復 order_items 表結構
確保符合 cloud_mysql_schema.md 的定義

主要功能：
1. 確保 order_items 表的所有必要欄位都存在
2. 為非合作店家的 OCR 菜單項目提供支援
3. 確保 menu_item_id 欄位的外鍵約束正確
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import OrderItem, MenuItem, Menu, Store, User
from sqlalchemy import text
import datetime

def fix_order_items_schema():
    """修復 order_items 表結構"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 開始修復 order_items 表結構...")
            
            # 1. 檢查並確保 order_items 表的所有必要欄位都存在
            print("📋 檢查 order_items 表欄位...")
            
            # 檢查 created_at 欄位
            try:
                db.session.execute(text("SELECT created_at FROM order_items LIMIT 1"))
                print("✅ created_at 欄位已存在")
            except Exception as e:
                print("❌ created_at 欄位不存在，正在新增...")
                db.session.execute(text("ALTER TABLE order_items ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                print("✅ created_at 欄位已新增")
            
            # 檢查 original_name 欄位
            try:
                db.session.execute(text("SELECT original_name FROM order_items LIMIT 1"))
                print("✅ original_name 欄位已存在")
            except Exception as e:
                print("❌ original_name 欄位不存在，正在新增...")
                db.session.execute(text("ALTER TABLE order_items ADD COLUMN original_name VARCHAR(100) NULL"))
                print("✅ original_name 欄位已新增")
            
            # 檢查 translated_name 欄位
            try:
                db.session.execute(text("SELECT translated_name FROM order_items LIMIT 1"))
                print("✅ translated_name 欄位已存在")
            except Exception as e:
                print("❌ translated_name 欄位不存在，正在新增...")
                db.session.execute(text("ALTER TABLE order_items ADD COLUMN translated_name VARCHAR(100) NULL"))
                print("✅ translated_name 欄位已新增")
            
            # 2. 確保 menu_item_id 欄位的外鍵約束正確
            print("🔗 檢查 menu_item_id 外鍵約束...")
            
            # 檢查外鍵約束是否存在
            try:
                result = db.session.execute(text("""
                    SELECT CONSTRAINT_NAME 
                    FROM information_schema.KEY_COLUMN_USAGE 
                    WHERE TABLE_NAME = 'order_items' 
                    AND COLUMN_NAME = 'menu_item_id' 
                    AND REFERENCED_TABLE_NAME = 'menu_items'
                """)).fetchall()
                
                if result:
                    print("✅ menu_item_id 外鍵約束已存在")
                else:
                    print("⚠️ menu_item_id 外鍵約束不存在，正在新增...")
                    db.session.execute(text("""
                        ALTER TABLE order_items 
                        ADD CONSTRAINT fk_order_items_menu_item_id 
                        FOREIGN KEY (menu_item_id) REFERENCES menu_items(menu_item_id)
                    """))
                    print("✅ menu_item_id 外鍵約束已新增")
            except Exception as e:
                print(f"⚠️ 外鍵約束檢查失敗: {e}")
            
            # 3. 為非合作店家創建預設的菜單結構
            print("🏪 檢查並創建預設店家結構...")
            
            # 查找或創建預設店家
            default_store = Store.query.filter_by(store_name='預設店家').first()
            if not default_store:
                print("📝 創建預設店家...")
                default_store = Store(
                    store_name='預設店家',
                    partner_level=0  # 非合作店家
                )
                db.session.add(default_store)
                db.session.flush()
                print(f"✅ 預設店家已創建，ID: {default_store.store_id}")
            else:
                print(f"✅ 預設店家已存在，ID: {default_store.store_id}")
            
            # 查找或創建預設菜單
            default_menu = Menu.query.filter_by(store_id=default_store.store_id).first()
            if not default_menu:
                print("📋 創建預設菜單...")
                default_menu = Menu(
                    store_id=default_store.store_id,
                    version=1,
                    effective_date=datetime.datetime.now()
                )
                db.session.add(default_menu)
                db.session.flush()
                print(f"✅ 預設菜單已創建，ID: {default_menu.menu_id}")
            else:
                print(f"✅ 預設菜單已存在，ID: {default_menu.menu_id}")
            
            # 4. 檢查並修復現有的無效 menu_item_id
            print("🔍 檢查現有的無效 menu_item_id...")
            
            # 查找所有 menu_item_id 為 NULL 的 order_items
            invalid_items = db.session.execute(text("""
                SELECT oi.order_item_id, oi.menu_item_id, oi.original_name, oi.translated_name
                FROM order_items oi 
                WHERE oi.menu_item_id IS NULL
            """)).fetchall()
            
            if invalid_items:
                print(f"⚠️ 發現 {len(invalid_items)} 個無效的 menu_item_id，正在修復...")
                
                for item in invalid_items:
                    try:
                        # 為每個無效項目創建臨時的 MenuItem
                        item_name = item.original_name or item.translated_name or '臨時項目'
                        
                        temp_menu_item = MenuItem(
                            menu_id=default_menu.menu_id,
                            item_name=item_name,
                            price_small=0,  # 預設價格
                            price_big=0
                        )
                        db.session.add(temp_menu_item)
                        db.session.flush()
                        
                        # 更新 order_item 的 menu_item_id
                        db.session.execute(text("""
                            UPDATE order_items 
                            SET menu_item_id = :menu_item_id 
                            WHERE order_item_id = :order_item_id
                        """), {
                            'menu_item_id': temp_menu_item.menu_item_id,
                            'order_item_id': item.order_item_id
                        })
                        
                        print(f"✅ 已修復 order_item_id: {item.order_item_id}")
                        
                    except Exception as e:
                        print(f"❌ 修復 order_item_id {item.order_item_id} 失敗: {e}")
                        continue
            else:
                print("✅ 沒有發現無效的 menu_item_id")
            
            # 5. 提交所有變更
            db.session.commit()
            print("✅ 所有資料庫變更已提交")
            
            # 6. 驗證修復結果
            print("🔍 驗證修復結果...")
            
            # 檢查是否還有無效的 menu_item_id
            remaining_invalid = db.session.execute(text("""
                SELECT COUNT(*) as count
                FROM order_items 
                WHERE menu_item_id IS NULL
            """)).fetchone()
            
            if remaining_invalid.count == 0:
                print("✅ 所有 menu_item_id 都已有效")
            else:
                print(f"⚠️ 仍有 {remaining_invalid.count} 個無效的 menu_item_id")
            
            print("🎉 order_items 表結構修復完成！")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 修復失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == "__main__":
    success = fix_order_items_schema()
    if success:
        print("✅ 資料庫遷移成功完成")
        sys.exit(0)
    else:
        print("❌ 資料庫遷移失敗")
        sys.exit(1)
