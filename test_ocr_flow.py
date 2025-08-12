#!/usr/bin/env python3
"""
OCR菜單流程測試腳本
測試修改後的OCR菜單處理流程
"""

import requests
import json
import os
from datetime import datetime

# 測試配置
BASE_URL = "http://localhost:5000"  # 本地測試
# BASE_URL = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"  # 生產環境

def test_ocr_flow():
    """測試完整的OCR菜單流程"""
    print("🧪 開始測試OCR菜單流程...")
    
    # 測試1: 上傳菜單圖片（模擬）
    print("\n1️⃣ 測試菜單OCR處理...")
    
    # 由於沒有實際圖片，我們模擬一個成功的OCR回應
    mock_ocr_response = {
        "success": True,
        "ocr_menu_id": 123,
        "menu_items": [
            {
                "id": "ocr_123_1",
                "original_name": "宮保雞丁",
                "translated_name": "Kung Pao Chicken",
                "price": 180,
                "description": "經典川菜",
                "category": "主菜"
            },
            {
                "id": "ocr_123_2", 
                "original_name": "麻婆豆腐",
                "translated_name": "Mapo Tofu",
                "price": 120,
                "description": "四川名菜",
                "category": "主菜"
            }
        ],
        "store_name": "川菜館",
        "saved_to_database": True
    }
    
    print(f"✅ OCR處理完成，菜單ID: {mock_ocr_response['ocr_menu_id']}")
    
    # 測試2: 取得OCR菜單資料
    print("\n2️⃣ 測試取得OCR菜單資料...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/menu/ocr/{mock_ocr_response['ocr_menu_id']}?lang=en")
        if response.status_code == 200:
            menu_data = response.json()
            print(f"✅ 成功取得菜單資料，共 {menu_data.get('total_items', 0)} 個項目")
            print(f"   店家名稱: {menu_data.get('store_name', 'N/A')}")
        else:
            print(f"❌ 取得菜單資料失敗: {response.status_code}")
            print(f"   錯誤訊息: {response.text}")
    except Exception as e:
        print(f"❌ 取得菜單資料時發生錯誤: {e}")
    
    # 測試3: 建立OCR菜單訂單
    print("\n3️⃣ 測試建立OCR菜單訂單...")
    
    order_data = {
        "ocr_menu_id": mock_ocr_response['ocr_menu_id'],
        "items": [
            {
                "id": "ocr_123_1",
                "quantity": 2,
                "price": 180,
                "item_name": "宮保雞丁",
                "translated_name": "Kung Pao Chicken"
            },
            {
                "id": "ocr_123_2",
                "quantity": 1,
                "price": 120,
                "item_name": "麻婆豆腐",
                "translated_name": "Mapo Tofu"
            }
        ],
        "line_user_id": "test_user_123",
        "language": "en",
        "store_id": 1
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orders/ocr",
            headers={"Content-Type": "application/json"},
            json=order_data
        )
        
        if response.status_code == 201:
            order_result = response.json()
            print(f"✅ 成功建立OCR訂單，訂單ID: {order_result.get('order_id')}")
            print(f"   總金額: ${order_result.get('total_amount', 0)}")
            print(f"   項目數量: {len(order_result.get('order_details', []))}")
            print(f"   OCR菜單ID: {order_result.get('ocr_menu_id')}")
            print(f"   店家名稱: {order_result.get('store_name')}")
        else:
            print(f"❌ 建立訂單失敗: {response.status_code}")
            print(f"   錯誤訊息: {response.text}")
    except Exception as e:
        print(f"❌ 建立訂單時發生錯誤: {e}")
    
    # 測試4: 查詢使用者OCR菜單歷史
    print("\n4️⃣ 測試查詢使用者OCR菜單歷史...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/menu/ocr/user/1")
        if response.status_code == 200:
            history_data = response.json()
            print(f"✅ 成功取得使用者菜單歷史，共 {history_data.get('total_count', 0)} 個菜單")
            for menu in history_data.get('ocr_menus', []):
                print(f"   - 菜單ID: {menu.get('ocr_menu_id')}, 店家: {menu.get('store_name')}, 項目數: {menu.get('item_count')}")
        else:
            print(f"❌ 取得菜單歷史失敗: {response.status_code}")
            print(f"   錯誤訊息: {response.text}")
    except Exception as e:
        print(f"❌ 取得菜單歷史時發生錯誤: {e}")
    
    # 測試5: 測試一般訂單建立（包含OCR項目）
    print("\n5️⃣ 測試一般訂單建立（包含OCR項目）...")
    
    general_order_data = {
        "items": [
            {
                "id": "ocr_123_1",
                "quantity": 1,
                "price": 180,
                "item_name": "宮保雞丁",
                "translated_name": "Kung Pao Chicken"
            }
        ],
        "line_user_id": "test_user_456",
        "language": "zh",
        "store_id": 1
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orders",
            headers={"Content-Type": "application/json"},
            json=general_order_data
        )
        
        if response.status_code == 201:
            order_result = response.json()
            print(f"✅ 成功建立一般訂單，訂單ID: {order_result.get('order_id')}")
            print(f"   總金額: ${order_result.get('total_amount', 0)}")
            print(f"   OCR菜單ID: {order_result.get('ocr_menu_id')}")
        else:
            print(f"❌ 建立一般訂單失敗: {response.status_code}")
            print(f"   錯誤訊息: {response.text}")
    except Exception as e:
        print(f"❌ 建立一般訂單時發生錯誤: {e}")
    
    print("\n🎉 OCR菜單流程測試完成！")

def test_api_endpoints():
    """測試API端點是否正常運作"""
    print("\n🔍 測試API端點...")
    
    endpoints = [
        "/api/menu/ocr/1",
        "/api/menu/ocr/user/1",
        "/api/orders/1/confirm"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            print(f"✅ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: 錯誤 - {e}")

if __name__ == "__main__":
    print("🚀 OCR菜單流程測試開始")
    print(f"📡 測試目標: {BASE_URL}")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 測試API端點
    test_api_endpoints()
    
    # 測試完整流程
    test_ocr_flow()
    
    print("\n✨ 所有測試完成！")
