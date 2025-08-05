#!/usr/bin/env python3
"""
診斷臨時訂單問題
詳細分析為什麼修復還沒有生效
"""

import requests
import json

# 生產環境 URL
BASE_URL = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"

def test_api_version():
    """測試 API 版本和部署狀態"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        print(f"🏥 健康檢查：{response.status_code}")
        if response.status_code == 200:
            print(f"📋 回應內容：{response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康檢查失敗：{e}")
        return False

def test_debug_endpoint():
    """測試除錯端點"""
    debug_data = {
        "store_id": 1,
        "line_user_id": None,
        "language": "zh",
        "items": [
            {
                "id": "temp_36_0",
                "item_name": "奶油經典夏威夷",
                "price": 115,
                "quantity": 1
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/debug/order-data",
            headers={"Content-Type": "application/json"},
            json=debug_data,
            timeout=30
        )
        
        print(f"🔍 除錯端點狀態碼：{response.status_code}")
        print(f"🔍 除錯回應：{response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 除錯端點失敗：{e}")
        return False

def test_temp_order_with_details():
    """詳細測試臨時訂單"""
    temp_order_data = {
        "store_id": 1,
        "line_user_id": None,
        "language": "zh",
        "items": [
            {
                "id": "temp_36_0",
                "item_name": "奶油經典夏威夷",
                "price": 115,
                "quantity": 1
            }
        ]
    }
    
    print("\n🧪 詳細測試臨時訂單...")
    print(f"📤 發送資料：{json.dumps(temp_order_data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orders",
            headers={"Content-Type": "application/json"},
            json=temp_order_data,
            timeout=30
        )
        
        print(f"📥 回應狀態碼：{response.status_code}")
        print(f"📥 回應內容：{response.text}")
        
        if response.status_code == 400:
            # 解析錯誤訊息
            try:
                error_data = response.json()
                if "validation_errors" in error_data:
                    print("\n🔍 驗證錯誤分析：")
                    for error in error_data["validation_errors"]:
                        print(f"  - {error}")
                    
                    if "找不到菜單項目 ID temp_36_0" in str(error_data):
                        print("\n💡 問題分析：")
                        print("  - 後端仍然在檢查資料庫中的正式 menu_item_id")
                        print("  - 修復代碼可能還沒有部署或生效")
                        print("  - 或者資料庫結構還沒有更新")
            except:
                pass
        
        return response.status_code == 201
        
    except Exception as e:
        print(f"❌ 請求失敗：{e}")
        return False

def test_regular_order():
    """測試正式訂單作為對比"""
    regular_order_data = {
        "store_id": 1,
        "line_user_id": None,
        "language": "zh",
        "items": [
            {
                "menu_item_id": 1,
                "quantity": 1
            }
        ]
    }
    
    print("\n🧪 測試正式訂單（對比）...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orders",
            headers={"Content-Type": "application/json"},
            json=regular_order_data,
            timeout=30
        )
        
        print(f"📥 正式訂單狀態碼：{response.status_code}")
        print(f"📥 正式訂單回應：{response.text}")
        
        return response.status_code == 201
        
    except Exception as e:
        print(f"❌ 正式訂單測試失敗：{e}")
        return False

def main():
    """主診斷函數"""
    print("🔍 開始診斷臨時訂單問題...")
    
    # 1. 測試服務健康狀態
    print("\n1️⃣ 測試服務健康狀態...")
    health_ok = test_api_version()
    
    if not health_ok:
        print("❌ 服務不可用，無法繼續診斷")
        return
    
    # 2. 測試除錯端點
    print("\n2️⃣ 測試除錯端點...")
    debug_ok = test_debug_endpoint()
    
    # 3. 詳細測試臨時訂單
    print("\n3️⃣ 詳細測試臨時訂單...")
    temp_ok = test_temp_order_with_details()
    
    # 4. 測試正式訂單
    print("\n4️⃣ 測試正式訂單...")
    regular_ok = test_regular_order()
    
    # 5. 總結分析
    print("\n📊 診斷結果：")
    print(f"  服務健康：{'✅ 正常' if health_ok else '❌ 異常'}")
    print(f"  除錯端點：{'✅ 可用' if debug_ok else '❌ 不可用'}")
    print(f"  臨時訂單：{'✅ 成功' if temp_ok else '❌ 失敗'}")
    print(f"  正式訂單：{'✅ 成功' if regular_ok else '❌ 失敗'}")
    
    print("\n💡 建議：")
    if not temp_ok:
        print("  - 修復代碼可能還沒有部署到生產環境")
        print("  - 或者資料庫結構還沒有更新")
        print("  - 建議檢查 GitHub Actions 部署狀態")
        print("  - 或者手動執行資料庫遷移")

if __name__ == "__main__":
    main() 