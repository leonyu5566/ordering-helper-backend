#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Store Resolver 功能

這個腳本用來測試 store_resolver.py 的功能是否正常運作
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_store_resolver():
    """測試 Store Resolver 功能"""
    print("🧪 開始測試 Store Resolver...")
    
    try:
        # 測試 1: 基本功能
        print("\n📋 測試 1: 基本功能")
        from app.api.store_resolver import resolve_store_id, validate_store_id
        
        # 測試整數輸入
        result = resolve_store_id(123)
        print(f"✅ 整數輸入 123 -> {result}")
        
        # 測試數字字串輸入
        result = resolve_store_id("456")
        print(f"✅ 數字字串輸入 '456' -> {result}")
        
        # 測試 Google Place ID 輸入
        place_id = "ChlJ0boght2rQjQRsH-_buCo3S4"
        result = resolve_store_id(place_id)
        print(f"✅ Google Place ID 輸入 '{place_id}' -> {result}")
        
        # 測試 2: 驗證功能
        print("\n📋 測試 2: 驗證功能")
        
        # 測試有效格式
        valid_formats = [
            123,                    # 整數
            "456",                  # 數字字串
            "ChlJ0boght2rQjQRsH-_buCo3S4",  # Google Place ID
            "ChIJN1t_tDeuEmsRUsoyG83frY4"   # 另一個 Place ID
        ]
        
        for fmt in valid_formats:
            is_valid = validate_store_id(fmt)
            print(f"✅ 格式 {fmt} -> {'有效' if is_valid else '無效'}")
        
        # 測試無效格式
        invalid_formats = [
            "",                     # 空字串
            "abc",                  # 非數字字串
            "ChIJ",                 # 太短的 Place ID
            -1,                     # 負整數
            0                       # 零
        ]
        
        for fmt in invalid_formats:
            is_valid = validate_store_id(fmt)
            print(f"❌ 格式 {fmt} -> {'有效' if is_valid else '無效'}")
        
        # 測試 3: 重複解析同一個 Place ID
        print("\n📋 測試 3: 重複解析同一個 Place ID")
        place_id = "ChlJ0boght2rQjQRsH-_buCo3S4"
        
        # 第一次解析
        result1 = resolve_store_id(place_id)
        print(f"✅ 第一次解析 '{place_id}' -> {result1}")
        
        # 第二次解析（應該得到相同的結果）
        result2 = resolve_store_id(place_id)
        print(f"✅ 第二次解析 '{place_id}' -> {result2}")
        
        if result1 == result2:
            print(f"✅ 重複解析結果一致: {result1}")
        else:
            print(f"❌ 重複解析結果不一致: {result1} vs {result2}")
        
        print("\n🎉 所有測試完成！")
        return True
        
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        print("請確保 app 模組可以正確導入")
        return False
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """測試資料庫連線"""
    print("\n🔌 測試資料庫連線...")
    
    try:
        from app import create_app
        from app.models import db
        
        # 建立 Flask 應用
        app = create_app()
        
        with app.app_context():
            # 測試資料庫連線
            db.session.execute("SELECT 1")
            print("✅ 資料庫連線成功")
            
            # 測試 stores 表是否存在
            result = db.session.execute("SHOW TABLES LIKE 'stores'")
            if result.fetchone():
                print("✅ stores 表存在")
            else:
                print("❌ stores 表不存在")
                
            # 測試 place_id 欄位是否存在
            result = db.session.execute("DESCRIBE stores")
            columns = [row[0] for row in result.fetchall()]
            if 'place_id' in columns:
                print("✅ stores.place_id 欄位存在")
            else:
                print("❌ stores.place_id 欄位不存在")
                
        return True
        
    except Exception as e:
        print(f"❌ 資料庫連線測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 開始 Store Resolver 測試")
    print("=" * 50)
    
    # 測試資料庫連線
    db_ok = test_database_connection()
    
    if db_ok:
        # 測試 Store Resolver 功能
        resolver_ok = test_store_resolver()
        
        if resolver_ok:
            print("\n🎉 所有測試都通過了！")
            print("Store Resolver 已經準備好處理你的 Google Place ID 了！")
        else:
            print("\n❌ Store Resolver 測試失敗")
    else:
        print("\n❌ 資料庫連線測試失敗，無法進行 Store Resolver 測試")
    
    print("\n" + "=" * 50)
    print("測試完成")
