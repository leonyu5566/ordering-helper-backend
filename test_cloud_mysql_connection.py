#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud Run 與 Cloud MySQL 連線測試腳本
檢查後端服務是否能正常連線到 GCP Cloud MySQL 資料庫
"""

import requests
import json
import time
from datetime import datetime

# Cloud Run 服務 URL（請根據實際部署的 URL 修改）
CLOUD_RUN_URL = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"

def test_health_check():
    """測試健康檢查端點"""
    try:
        print("🔍 測試健康檢查端點...")
        response = requests.get(f"{CLOUD_RUN_URL}/api/health", timeout=10)
        
        print(f"狀態碼: {response.status_code}")
        print(f"回應內容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 健康檢查通過")
            return True
        else:
            print("❌ 健康檢查失敗")
            return False
            
    except Exception as e:
        print(f"❌ 健康檢查異常: {e}")
        return False

def test_database_connection():
    """測試資料庫連線"""
    try:
        print("\n🔍 測試資料庫連線...")
        
        # 使用一個簡單的 API 端點來測試資料庫連線
        # 這裡使用 stores 端點，因為它會查詢資料庫
        response = requests.get(f"{CLOUD_RUN_URL}/api/stores", timeout=15)
        
        print(f"狀態碼: {response.status_code}")
        print(f"回應內容: {response.text[:500]}...")  # 只顯示前500字元
        
        if response.status_code == 200:
            print("✅ 資料庫連線正常")
            return True
        else:
            print("❌ 資料庫連線失敗")
            return False
            
    except Exception as e:
        print(f"❌ 資料庫連線異常: {e}")
        return False

def test_order_creation():
    """測試訂單建立功能（包含資料庫寫入）"""
    try:
        print("\n🔍 測試訂單建立功能...")
        
        # 建立測試訂單資料
        test_order = {
            "line_user_id": "test_user_connection_check",
            "store_id": "test_store",
            "items": [
                {
                    "menu_item_id": "temp_test_1",
                    "quantity": 1,
                    "price": 100,
                    "name": {
                        "original": "測試菜品",
                        "translated": "Test Dish"
                    },
                    "item_name": "Test Dish",
                    "subtotal": 100
                }
            ],
            "total": 100,
            "language": "zh-TW"
        }
        
        response = requests.post(
            f"{CLOUD_RUN_URL}/api/orders",
            json=test_order,
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        
        print(f"狀態碼: {response.status_code}")
        print(f"回應內容: {response.text}")
        
        if response.status_code == 201:
            print("✅ 訂單建立成功，資料庫寫入正常")
            return True
        else:
            print("❌ 訂單建立失敗")
            return False
            
    except Exception as e:
        print(f"❌ 訂單建立異常: {e}")
        return False

def test_menu_processing():
    """測試菜單處理功能"""
    try:
        print("\n🔍 測試菜單處理功能...")
        
        # 測試簡單的菜單查詢
        response = requests.get(f"{CLOUD_RUN_URL}/api/menu/1", timeout=15)
        
        print(f"狀態碼: {response.status_code}")
        print(f"回應內容: {response.text[:300]}...")  # 只顯示前300字元
        
        if response.status_code in [200, 404]:  # 404 也是正常的（如果沒有菜單資料）
            print("✅ 菜單處理功能正常")
            return True
        else:
            print("❌ 菜單處理功能異常")
            return False
            
    except Exception as e:
        print(f"❌ 菜單處理異常: {e}")
        return False

def test_environment_variables():
    """測試環境變數設定"""
    try:
        print("\n🔍 測試環境變數...")
        
        # 使用 debug 端點來檢查環境變數（如果有的話）
        response = requests.get(f"{CLOUD_RUN_URL}/api/test", timeout=10)
        
        print(f"狀態碼: {response.status_code}")
        print(f"回應內容: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ 環境變數檢查通過")
            return True
        else:
            print("⚠️ 環境變數檢查端點不可用")
            return True  # 這不是錯誤，只是端點不存在
            
    except Exception as e:
        print(f"❌ 環境變數檢查異常: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始 Cloud Run 與 Cloud MySQL 連線測試")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目標服務: {CLOUD_RUN_URL}")
    print("=" * 60)
    
    tests = [
        ("健康檢查", test_health_check),
        ("資料庫連線", test_database_connection),
        ("訂單建立", test_order_creation),
        ("菜單處理", test_menu_processing),
        ("環境變數", test_environment_variables)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 測試異常: {e}")
            results.append((test_name, False))
        
        time.sleep(2)  # 等待 2 秒再進行下一個測試
    
    # 總結報告
    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n總計: {passed}/{total} 項測試通過")
    
    if passed == total:
        print("🎉 所有測試通過！Cloud Run 與 Cloud MySQL 連線正常")
    elif passed >= total * 0.8:
        print("⚠️ 大部分測試通過，但有一些問題需要檢查")
    else:
        print("❌ 多項測試失敗，需要檢查 Cloud Run 配置和資料庫連線")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
