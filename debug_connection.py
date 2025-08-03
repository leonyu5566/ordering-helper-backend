#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試資料庫連線問題
"""

import pymysql
from dotenv import load_dotenv
import os
from app import create_app
from app.models import db, Store

# 載入環境變數
load_dotenv('notebook.env')

def test_direct_connection():
    """測試直接 PyMySQL 連線"""
    print("🔍 測試直接 PyMySQL 連線...")
    try:
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
        print("✅ 直接 PyMySQL 連線成功！")
        connection.close()
        return True
    except Exception as e:
        print(f"❌ 直接 PyMySQL 連線失敗：{e}")
        return False

def test_flask_connection():
    """測試 Flask SQLAlchemy 連線"""
    print("\n🔍 測試 Flask SQLAlchemy 連線...")
    try:
        app = create_app()
        with app.app_context():
            # 檢查資料庫連線字串
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            print(f"📋 資料庫連線字串: {db_uri}")
            
            # 嘗試查詢
            stores = Store.query.all()
            print(f"✅ Flask SQLAlchemy 連線成功！找到 {len(stores)} 個店家")
            return True
    except Exception as e:
        print(f"❌ Flask SQLAlchemy 連線失敗：{e}")
        return False

def compare_environment_variables():
    """比較環境變數"""
    print("\n🔍 檢查環境變數...")
    vars_to_check = ['DB_HOST', 'DB_USERNAME', 'DB_PASSWORD', 'DB_NAME']
    
    for var in vars_to_check:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:10]}..." if len(value) > 10 else f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: 未設定")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 資料庫連線調試工具")
    print("=" * 60)
    
    # 檢查環境變數
    compare_environment_variables()
    
    # 測試直接連線
    direct_success = test_direct_connection()
    
    # 測試 Flask 連線
    flask_success = test_flask_connection()
    
    print("\n" + "=" * 60)
    print("📊 測試結果總結：")
    print(f"直接 PyMySQL 連線: {'✅ 成功' if direct_success else '❌ 失敗'}")
    print(f"Flask SQLAlchemy 連線: {'✅ 成功' if flask_success else '❌ 失敗'}")
    
    if direct_success and not flask_success:
        print("\n💡 問題分析：")
        print("- 直接 PyMySQL 連線成功，但 Flask SQLAlchemy 失敗")
        print("- 可能是 SQLAlchemy 連線字串格式問題")
        print("- 或 SSL 設定差異") 