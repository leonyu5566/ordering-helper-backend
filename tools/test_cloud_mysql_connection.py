#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud Run 與 Cloud MySQL 連線測試腳本

功能：
1. 測試 Cloud Run 服務是否正常運行
2. 測試資料庫連線是否正常
3. 測試基本的 CRUD 操作
4. 檢查資料庫結構是否符合預期
5. 測試訂單建立功能

使用方法：
python3 tools/test_cloud_mysql_connection.py
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_cloud_run_health():
    """測試 Cloud Run 健康檢查"""
    print("🔍 測試 Cloud Run 健康檢查...")
    
    try:
        # 這裡需要替換為實際的 Cloud Run URL
        base_url = os.getenv('CLOUD_RUN_URL', 'https://your-cloud-run-service-url')
        
        # 測試健康檢查端點
        health_url = f"{base_url}/api/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Cloud Run 服務正常運行")
            return True
        else:
            print(f"❌ Cloud Run 服務異常，狀態碼: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cloud Run 連線失敗: {e}")
        return False

def test_database_connection():
    """測試資料庫連線"""
    print("\n🔍 測試資料庫連線...")
    
    try:
        base_url = os.getenv('CLOUD_RUN_URL', 'https://your-cloud-run-service-url')
        
        # 測試店家列表查詢
        stores_url = f"{base_url}/api/stores"
        response = requests.get(stores_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 資料庫連線正常")
            print(f"📊 查詢到 {len(data)} 個店家")
            return True
        else:
            print(f"❌ 資料庫查詢失敗，狀態碼: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 資料庫連線失敗: {e}")
        return False

def test_menu_functionality():
    """測試菜單功能"""
    print("\n🔍 測試菜單功能...")
    
    try:
        base_url = os.getenv('CLOUD_RUN_URL', 'https://your-cloud-run-service-url')
        
        # 測試菜單查詢（使用預設店家 ID）
        menu_url = f"{base_url}/api/menu/1"
        response = requests.get(menu_url, timeout=10)
        
        if response.status_code in [200, 404]:
            print("✅ 菜單查詢功能正常")
            if response.status_code == 404:
                print("ℹ️ 沒有找到菜單資料（這是正常的）")
            return True
        else:
            print(f"❌ 菜單查詢失敗，狀態碼: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 菜單功能測試失敗: {e}")
        return False

def test_order_creation():
    """測試訂單建立功能"""
    print("\n🔍 測試訂單建立功能...")
    
    try:
        base_url = os.getenv('CLOUD_RUN_URL', 'https://your-cloud-run-service-url')
        
        # 準備測試訂單資料
        test_order = {
            "lang": "zh-TW",
            "items": [
                {
                    "name": {
                        "original": "測試菜名",
                        "translated": "Test Dish"
                    },
                    "quantity": 1,
                    "price": 100
                }
            ],
            "line_user_id": "test_user_123"
        }
        
        # 測試訂單建立
        order_url = f"{base_url}/api/orders/simple"
        response = requests.post(
            order_url,
            json=test_order,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code in [201, 200]:
            print("✅ 訂單建立功能正常")
            data = response.json()
            if 'order_id' in data:
                print(f"📝 訂單 ID: {data['order_id']}")
            return True
        else:
            print(f"❌ 訂單建立失敗，狀態碼: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📋 錯誤詳情: {error_data}")
            except:
                print(f"📋 錯誤回應: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 訂單建立測試失敗: {e}")
        return False

def test_database_schema():
    """測試資料庫結構"""
    print("\n🔍 測試資料庫結構...")
    
    try:
        base_url = os.getenv('CLOUD_RUN_URL', 'https://your-cloud-run-service-url')
        
        # 測試資料庫結構檢查端點
        schema_url = f"{base_url}/api/admin/migrate-database"
        response = requests.post(schema_url, timeout=30)
        
        if response.status_code in [200, 201]:
            print("✅ 資料庫結構檢查正常")
            return True
        else:
            print(f"❌ 資料庫結構檢查失敗，狀態碼: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 資料庫結構測試失敗: {e}")
        return False

def test_ocr_functionality():
    """測試 OCR 功能"""
    print("\n🔍 測試 OCR 功能...")
    
    try:
        base_url = os.getenv('CLOUD_RUN_URL', 'https://your-cloud-run-service-url')
        
        # 測試 OCR 端點
        ocr_url = f"{base_url}/api/menu/simple-ocr"
        
        # 準備測試資料（模擬圖片上傳）
        test_data = {
            "lang": "zh-TW",
            "store_id": "non-partner"
        }
        
        response = requests.post(
            ocr_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code in [200, 201, 400]:
            print("✅ OCR 端點正常回應")
            return True
        else:
            print(f"❌ OCR 端點異常，狀態碼: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ OCR 功能測試失敗: {e}")
        return False

def generate_test_report(results):
    """生成測試報告"""
    print("\n" + "="*50)
    print("📊 Cloud Run 與 Cloud MySQL 連線測試報告")
    print("="*50)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"測試時間: {timestamp}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n測試結果: {passed_tests}/{total_tests} 項通過 ({passed_tests/total_tests*100:.1f}%)")
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"- {test_name}: {status}")
    
    # 生成建議
    print("\n📋 建議:")
    if passed_tests == total_tests:
        print("🎉 所有測試通過！系統運行正常。")
    elif passed_tests >= total_tests * 0.8:
        print("⚠️ 大部分功能正常，建議檢查失敗的項目。")
    else:
        print("🚨 多項測試失敗，建議立即檢查系統配置。")
    
    return results

def main():
    """主測試函數"""
    print("🚀 開始 Cloud Run 與 Cloud MySQL 連線測試...")
    print("="*50)
    
    # 檢查環境變數
    cloud_run_url = os.getenv('CLOUD_RUN_URL')
    if not cloud_run_url:
        print("⚠️ 警告: 未設定 CLOUD_RUN_URL 環境變數")
        print("請設定正確的 Cloud Run 服務 URL")
        return
    
    print(f"🌐 測試目標: {cloud_run_url}")
    
    # 執行測試
    results = {}
    
    results["Cloud Run 健康檢查"] = test_cloud_run_health()
    results["資料庫連線"] = test_database_connection()
    results["菜單功能"] = test_menu_functionality()
    results["訂單建立"] = test_order_creation()
    results["資料庫結構"] = test_database_schema()
    results["OCR 功能"] = test_ocr_functionality()
    
    # 生成報告
    generate_test_report(results)
    
    # 保存報告到檔案
    save_report_to_file(results, timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"))

def save_report_to_file(results, timestamp):
    """保存測試報告到檔案"""
    report_content = f"""# Cloud Run 與 Cloud MySQL 連線測試報告

## 測試時間
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 測試結果

"""
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    report_content += f"總計: {passed_tests}/{total_tests} 項測試通過 ({passed_tests/total_tests*100:.1f}%)\n\n"
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        report_content += f"- {test_name}: {status}\n"
    
    # 保存到檔案
    filename = f"cloud_mysql_connection_test_{timestamp}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n📄 測試報告已保存到: {filename}")

if __name__ == "__main__":
    main()
