#!/usr/bin/env python3
"""
簡單的 Store ID 修復測試
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 設置環境變數以避免 API 錯誤
os.environ['GEMINI_API_KEY'] = 'dummy_key'
os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'dummy_token'
os.environ['LINE_CHANNEL_SECRET'] = 'dummy_secret'

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime

def simple_test():
    """簡單測試"""
    
    # 創建 Flask 應用
    app = Flask(__name__)
    
    # 設定資料庫（使用 SQLite）
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///simple.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 創建 SQLAlchemy 實例
    db = SQLAlchemy()
    db.init_app(app)
    
    # 定義簡單的模型
    class Store(db.Model):
        __tablename__ = 'stores'
        store_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        store_name = db.Column(db.String(100), nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    class Menu(db.Model):
        __tablename__ = 'menus'
        menu_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=False)
        version = db.Column(db.Integer, nullable=False, default=1)
        created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    with app.app_context():
        print("🚀 開始簡單測試...")
        
        # 1. 創建資料庫結構
        print("🏗️  創建資料庫結構...")
        db.create_all()
        
        # 2. 創建預設店家
        print("🏪 創建預設店家...")
        default_store = Store(
            store_name='預設店家',
            created_at=datetime.datetime.utcnow()
        )
        db.session.add(default_store)
        db.session.commit()
        print(f"  ✅ 預設店家已創建 (store_id: {default_store.store_id})")
        
        # 3. 創建預設菜單
        print("📋 創建預設菜單...")
        default_menu = Menu(
            store_id=default_store.store_id,
            version=1,
            created_at=datetime.datetime.utcnow()
        )
        db.session.add(default_menu)
        db.session.commit()
        print(f"  ✅ 預設菜單已創建 (menu_id: {default_menu.menu_id})")
        
        # 4. 顯示資料庫狀態
        print("\n📊 資料庫狀態：")
        print(f"  - 店家數量: {Store.query.count()}")
        print(f"  - 菜單數量: {Menu.query.count()}")
        
        print("\n✅ 簡單測試成功！")
        return True

if __name__ == "__main__":
    success = simple_test()
    if success:
        print("\n🎉 測試成功！")
    else:
        print("\n💥 測試失敗！")
        sys.exit(1) 