#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查資料庫中的菜單資料
"""

import pymysql
from dotenv import load_dotenv
import os

# 載入環境變數
load_dotenv('notebook.env')

def check_menu_data():
    """檢查菜單資料"""
    try:
        # 建立連線
        connection = pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USERNAME'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=3306,
            charset='utf8mb4',
            ssl={'ssl': {}},
            server_public_key=True
        )
        
        print("🔍 檢查菜單資料...")
        print("=" * 60)
        
        with connection.cursor() as cursor:
            # 檢查所有表格
            cursor.execute("SHOW TABLES")
            all_tables = cursor.fetchall()
            print("📋 所有表格：")
            for table in all_tables:
                print(f"  - {table[0]}")
            
            print("\n" + "-" * 40)
            
            # 檢查菜單相關表格
            cursor.execute("SHOW TABLES LIKE '%menu%'")
            menu_tables = cursor.fetchall()
            print("📋 菜單相關表格：")
            for table in menu_tables:
                print(f"  - {table[0]}")
            
            print("\n" + "-" * 40)
            
            # 檢查 ocr_menus 表格
            cursor.execute("SELECT COUNT(*) FROM ocr_menus")
            ocr_menu_count = cursor.fetchone()[0]
            print(f"📊 ocr_menus 表格記錄數: {ocr_menu_count}")
            
            if ocr_menu_count > 0:
                cursor.execute("SELECT * FROM ocr_menus LIMIT 3")
                ocr_menus = cursor.fetchall()
                print("📋 ocr_menus 表格資料（前3筆）：")
                for menu in ocr_menus:
                    print(f"  - {menu}")
            
            print("\n" + "-" * 40)
            
            # 檢查 ocr_menu_items 表格
            cursor.execute("SELECT COUNT(*) FROM ocr_menu_items")
            ocr_item_count = cursor.fetchone()[0]
            print(f"📊 ocr_menu_items 表格記錄數: {ocr_item_count}")
            
            if ocr_item_count > 0:
                cursor.execute("SELECT * FROM ocr_menu_items LIMIT 5")
                ocr_items = cursor.fetchall()
                print("📋 ocr_menu_items 表格資料（前5筆）：")
                for item in ocr_items:
                    print(f"  - {item}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 檢查失敗：{e}")
        return False

if __name__ == "__main__":
    success = check_menu_data()
    
    if success:
        print("\n🎉 檢查完成！")
    else:
        print("\n💥 檢查失敗！") 