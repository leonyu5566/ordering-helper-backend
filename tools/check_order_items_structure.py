#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 order_items 表結構
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

def check_order_items_structure():
    """檢查 order_items 表結構"""
    engine = get_database_connection()
    
    try:
        with engine.connect() as connection:
            # 檢查 order_items 表結構
            result = connection.execute(text("DESCRIBE order_items"))
            columns = result.fetchall()
            
            print("📋 order_items 表結構:")
            print("=" * 60)
            print(f"{'欄位名稱':<20} {'類型':<20} {'NULL':<8} {'KEY':<8} {'DEFAULT':<15} {'EXTRA':<10}")
            print("-" * 60)
            
            for col in columns:
                field_name = col[0]
                field_type = col[1]
                null_allowed = col[2]
                key_type = col[3]
                default_value = col[4] if col[4] else 'NULL'
                extra = col[5] if col[5] else ''
                
                print(f"{field_name:<20} {field_type:<20} {null_allowed:<8} {key_type:<8} {default_value:<15} {extra:<10}")
            
            print("\n" + "=" * 60)
            print("📊 欄位統計:")
            print(f"總欄位數: {len(columns)}")
            
            # 檢查是否有 created_at 欄位
            has_created_at = any(col[0] == 'created_at' for col in columns)
            print(f"是否有 created_at 欄位: {'✅ 是' if has_created_at else '❌ 否'}")
            
            # 檢查是否有 original_name 欄位
            has_original_name = any(col[0] == 'original_name' for col in columns)
            print(f"是否有 original_name 欄位: {'✅ 是' if has_original_name else '❌ 否'}")
            
            # 檢查是否有 translated_name 欄位
            has_translated_name = any(col[0] == 'translated_name' for col in columns)
            print(f"是否有 translated_name 欄位: {'✅ 是' if has_translated_name else '❌ 否'}")
            
    except Exception as e:
        print(f"❌ 檢查過程中發生錯誤: {e}")

if __name__ == "__main__":
    check_order_items_structure()
