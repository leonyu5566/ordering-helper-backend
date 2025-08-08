#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新增缺少的資料庫欄位
功能：為 order_items 表新增缺少的欄位
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

def add_missing_columns():
    """新增缺少的欄位"""
    engine = get_database_connection()
    
    print("🔧 開始新增缺少的資料庫欄位...")
    
    try:
        with engine.connect() as connection:
            
            # 檢查 order_items 表結構
            print("\n📋 檢查 order_items 表結構...")
            result = connection.execute(text("DESCRIBE order_items"))
            existing_columns = [row[0] for row in result.fetchall()]
            
            print(f"現有欄位: {', '.join(existing_columns)}")
            
            # 需要新增的欄位
            missing_columns = [
                ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
                ('original_name', 'VARCHAR(100) NULL'),
                ('translated_name', 'VARCHAR(100) NULL')
            ]
            
            # 新增缺少的欄位
            for column_name, column_def in missing_columns:
                if column_name not in existing_columns:
                    print(f"\n➕ 新增欄位: {column_name}")
                    sql = f"ALTER TABLE order_items ADD COLUMN {column_name} {column_def}"
                    print(f"執行 SQL: {sql}")
                    
                    try:
                        connection.execute(text(sql))
                        connection.commit()
                        print(f"✅ 成功新增欄位: {column_name}")
                    except SQLAlchemyError as e:
                        print(f"❌ 新增欄位失敗: {column_name} - {e}")
                else:
                    print(f"✅ 欄位已存在: {column_name}")
            
            # 驗證新增結果
            print("\n📋 驗證新增結果...")
            result = connection.execute(text("DESCRIBE order_items"))
            final_columns = [row[0] for row in result.fetchall()]
            
            print(f"最終欄位: {', '.join(final_columns)}")
            
            # 檢查是否所有必要欄位都存在
            required_columns = ['order_item_id', 'order_id', 'menu_item_id', 'quantity_small', 
                              'subtotal', 'created_at', 'original_name', 'translated_name']
            
            missing_required = [col for col in required_columns if col not in final_columns]
            
            if missing_required:
                print(f"❌ 仍缺少必要欄位: {missing_required}")
                return False
            else:
                print("✅ 所有必要欄位都已存在")
                return True
                
    except Exception as e:
        print(f"❌ 新增欄位過程中發生錯誤: {e}")
        return False

def test_order_items_functionality():
    """測試 order_items 表功能"""
    engine = get_database_connection()
    
    print("\n🧪 測試 order_items 表功能...")
    
    try:
        with engine.connect() as connection:
            
            # 測試插入資料
            print("測試插入測試資料...")
            test_sql = """
            INSERT INTO order_items (order_id, menu_item_id, quantity_small, subtotal, 
                                   original_name, translated_name) 
            VALUES (1, 1, 2, 200, '測試菜名', 'Test Dish Name')
            """
            
            try:
                connection.execute(text(test_sql))
                connection.commit()
                print("✅ 測試資料插入成功")
                
                # 查詢測試資料
                result = connection.execute(text("SELECT * FROM order_items WHERE original_name = '測試菜名'"))
                test_data = result.fetchone()
                
                if test_data:
                    print("✅ 測試資料查詢成功")
                    print(f"測試資料: {test_data}")
                    
                    # 清理測試資料
                    cleanup_sql = "DELETE FROM order_items WHERE original_name = '測試菜名'"
                    connection.execute(text(cleanup_sql))
                    connection.commit()
                    print("✅ 測試資料清理完成")
                    
                else:
                    print("❌ 測試資料查詢失敗")
                    
            except SQLAlchemyError as e:
                print(f"❌ 測試失敗: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False
    
    return True

def main():
    """主函數"""
    print("🚀 開始資料庫欄位遷移...")
    
    # 新增缺少的欄位
    if add_missing_columns():
        print("\n✅ 欄位新增完成")
        
        # 測試功能
        if test_order_items_functionality():
            print("\n🎉 資料庫遷移成功！")
            print("📝 所有必要欄位都已新增並通過功能測試")
        else:
            print("\n❌ 功能測試失敗")
    else:
        print("\n❌ 欄位新增失敗")

if __name__ == "__main__":
    main()
