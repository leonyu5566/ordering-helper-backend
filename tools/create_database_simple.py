#!/usr/bin/env python3
"""
簡單的資料庫創建腳本
不依賴外部 API，只創建基本的資料庫結構
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 設置環境變數以避免 API 錯誤
os.environ['GEMINI_API_KEY'] = 'dummy_key'
os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'dummy_token'
os.environ['LINE_CHANNEL_SECRET'] = 'dummy_secret'

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.models import db, Store, Menu, MenuItem, Language, User, Order, OrderItem
import datetime

def create_database_simple():
    """創建簡單的資料庫結構"""
    
    # 創建 Flask 應用
    app = Flask(__name__)
    
    # 設定資料庫（使用 SQLite）
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化資料庫
    db.init_app(app)
    
    with app.app_context():
        print("🗑️  刪除所有資料表...")
        db.drop_all()
        
        print("🏗️  重新建立資料表...")
        db.create_all()
        
        print("✅ 資料庫結構創建完成！")
        
        # 顯示建立的資料表
        print("\n📋 已建立的資料表：")
        for table in db.metadata.tables.keys():
            print(f"  - {table}")
        
        return True

if __name__ == "__main__":
    print("🚀 開始創建資料庫...")
    success = create_database_simple()
    if success:
        print("\n🎉 資料庫創建成功！")
    else:
        print("\n💥 資料庫創建失敗！")
        sys.exit(1) 