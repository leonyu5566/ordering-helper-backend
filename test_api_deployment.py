#!/usr/bin/env python3
"""
測試部署的 API 是否正常工作
驗證雙語訂單處理功能
"""

import requests
import json

def test_api_deployment():
    """測試 API 部署"""
    base_url = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"
    
    print("🧪 測試 API 部署...")
    
    # 1. 測試健康檢查
    print("\n1️⃣ 測試健康檢查...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ 健康檢查通過")
            print(f"   回應: {response.json()}")
        else:
            print(f"❌ 健康檢查失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康檢查異常: {e}")
    
    # 2. 測試舊格式訂單
    print("\n2️⃣ 測試舊格式訂單...")
    old_format_request = {
        "store_id": 1,
        "items": [
            {
                "item_name": "經典夏威夷奶醬義大利麵",
                "quantity": 1,
                "price": 115
            },
            {
                "name": "奶油蝦仁鳳梨義大利麵",
                "qty": 1,
                "price_small": 140
            }
        ],
        "language": "en",
        "line_user_id": "U1234567890abcdef"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/orders",
            json=old_format_request,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            result = response.json()
            print("✅ 舊格式訂單處理成功")
            print(f"   訂單ID: {result.get('order_id')}")
            print(f"   總金額: {result.get('total_amount')}")
            print(f"   中文摘要: {result.get('zh_summary')}")
            print(f"   使用者摘要: {result.get('user_summary')}")
            print(f"   語音URL: {result.get('voice_url')}")
        else:
            print(f"❌ 舊格式訂單處理失敗: {response.status_code}")
            print(f"   錯誤: {response.text}")
    except Exception as e:
        print(f"❌ 舊格式訂單處理異常: {e}")
    
    # 3. 測試新格式訂單
    print("\n3️⃣ 測試新格式訂單...")
    new_format_request = {
        "lang": "en",
        "items": [
            {
                "name": {
                    "original": "經典夏威夷奶醬義大利麵",
                    "translated": "Creamy Classic Hawaiian"
                },
                "quantity": 1,
                "price": 115
            },
            {
                "name": {
                    "original": "奶油蝦仁鳳梨義大利麵",
                    "translated": "Creamy Shrimp Pineapple"
                },
                "quantity": 1,
                "price": 140
            }
        ],
        "line_user_id": "U1234567890abcdef"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/orders/simple",
            json=new_format_request,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            result = response.json()
            print("✅ 新格式訂單處理成功")
            print(f"   訂單ID: {result.get('order_id')}")
            print(f"   總金額: {result.get('total_amount')}")
            print(f"   中文摘要: {result.get('zh_summary')}")
            print(f"   使用者摘要: {result.get('user_summary')}")
            print(f"   語音URL: {result.get('voice_url')}")
        else:
            print(f"❌ 新格式訂單處理失敗: {response.status_code}")
            print(f"   錯誤: {response.text}")
    except Exception as e:
        print(f"❌ 新格式訂單處理異常: {e}")
    
    # 4. 測試臨時訂單（非合作店家）
    print("\n4️⃣ 測試臨時訂單...")
    temp_order_request = {
        "store_id": "non-partner",
        "items": [
            {
                "id": "temp_36_0",
                "item_name": "奶油經典夏威夷",
                "price": 115,
                "quantity": 1
            }
        ],
        "language": "zh",
        "line_user_id": "U1234567890abcdef"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/orders",
            json=temp_order_request,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            result = response.json()
            print("✅ 臨時訂單處理成功")
            print(f"   訂單ID: {result.get('order_id')}")
            print(f"   總金額: {result.get('total_amount')}")
            print(f"   中文摘要: {result.get('zh_summary')}")
            print(f"   使用者摘要: {result.get('user_summary')}")
            print(f"   語音URL: {result.get('voice_url')}")
        else:
            print(f"❌ 臨時訂單處理失敗: {response.status_code}")
            print(f"   錯誤: {response.text}")
    except Exception as e:
        print(f"❌ 臨時訂單處理異常: {e}")
    
    print("\n🎉 API 部署測試完成!")

if __name__ == "__main__":
    test_api_deployment()
