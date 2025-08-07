#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
欄位名稱同步測試腳本
功能：測試修正後的API端點是否使用統一的欄位名稱
"""

import requests
import json
import time

# 測試環境設定
BASE_URL = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"

def test_menu_api():
    """測試菜單API的欄位名稱"""
    print("🧪 測試菜單API欄位名稱...")
    
    try:
        # 測試合作店家菜單
        response = requests.get(f"{BASE_URL}/api/menu/1", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            menu_items = data.get('menu_items', [])
            
            if menu_items:
                item = menu_items[0]
                print("✅ 菜單項目欄位檢查：")
                
                # 檢查必要欄位
                required_fields = ['menu_item_id', 'item_name', 'price_small']
                for field in required_fields:
                    if field in item:
                        print(f"  ✅ {field}: {item[field]}")
                    else:
                        print(f"  ❌ 缺少欄位: {field}")
                
                # 檢查可選欄位
                optional_fields = ['price_big', 'description', 'translated_name']
                for field in optional_fields:
                    if field in item:
                        print(f"  ✅ {field}: {item[field]}")
                    else:
                        print(f"  ⚠️ 可選欄位: {field} (未提供)")
                
                return True
            else:
                print("⚠️ 沒有菜單項目可測試")
                return False
        else:
            print(f"❌ API請求失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_order_api():
    """測試訂單API的欄位名稱"""
    print("\n🧪 測試訂單API欄位名稱...")
    
    # 準備測試訂單資料
    test_order_data = {
        "user_id": "test_user_123",
        "store_id": 1,
        "items": [
            {
                "menu_item_id": 1,
                "quantity": 2,
                "price_small": 120,
                "item_name": "測試菜品",
                "subtotal": 240
            }
        ],
        "total_amount": 240,
        "language": "zh"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orders",
            json=test_order_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📤 發送測試訂單...")
        print(f"📥 回應狀態: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("✅ 訂單API欄位檢查：")
            
            # 檢查回應欄位
            response_fields = ['order_id', 'message', 'order_details']
            for field in response_fields:
                if field in data:
                    print(f"  ✅ {field}: {data[field]}")
                else:
                    print(f"  ⚠️ 回應欄位: {field} (未提供)")
            
            return True
        else:
            print(f"❌ 訂單API失敗: {response.status_code}")
            print(f"錯誤訊息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_simple_order_api():
    """測試簡單訂單API的欄位名稱"""
    print("\n🧪 測試簡單訂單API欄位名稱...")
    
    # 準備測試資料
    test_data = {
        "items": [
            {
                "name": "測試菜品",
                "quantity": 1,
                "price": 100
            }
        ],
        "user_language": "zh",
        "line_user_id": "test_user_123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orders/simple",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📤 發送簡單訂單...")
        print(f"📥 回應狀態: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("✅ 簡單訂單API欄位檢查：")
            
            # 檢查回應欄位
            response_fields = ['success', 'order_id', 'total_amount', 'chinese_summary', 'user_summary']
            for field in response_fields:
                if field in data:
                    print(f"  ✅ {field}: {data[field]}")
                else:
                    print(f"  ⚠️ 回應欄位: {field} (未提供)")
            
            return True
        else:
            print(f"❌ 簡單訂單API失敗: {response.status_code}")
            print(f"錯誤訊息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_store_api():
    """測試店家API的欄位名稱"""
    print("\n🧪 測試店家API欄位名稱...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/stores/1", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 店家API欄位檢查：")
            
            # 檢查店家資訊欄位
            store_info = data.get('store_info', {})
            store_fields = ['store_id', 'store_name', 'partner_level', 'gps_lat', 'gps_lng']
            for field in store_fields:
                if field in store_info:
                    print(f"  ✅ {field}: {store_info[field]}")
                else:
                    print(f"  ⚠️ 店家欄位: {field} (未提供)")
            
            return True
        else:
            print(f"❌ 店家API失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始欄位名稱同步測試...")
    print("=" * 50)
    
    # 執行測試
    tests = [
        ("菜單API", test_menu_api),
        ("訂單API", test_order_api),
        ("簡單訂單API", test_simple_order_api),
        ("店家API", test_store_api)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 測試: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 測試異常: {e}")
            results.append((test_name, False))
    
    # 顯示測試結果
    print("\n" + "=" * 50)
    print("📊 測試結果總結：")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 總體結果: {passed}/{total} 測試通過")
    
    if passed == total:
        print("🎉 所有測試通過！欄位名稱同步成功！")
    else:
        print("⚠️ 部分測試失敗，請檢查API端點")
    
    print("\n💡 建議：")
    print("1. 檢查失敗的API端點")
    print("2. 確認欄位名稱是否正確統一")
    print("3. 測試前端和Line Bot的整合")
    print("4. 進行完整的功能測試")

if __name__ == "__main__":
    main()
