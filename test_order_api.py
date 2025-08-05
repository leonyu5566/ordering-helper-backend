#!/usr/bin/env python3
"""
訂單 API 測試腳本
用於驗證修改後的訂單建立功能
"""

import requests
import json

# 測試配置
BASE_URL = "http://localhost:5000"  # 根據你的環境調整
API_BASE = f"{BASE_URL}/api"

def test_debug_endpoint():
    """測試除錯端點"""
    print("🔍 測試除錯端點...")
    
    # 模擬前端可能發送的錯誤資料
    test_cases = [
        {
            "name": "正確格式",
            "data": {
                "line_user_id": "test_user_123",
                "store_id": 1,
                "items": [
                    {
                        "menu_item_id": 1,
                        "quantity": 2,
                        "price": 100
                    }
                ]
            }
        },
        {
            "name": "錯誤格式 - 使用 id 而不是 menu_item_id",
            "data": {
                "line_user_id": "test_user_123",
                "store_id": 1,
                "items": [
                    {
                        "id": 1,  # 錯誤：應該是 menu_item_id
                        "qty": 2,  # 錯誤：應該是 quantity
                        "price": 100
                    }
                ]
            }
        },
        {
            "name": "缺少必要欄位",
            "data": {
                "line_user_id": "test_user_123",
                # 缺少 store_id 和 items
            }
        },
        {
            "name": "空資料",
            "data": {}
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 測試案例: {test_case['name']}")
        try:
            response = requests.post(
                f"{API_BASE}/debug/order-data",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"狀態碼: {response.status_code}")
            print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            
        except Exception as e:
            print(f"❌ 請求失敗: {e}")

def test_order_creation():
    """測試訂單建立"""
    print("\n🛒 測試訂單建立...")
    
    # 測試正確格式
    correct_data = {
        "line_user_id": "test_user_123",
        "store_id": 1,
        "items": [
            {
                "menu_item_id": 1,
                "quantity": 2
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/orders",
            json=correct_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"正確格式 - 狀態碼: {response.status_code}")
        print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ 正確格式測試失敗: {e}")
    
    # 測試錯誤格式（使用舊的欄位名稱）
    wrong_data = {
        "line_user_id": "test_user_123",
        "store_id": 1,
        "items": [
            {
                "id": 1,  # 錯誤：應該是 menu_item_id
                "qty": 2,  # 錯誤：應該是 quantity
                "price": 100
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/orders",
            json=wrong_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\n錯誤格式 - 狀態碼: {response.status_code}")
        print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ 錯誤格式測試失敗: {e}")

def test_temp_order_creation():
    """測試臨時訂單建立"""
    print("\n📝 測試臨時訂單建立...")
    
    # 測試正確格式
    correct_data = {
        "processing_id": 1,
        "items": [
            {
                "original_name": "測試菜色",
                "translated_name": "Test Dish",
                "quantity": 2,
                "price": 100
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/orders/temp",
            json=correct_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"正確格式 - 狀態碼: {response.status_code}")
        print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ 正確格式測試失敗: {e}")

if __name__ == "__main__":
    print("🚀 開始測試訂單 API...")
    
    # 測試除錯端點
    test_debug_endpoint()
    
    # 測試訂單建立
    test_order_creation()
    
    # 測試臨時訂單建立
    test_temp_order_creation()
    
    print("\n✅ 測試完成！") 