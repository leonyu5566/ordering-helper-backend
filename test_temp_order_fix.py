#!/usr/bin/env python3
"""
測試臨時訂單修復
驗證後端是否能正確處理臨時菜單項目
"""

import requests
import json

# 測試配置
BASE_URL = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"

def test_temp_order():
    """測試臨時訂單提交"""
    
    # 模擬前端發送的臨時訂單資料
    temp_order_data = {
        "store_id": 1,  # 假設的店家ID
        "line_user_id": None,  # 訪客模式
        "language": "zh",
        "items": [
            {
                "id": "temp_36_0",  # 臨時ID
                "item_name": "奶油經典夏威夷",
                "price": 115,
                "quantity": 1
            }
        ]
    }
    
    print("🧪 測試臨時訂單提交...")
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
        
        if response.status_code == 201:
            print("✅ 測試成功！臨時訂單已正確處理")
            return True
        else:
            print("❌ 測試失敗！")
            return False
            
    except Exception as e:
        print(f"❌ 請求失敗：{e}")
        return False

def test_regular_order():
    """測試正式訂單提交（對比）"""
    
    # 模擬正式訂單資料
    regular_order_data = {
        "store_id": 1,
        "line_user_id": None,
        "language": "zh",
        "items": [
            {
                "menu_item_id": 1,  # 正式的菜單項目ID
                "quantity": 1
            }
        ]
    }
    
    print("\n🧪 測試正式訂單提交...")
    print(f"📤 發送資料：{json.dumps(regular_order_data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orders",
            headers={"Content-Type": "application/json"},
            json=regular_order_data,
            timeout=30
        )
        
        print(f"📥 回應狀態碼：{response.status_code}")
        print(f"📥 回應內容：{response.text}")
        
        if response.status_code == 201:
            print("✅ 正式訂單測試成功！")
            return True
        else:
            print("❌ 正式訂單測試失敗！")
            return False
            
    except Exception as e:
        print(f"❌ 請求失敗：{e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始測試臨時訂單修復...")
    
    # 測試臨時訂單
    temp_success = test_temp_order()
    
    # 測試正式訂單
    regular_success = test_regular_order()
    
    print("\n📊 測試結果：")
    print(f"  臨時訂單：{'✅ 成功' if temp_success else '❌ 失敗'}")
    print(f"  正式訂單：{'✅ 成功' if regular_success else '❌ 失敗'}")
    
    if temp_success and regular_success:
        print("\n🎉 所有測試通過！修復成功！")
    else:
        print("\n💥 部分測試失敗，需要進一步檢查")

if __name__ == "__main__":
    main() 