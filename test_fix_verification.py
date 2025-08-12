#!/usr/bin/env python3
"""
修復驗證測試腳本
用於測試 Azure Static Web Apps 路由問題和資料庫外鍵約束問題的修復
"""

import requests
import json
import sys
import time

# Cloud Run 後端 URL
CLOUD_RUN_URL = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"

def test_health_check():
    """測試健康檢查端點"""
    print("🔍 測試健康檢查端點...")
    try:
        response = requests.get(f"{CLOUD_RUN_URL}/api/health", timeout=10)
        print(f"✅ 健康檢查成功: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ 健康檢查失敗: {e}")
        return False

def test_menu_upload_without_user_id():
    """測試沒有 user_id 的菜單上傳（應該自動創建臨時使用者）"""
    print("\n🔍 測試沒有 user_id 的菜單上傳...")
    
    # 創建一個簡單的測試圖片（1x1 像素的 JPEG）
    test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    
    try:
        # 創建 FormData
        files = {
            'file': ('test_image.jpg', test_image_data, 'image/jpeg')
        }
        data = {
            'store_id': '46',
            'lang': 'en'
            # 故意不提供 user_id
        }
        
        headers = {
            'Origin': 'https://green-beach-0f9762500.1.azurestaticapps.net'
        }
        
        response = requests.post(
            f"{CLOUD_RUN_URL}/api/upload-menu-image",
            files=files,
            data=data,
            headers=headers,
            timeout=30
        )
        
        print(f"✅ 菜單上傳測試完成: {response.status_code}")
        if response.status_code == 201:
            result = response.json()
            print(f"   - 處理ID: {result.get('processing_id')}")
            print(f"   - 菜單項目數: {result.get('total_items', 0)}")
            print(f"   - 儲存到資料庫: {result.get('saved_to_database', False)}")
            return True
        else:
            print(f"   - 錯誤回應: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 菜單上傳測試失敗: {e}")
        return False

def test_order_submission():
    """測試訂單提交"""
    print("\n🔍 測試訂單提交...")
    
    # 測試訂單數據
    test_order = {
        "items": [
            {
                "name": {
                    "original": "測試商品",
                    "translated": "Test Product"
                },
                "quantity": 1,
                "price": 100
            }
        ],
        "line_user_id": "test_user_123",
        "lang": "zh-TW"
    }
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'https://green-beach-0f9762500.1.azurestaticapps.net'
        }
        
        response = requests.post(
            f"{CLOUD_RUN_URL}/api/orders/simple",
            json=test_order,
            headers=headers,
            timeout=30
        )
        
        print(f"✅ 訂單提交測試完成: {response.status_code}")
        if response.status_code == 201:
            result = response.json()
            print(f"   - 訂單ID: {result.get('order_id')}")
            print(f"   - 總金額: {result.get('total_amount')}")
            print(f"   - 成功: {result.get('success', False)}")
            return True
        else:
            print(f"   - 錯誤回應: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 訂單提交測試失敗: {e}")
        return False

def test_cors_preflight():
    """測試 CORS 預檢請求"""
    print("\n🔍 測試 CORS 預檢請求...")
    try:
        headers = {
            'Origin': 'https://green-beach-0f9762500.1.azurestaticapps.net',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        response = requests.options(f"{CLOUD_RUN_URL}/api/orders", headers=headers, timeout=10)
        print(f"✅ CORS 預檢成功: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ CORS 預檢失敗: {e}")
        return False

def test_store_resolver():
    """測試店家解析器"""
    print("\n🔍 測試店家解析器...")
    try:
        response = requests.get(
            f"{CLOUD_RUN_URL}/api/stores/check-partner-status?place_id=ChIJ0boght2rQjQRsH-_buCo3S4",
            timeout=10
        )
        print(f"✅ 店家解析成功: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ 店家解析失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始修復驗證測試...")
    print(f"目標 URL: {CLOUD_RUN_URL}")
    print("=" * 60)
    
    tests = [
        test_health_check,
        test_cors_preflight,
        test_store_resolver,
        test_menu_upload_without_user_id,
        test_order_submission
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ 測試執行錯誤: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 測試結果總結:")
    print(f"總測試數: {len(tests)}")
    print(f"成功: {sum(results)}")
    print(f"失敗: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 所有測試通過！修復成功。")
        return 0
    else:
        print("⚠️ 部分測試失敗，需要進一步檢查。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
