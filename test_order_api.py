#!/usr/bin/env python3
"""
訂單 API 測試腳本
測試 line_user_id 可選功能的修復
"""

import requests
import json
import sys

# API 基礎 URL
BASE_URL = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"

def test_order_with_line_user_id():
    """測試帶有 line_user_id 的訂單（LINE 入口）"""
    print("=== 測試 1: LINE 入口訂單 ===")
    
    order_data = {
        "line_user_id": "test_line_user_123",
        "store_id": 1,
        "language": "zh",
        "items": [
            {
                "menu_item_id": 1,
                "quantity": 2,
                "price_unit": 100
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/orders", json=order_data)
        print(f"狀態碼: {response.status_code}")
        print(f"回應: {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ 成功建立訂單，ID: {result.get('order_id')}")
        else:
            print("❌ 訂單建立失敗")
            
    except Exception as e:
        print(f"❌ 請求失敗: {e}")

def test_order_without_line_user_id():
    """測試沒有 line_user_id 的訂單（非 LINE 入口）"""
    print("\n=== 測試 2: 非 LINE 入口訂單 ===")
    
    order_data = {
        "store_id": 1,
        "language": "zh",
        "items": [
            {
                "menu_item_id": 1,
                "quantity": 1,
                "price_unit": 100
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/orders", json=order_data)
        print(f"狀態碼: {response.status_code}")
        print(f"回應: {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ 成功建立訪客訂單，ID: {result.get('order_id')}")
        else:
            print("❌ 訪客訂單建立失敗")
            
    except Exception as e:
        print(f"❌ 請求失敗: {e}")

def test_order_with_old_format():
    """測試舊格式的訂單資料"""
    print("\n=== 測試 3: 舊格式訂單資料 ===")
    
    order_data = {
        "store_id": 1,
        "items": [
            {
                "id": 1,           # 舊格式
                "qty": 1,          # 舊格式
                "price": 100       # 舊格式
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/orders", json=order_data)
        print(f"狀態碼: {response.status_code}")
        print(f"回應: {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ 成功建立舊格式訂單，ID: {result.get('order_id')}")
        else:
            print("❌ 舊格式訂單建立失敗")
            
    except Exception as e:
        print(f"❌ 請求失敗: {e}")

def test_invalid_order():
    """測試無效的訂單資料"""
    print("\n=== 測試 4: 無效訂單資料 ===")
    
    # 缺少必要欄位
    order_data = {
        "store_id": 1
        # 缺少 items
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/orders", json=order_data)
        print(f"狀態碼: {response.status_code}")
        print(f"回應: {response.text}")
        
        if response.status_code == 400:
            print("✅ 正確拒絕無效訂單")
        else:
            print("❌ 應該拒絕無效訂單")
            
    except Exception as e:
        print(f"❌ 請求失敗: {e}")

def test_menu_api():
    """測試菜單 API 是否正常"""
    print("\n=== 測試 5: 菜單 API ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/menu/1?lang=zh")
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 菜單 API 正常，項目數量: {len(result.get('menu_items', []))}")
        else:
            print("❌ 菜單 API 失敗")
            
    except Exception as e:
        print(f"❌ 請求失敗: {e}")

def main():
    """執行所有測試"""
    print("開始測試訂單 API 修復...")
    print("=" * 50)
    
    # 測試菜單 API
    test_menu_api()
    
    # 測試訂單 API
    test_order_with_line_user_id()
    test_order_without_line_user_id()
    test_order_with_old_format()
    test_invalid_order()
    
    print("\n" + "=" * 50)
    print("測試完成！")

if __name__ == "__main__":
    main() 