#!/usr/bin/env python3
"""
資料庫重建腳本
用於重新建立資料庫結構，包含所有最新的模型變更
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import *
from tools.manage_translations import init_languages

def rebuild_database():
    """重建資料庫"""
    app = create_app()
    
    with app.app_context():
        print("🗑️  刪除所有資料表...")
        db.drop_all()
        
        print("🏗️  重新建立資料表...")
        db.create_all()
        
        print("🌐  初始化語言資料...")
        init_languages()
        
        print("✅ 資料庫重建完成！")
        
        # 顯示建立的資料表
        print("\n📋 已建立的資料表：")
        for table in db.metadata.tables.keys():
            print(f"  - {table}")

if __name__ == "__main__":
    print("🚀 開始重建資料庫...")
    rebuild_database() 