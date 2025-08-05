#!/usr/bin/env python3
"""
測試生產環境的臨時訂單修復
直接測試部署在 Cloud Run 的 API
"""

import requests
import json

# 生產環境 URL
BASE_URL = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"

def test_temp_order():
    """測試臨時訂單提交"""
    
    # 模擬前端發送的臨時訂單資料
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

def test_health_check():
    """測試健康檢查"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        print(f"🏥 健康檢查狀態碼：{response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康檢查失敗：{e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始測試生產環境修復...")
    
    # 先測試健康檢查
    print("\n🏥 測試服務健康狀態...")
    health_ok = test_health_check()
    
    if not health_ok:
        print("❌ 服務不可用，跳過訂單測試")
        return
    
    # 測試臨時訂單
    print("\n🧪 測試臨時訂單...")
    temp_success = test_temp_order()
    
    print("\n📊 測試結果：")
    print(f"  服務健康：{'✅ 正常' if health_ok else '❌ 異常'}")
    print(f"  臨時訂單：{'✅ 成功' if temp_success else '❌ 失敗'}")
    
    if health_ok and temp_success:
        print("\n🎉 所有測試通過！修復成功！")
    elif health_ok:
        print("\n⚠️  服務正常但臨時訂單仍有問題")
        print("💡 建議：檢查代碼是否已部署到生產環境")
    else:
        print("\n💥 服務異常，無法測試")

if __name__ == "__main__":
    main() 