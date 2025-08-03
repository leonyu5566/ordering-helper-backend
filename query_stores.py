#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查詢店家資料的腳本
"""

import pymysql
from dotenv import load_dotenv
import os

# 載入環境變數
load_dotenv('notebook.env')

def query_stores():
    """查詢店家資料"""
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
        
        print("🔍 查詢店家資料...")
        print("=" * 60)
        
        # 查詢店家資料
        with connection.cursor() as cursor:
            # 先檢查表格結構
            cursor.execute("DESCRIBE stores")
            columns = cursor.fetchall()
            print("📋 stores 表格結構：")
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
            print("-" * 40)
            
            # 查詢店家資料
            cursor.execute("SELECT * FROM stores ORDER BY store_id")
            stores = cursor.fetchall()
            
            if stores:
                print(f"📊 資料庫中共有 {len(stores)} 個店家：")
                print("=" * 60)
                
                for store in stores:
                    print(f"🏪 店家資料: {store}")
                    print("-" * 40)
            else:
                print("📭 資料庫中沒有店家資料")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 查詢失敗：{e}")
        return False

if __name__ == "__main__":
    success = query_stores()
    
    if success:
        print("\n🎉 查詢完成！")
    else:
        print("\n💥 查詢失敗！") 