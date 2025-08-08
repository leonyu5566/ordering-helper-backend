#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 order_items 表新增欄位
功能：驗證新增的欄位是否正常工作
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def get_database_connection():
    """取得資料庫連線"""
    DATABASE_URL = "mysql+aiomysql://gae252g1usr:gae252g1PSWD%21@35.201.153.17:3306/gae252g1_db"
    pymysql_url = DATABASE_URL.replace("mysql+aiomysql://", "mysql+pymysql://")
    return create_engine(pymysql_url)

def test_new_columns():
    """測試新增的欄位"""
    engine = get_database_connection()
    
    print("🧪 測試 order_items 表新增欄位...")
    
    try:
        with engine.connect() as connection:
            
            # 檢查欄位是否存在
            print("\n📋 檢查欄位結構...")
            result = connection.execute(text("DESCRIBE order_items"))
            columns = result.fetchall()
            
            required_columns = ['created_at', 'original_name', 'translated_name']
            existing_columns = [col[0] for col in columns]
            
            print(f"現有欄位: {', '.join(existing_columns)}")
            
            # 檢查必要欄位
            missing_columns = [col for col in required_columns if col not in existing_columns]
            
            if missing_columns:
                print(f"❌ 缺少欄位: {missing_columns}")
                return False
            else:
                print("✅ 所有必要欄位都存在")
            
            # 檢查欄位類型
            print("\n📋 檢查欄位類型...")
            for col in columns:
                if col[0] in required_columns:
                    print(f"   {col[0]}: {col[1]} (NULL: {col[2]}, DEFAULT: {col[4]})")
            
            # 測試 SELECT 查詢（不插入資料）
            print("\n📋 測試查詢功能...")
            try:
                result = connection.execute(text("SELECT order_item_id, created_at, original_name, translated_name FROM order_items LIMIT 1"))
                rows = result.fetchall()
                print(f"✅ 查詢成功，找到 {len(rows)} 筆資料")
                
                if rows:
                    print("範例資料結構:")
                    for row in rows:
                        print(f"   order_item_id: {row[0]}")
                        print(f"   created_at: {row[1]}")
                        print(f"   original_name: {row[2]}")
                        print(f"   translated_name: {row[3]}")
                
            except SQLAlchemyError as e:
                print(f"❌ 查詢失敗: {e}")
                return False
            
            print("\n✅ 所有測試通過！")
            return True
                
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

def main():
    """主函數"""
    if test_new_columns():
        print("\n🎉 欄位測試成功！")
        print("📝 order_items 表已成功新增以下欄位:")
        print("   - created_at (DATETIME DEFAULT CURRENT_TIMESTAMP)")
        print("   - original_name (VARCHAR(100) NULL)")
        print("   - translated_name (VARCHAR(100) NULL)")
    else:
        print("\n❌ 欄位測試失敗")

if __name__ == "__main__":
    main()
