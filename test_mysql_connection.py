#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 資料庫連線測試腳本
功能：測試提供的 DATABASE_URL 是否能夠成功連線
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pymysql

def test_mysql_connection():
    """測試 MySQL 資料庫連線"""
    
    # 您提供的資料庫連線字串
    DATABASE_URL = "mysql+aiomysql://gae252g1usr:gae252g1PSWD%21@35.201.153.17:3306/gae252g1_db"
    
    print("🔍 開始測試 MySQL 資料庫連線...")
    print(f"📡 連線字串: {DATABASE_URL}")
    
    try:
        # 測試 1: 使用 PyMySQL（您的系統目前使用的驅動程式）
        print("\n📋 測試 1: 使用 PyMySQL 驅動程式")
        pymysql_url = DATABASE_URL.replace("mysql+aiomysql://", "mysql+pymysql://")
        print(f"轉換後的連線字串: {pymysql_url}")
        
        engine = create_engine(pymysql_url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            print("✅ PyMySQL 連線成功！")
            
            # 測試查詢資料庫版本
            version_result = connection.execute(text("SELECT VERSION() as version"))
            version = version_result.fetchone()
            print(f"📊 MySQL 版本: {version[0]}")
            
            # 測試查詢資料庫名稱
            db_result = connection.execute(text("SELECT DATABASE() as database_name"))
            db_name = db_result.fetchone()
            print(f"🗄️  當前資料庫: {db_name[0]}")
            
            # 列出所有表格
            tables_result = connection.execute(text("SHOW TABLES"))
            tables = [row[0] for row in tables_result.fetchall()]
            print(f"📋 資料庫中的表格 ({len(tables)} 個):")
            for table in tables:
                print(f"  - {table}")
                
    except SQLAlchemyError as e:
        print(f"❌ PyMySQL 連線失敗: {e}")
        
        # 測試 2: 嘗試使用 aiomysql（您原始字串中的驅動程式）
        print("\n📋 測試 2: 使用 aiomysql 驅動程式")
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test"))
                print("✅ aiomysql 連線成功！")
                
        except SQLAlchemyError as e:
            print(f"❌ aiomysql 連線也失敗: {e}")
            return False
    
    except Exception as e:
        print(f"❌ 連線測試失敗: {e}")
        return False
    
    print("\n✅ 資料庫連線測試完成！")
    return True

def test_database_structure():
    """測試資料庫結構"""
    print("\n🔍 測試資料庫結構...")
    
    DATABASE_URL = "mysql+aiomysql://gae252g1usr:gae252g1PSWD%21@35.201.153.17:3306/gae252g1_db"
    pymysql_url = DATABASE_URL.replace("mysql+aiomysql://", "mysql+pymysql://")
    
    try:
        engine = create_engine(pymysql_url)
        with engine.connect() as connection:
            
            # 檢查必要的表格
            required_tables = [
                'users', 'languages', 'stores', 'menus', 'menu_items', 
                'menu_translations', 'orders', 'order_items', 'voice_files',
                'ocr_menus', 'ocr_menu_items', 'store_translations'
            ]
            
            existing_tables = []
            for table in required_tables:
                try:
                    result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    existing_tables.append((table, count))
                    print(f"✅ {table}: {count} 筆資料")
                except Exception as e:
                    print(f"❌ {table}: 表格不存在或無法存取 - {e}")
            
            # 檢查語言資料
            try:
                lang_result = connection.execute(text("SELECT lang_code, lang_name FROM languages"))
                languages = lang_result.fetchall()
                print(f"\n🌐 支援的語言 ({len(languages)} 種):")
                for lang in languages:
                    print(f"  - {lang[0]}: {lang[1]}")
            except Exception as e:
                print(f"❌ 無法查詢語言資料: {e}")
            
            # 檢查店家資料
            try:
                store_result = connection.execute(text("SELECT store_id, store_name, partner_level FROM stores LIMIT 5"))
                stores = store_result.fetchall()
                print(f"\n🏪 店家資料 (前 5 筆):")
                for store in stores:
                    print(f"  - ID: {store[0]}, 名稱: {store[1]}, 等級: {store[2]}")
            except Exception as e:
                print(f"❌ 無法查詢店家資料: {e}")
                
    except Exception as e:
        print(f"❌ 資料庫結構測試失敗: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 MySQL 資料庫連線測試工具")
    print("=" * 50)
    
    # 測試基本連線
    if test_mysql_connection():
        # 測試資料庫結構
        test_database_structure()
    else:
        print("\n❌ 基本連線測試失敗，無法進行結構測試")
    
    print("\n" + "=" * 50)
    print("🏁 測試完成")
