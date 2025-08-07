#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列出所有資料庫表格
功能：詳細顯示資料庫中的 19 個表格及其結構
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def list_all_tables():
    """列出所有資料庫表格"""
    
    # 資料庫連線字串
    DATABASE_URL = "mysql+aiomysql://gae252g1usr:gae252g1PSWD%21@35.201.153.17:3306/gae252g1_db"
    pymysql_url = DATABASE_URL.replace("mysql+aiomysql://", "mysql+pymysql://")
    
    print("📋 資料庫表格詳細列表")
    print("=" * 60)
    
    try:
        engine = create_engine(pymysql_url)
        with engine.connect() as connection:
            
            # 獲取所有表格
            tables_result = connection.execute(text("SHOW TABLES"))
            tables = [row[0] for row in tables_result.fetchall()]
            
            print(f"🗄️  總共 {len(tables)} 個表格：\n")
            
            # 分類表格
            core_tables = ['users', 'languages', 'stores', 'menus', 'menu_items', 'menu_translations', 'orders', 'order_items', 'voice_files', 'store_translations']
            ocr_tables = ['ocr_menus', 'ocr_menu_items']
            system_tables = ['account', 'crawl_logs', 'gemini_processing', 'menu_crawls', 'menu_templates', 'reviews', 'user_actions']
            
            print("🎯 核心業務表格 (10 個)：")
            print("-" * 40)
            for i, table in enumerate(core_tables, 1):
                try:
                    count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.fetchone()[0]
                    print(f"{i:2d}. {table:<20} ({count:>3} 筆資料)")
                except:
                    print(f"{i:2d}. {table:<20} (無法查詢)")
            
            print("\n📸 OCR 處理表格 (2 個)：")
            print("-" * 40)
            for i, table in enumerate(ocr_tables, 1):
                try:
                    count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.fetchone()[0]
                    print(f"{i:2d}. {table:<20} ({count:>3} 筆資料)")
                except:
                    print(f"{i:2d}. {table:<20} (無法查詢)")
            
            print("\n⚙️  系統功能表格 (7 個)：")
            print("-" * 40)
            for i, table in enumerate(system_tables, 1):
                try:
                    count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.fetchone()[0]
                    print(f"{i:2d}. {table:<20} ({count:>3} 筆資料)")
                except:
                    print(f"{i:2d}. {table:<20} (無法查詢)")
            
            print("\n" + "=" * 60)
            print("📊 詳細表格結構：")
            print("=" * 60)
            
            # 顯示每個表格的詳細結構
            for table in sorted(tables):
                print(f"\n🔍 表格：{table}")
                print("-" * 40)
                
                try:
                    # 獲取表格結構
                    desc_result = connection.execute(text(f"DESCRIBE {table}"))
                    columns = desc_result.fetchall()
                    
                    print(f"{'欄位名稱':<20} {'類型':<20} {'NULL':<8} {'KEY':<8} {'DEFAULT':<15} {'EXTRA'}")
                    print("-" * 80)
                    
                    for col in columns:
                        field, type_name, null, key, default, extra = col
                        print(f"{field:<20} {type_name:<20} {null:<8} {key:<8} {str(default):<15} {extra}")
                    
                    # 獲取資料筆數
                    count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.fetchone()[0]
                    print(f"\n📈 資料筆數：{count}")
                    
                except Exception as e:
                    print(f"❌ 無法查詢表格結構：{e}")
                
                print("-" * 40)
            
    except SQLAlchemyError as e:
        print(f"❌ 資料庫連線失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        return False
    
    return True

def show_table_summary():
    """顯示表格摘要"""
    print("\n" + "=" * 60)
    print("📋 表格功能說明：")
    print("=" * 60)
    
    table_descriptions = {
        # 核心業務表格
        'users': '使用者管理 - 儲存 LINE Bot 使用者資訊',
        'languages': '語言管理 - 支援 193 種語言',
        'stores': '店家管理 - 合作和非合作店家資訊',
        'menus': '菜單主檔 - 店家菜單版本管理',
        'menu_items': '菜單項目 - 具體菜品資訊',
        'menu_translations': '菜單翻譯 - 多語言菜品翻譯',
        'orders': '訂單主檔 - 使用者訂單記錄',
        'order_items': '訂單項目 - 訂單中的具體項目',
        'voice_files': '語音檔案 - 訂單語音檔案管理',
        'store_translations': '店家翻譯 - 店家資訊多語言翻譯',
        
        # OCR 處理表格
        'ocr_menus': 'OCR 菜單主檔 - 非合作店家拍照辨識',
        'ocr_menu_items': 'OCR 菜單項目 - 辨識出的菜品資訊',
        
        # 系統功能表格
        'account': '帳戶管理 - 系統帳戶資訊',
        'crawl_logs': '爬蟲日誌 - 資料爬取記錄',
        'gemini_processing': 'AI 處理記錄 - Gemini API 使用記錄',
        'menu_crawls': '菜單爬取 - 自動菜單資料收集',
        'menu_templates': '菜單模板 - 標準化菜單格式',
        'reviews': '評論管理 - 店家評論資料',
        'user_actions': '使用者行為 - 使用者操作記錄'
    }
    
    for table, description in table_descriptions.items():
        print(f"📋 {table:<20} - {description}")

if __name__ == "__main__":
    print("🚀 資料庫表格詳細列表工具")
    print("=" * 60)
    
    if list_all_tables():
        show_table_summary()
        print("\n✅ 表格列表完成！")
    else:
        print("\n❌ 無法獲取表格列表")
    
    print("\n" + "=" * 60)
    print("🏁 完成")
