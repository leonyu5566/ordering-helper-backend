#!/usr/bin/env python3
"""
測試訂單格式修復
驗證後端能正確處理前端的雙語格式訂單資料
"""

import requests
import json
import sys
import time

# API 配置
API_BASE_URL = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"

def test_order_format_fix():
    """測試訂單格式修復"""
    print("🧪 測試訂單格式修復")
    print("=" * 50)
    
    # 測試資料：模擬前端發送的雙語格式
    test_order_data = {
        "line_user_id": f"test_user_{int(time.time())}",
        "store_id": "46",
        "language": "zh-TW",
        "items": [
            {
                "name": {
                    "original": "爆冰濃縮",
                    "translated": "Super Ice Espresso"
                },
                "quantity": 1,
                "price": 74,
                "menu_item_id": "ocr_6_1"  # 模擬 OCR 菜單項目 ID
            },
            {
                "name": {
                    "original": "美式咖啡",
                    "translated": "American Coffee"
                },
                "quantity": 2,
                "price": 65,
                "menu_item_id": "ocr_6_2"
            }
        ]
    }
    
    print("📤 發送測試訂單資料:")
    print(json.dumps(test_order_data, indent=2, ensure_ascii=False))
    print()
    
    try:
        # 發送訂單
        response = requests.post(
            f"{API_BASE_URL}/api/orders",
            json=test_order_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 API 回應狀態: {response.status_code}")
        print(f"📥 API 回應標頭: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 訂單提交成功！")
            print("📊 回應資料:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 驗證回應格式
            if "order_id" in result:
                print(f"✅ 訂單 ID: {result['order_id']}")
            if "total_amount" in result:
                print(f"✅ 總金額: {result['total_amount']}")
            if "order_details" in result:
                print(f"✅ 訂單明細數量: {len(result['order_details'])}")
                
        else:
            print("❌ 訂單提交失敗")
            try:
                error_data = response.json()
                print("📊 錯誤回應:")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(f"📊 錯誤回應 (純文字): {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ 請求失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")
        return False
    
    return response.status_code == 200

def test_simple_order():
    """測試簡單訂單格式"""
    print("\n🧪 測試簡單訂單格式")
    print("=" * 50)
    
    # 測試資料：簡單格式
    simple_order_data = {
        "line_user_id": f"simple_user_{int(time.time())}",
        "store_id": "46",
        "language": "zh-TW",
        "items": [
            {
                "item_name": "測試商品",
                "translated_name": "Test Product",
                "quantity": 1,
                "price": 100,
                "menu_item_id": "temp_1"
            }
        ]
    }
    
    print("📤 發送簡單訂單資料:")
    print(json.dumps(simple_order_data, indent=2, ensure_ascii=False))
    print()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/orders",
            json=simple_order_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 API 回應狀態: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 簡單訂單提交成功！")
            print(f"📊 訂單 ID: {result.get('order_id', 'N/A')}")
        else:
            print("❌ 簡單訂單提交失敗")
            try:
                error_data = response.json()
                print("📊 錯誤回應:")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(f"📊 錯誤回應 (純文字): {response.text}")
                
    except Exception as e:
        print(f"❌ 請求失敗: {e}")
        return False
    
    return response.status_code == 200

def main():
    """主函數"""
    print("🚀 開始測試訂單格式修復")
    print("=" * 60)
    
    # 測試 1: 雙語格式訂單
    success1 = test_order_format_fix()
    
    # 測試 2: 簡單格式訂單
    success2 = test_simple_order()
    
    # 總結
    print("\n" + "=" * 60)
    print("📋 測試總結:")
    print(f"  雙語格式訂單: {'✅ 成功' if success1 else '❌ 失敗'}")
    print(f"  簡單格式訂單: {'✅ 成功' if success2 else '❌ 失敗'}")
    
    if success1 and success2:
        print("\n🎉 所有測試通過！訂單格式修復成功！")
        return 0
    else:
        print("\n⚠️ 部分測試失敗，需要進一步檢查")
        return 1

if __name__ == "__main__":
    sys.exit(main())
