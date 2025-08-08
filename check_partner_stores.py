#!/usr/bin/env python3
"""
檢查合作店家資料庫連線和資料
"""

import os
import sys
import requests
from datetime import datetime

def check_api_endpoint():
    """檢查 API 端點"""
    # 嘗試連線到 Cloud Run 服務
    cloud_run_url = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"
    
    print(f"🌐 檢查 Cloud Run API 端點...")
    print(f"   服務 URL: {cloud_run_url}")
    
    try:
        # 健康檢查
        print("🔍 執行健康檢查...")
        response = requests.get(f"{cloud_run_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ 健康檢查通過")
            health_data = response.json()
            print(f"   狀態: {health_data.get('status', 'unknown')}")
            print(f"   時間戳: {health_data.get('timestamp', 'unknown')}")
        else:
            print(f"❌ 健康檢查失敗: {response.status_code}")
            print(f"   回應內容: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 無法連線到 Cloud Run 服務: {e}")
        return False
    
    try:
        # 檢查店家 API
        print("\n🔍 檢查店家 API...")
        response = requests.get(f"{cloud_run_url}/api/stores", timeout=10)
        if response.status_code == 200:
            print("✅ 店家 API 正常")
            stores_data = response.json()
            if stores_data.get('success'):
                stores = stores_data.get('stores', [])
                print(f"   API 返回 {len(stores)} 個店家")
                
                # 檢查合作店家
                partner_stores = [s for s in stores if s.get('partner_level', 0) > 0]
                non_partner_stores = [s for s in stores if s.get('partner_level', 0) == 0]
                
                print(f"   其中合作店家: {len(partner_stores)} 家")
                print(f"   非合作店家: {len(non_partner_stores)} 家")
                
                print("\n📋 店家詳細資訊:")
                for store in stores:
                    partner_status = "非合作店家" if store.get('partner_level', 0) == 0 else \
                                   "合作店家" if store.get('partner_level', 0) == 1 else \
                                   "VIP店家" if store.get('partner_level', 0) == 2 else "未知"
                    print(f"   📍 店家 ID: {store.get('store_id', 'N/A')}")
                    print(f"      店名: {store.get('store_name', 'Unknown')}")
                    print(f"      合作等級: {store.get('partner_level', 0)} ({partner_status})")
                    print(f"      GPS: {store.get('gps_lat', 'N/A')}, {store.get('gps_lng', 'N/A')}")
                    print(f"      Place ID: {store.get('place_id', 'N/A')}")
                    print("   " + "-" * 50)
            else:
                print("❌ API 回應格式錯誤")
                print(f"   回應內容: {stores_data}")
        else:
            print(f"❌ 店家 API 失敗: {response.status_code}")
            print(f"   回應內容: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 店家 API 錯誤: {e}")
        return False
    
    return True

def check_menu_api():
    """檢查菜單 API"""
    cloud_run_url = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"
    
    try:
        print("\n🍽️ 檢查菜單 API...")
        
        # 檢查第一個店家的菜單
        response = requests.get(f"{cloud_run_url}/api/stores", timeout=10)
        if response.status_code == 200:
            stores_data = response.json()
            if stores_data.get('success') and stores_data.get('stores'):
                first_store = stores_data['stores'][0]
                store_id = first_store.get('store_id')
                
                print(f"   檢查店家 ID {store_id} 的菜單...")
                
                # 檢查菜單 API
                menu_response = requests.get(f"{cloud_run_url}/api/menu/{store_id}", timeout=10)
                if menu_response.status_code == 200:
                    menu_data = menu_response.json()
                    if menu_data.get('success'):
                        menu = menu_data.get('menu', {})
                        items = menu.get('items', [])
                        print(f"   ✅ 菜單 API 正常")
                        print(f"      菜單 ID: {menu.get('menu_id', 'N/A')}")
                        print(f"      店家 ID: {menu.get('store_id', 'N/A')}")
                        print(f"      版本: {menu.get('version', 'N/A')}")
                        print(f"      菜單項目數: {len(items)}")
                        
                        if items:
                            print("      前3個菜單項目:")
                            for i, item in enumerate(items[:3]):
                                print(f"        {i+1}. {item.get('item_name', 'Unknown')} - ${item.get('price_small', 0)}")
                    else:
                        print(f"   ❌ 菜單 API 回應格式錯誤")
                        print(f"      回應內容: {menu_data}")
                elif menu_response.status_code == 404:
                    print(f"   ⚠️  店家 {store_id} 沒有菜單資料")
                else:
                    print(f"   ❌ 菜單 API 失敗: {menu_response.status_code}")
                    print(f"      回應內容: {menu_response.text}")
            else:
                print("   ❌ 無法取得店家資料來測試菜單 API")
        else:
            print("   ❌ 店家 API 失敗，無法測試菜單 API")
            
    except Exception as e:
        print(f"   ❌ 菜單 API 錯誤: {e}")

def check_order_api():
    """檢查訂單 API"""
    cloud_run_url = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"
    
    try:
        print("\n📝 檢查訂單 API...")
        
        # 測試簡化訂單 API
        test_order_data = {
            "line_user_id": "test_user_123",
            "items": [
                {
                    "name": {
                        "original": "測試餐點",
                        "translated": "Test Dish"
                    },
                    "quantity": 1,
                    "price": 100
                }
            ],
            "lang": "zh-TW"
        }
        
        print("   測試簡化訂單 API...")
        response = requests.post(
            f"{cloud_run_url}/api/orders/simple",
            json=test_order_data,
            timeout=15
        )
        
        if response.status_code == 201:
            order_data = response.json()
            if order_data.get('success'):
                print("   ✅ 訂單 API 正常")
                print(f"      訂單 ID: {order_data.get('order_id', 'N/A')}")
                print(f"      總金額: {order_data.get('total_amount', 'N/A')}")
                print(f"      項目數: {order_data.get('items_count', 'N/A')}")
                print(f"      中文摘要: {order_data.get('zh_summary', 'N/A')}")
                print(f"      使用者摘要: {order_data.get('user_summary', 'N/A')}")
            else:
                print("   ❌ 訂單 API 回應格式錯誤")
                print(f"      回應內容: {order_data}")
        else:
            print(f"   ❌ 訂單 API 失敗: {response.status_code}")
            print(f"      回應內容: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 訂單 API 錯誤: {e}")

def check_partner_store_logic():
    """檢查合作店家邏輯"""
    cloud_run_url = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"
    
    try:
        print("\n🔍 檢查合作店家邏輯...")
        
        # 取得所有店家
        response = requests.get(f"{cloud_run_url}/api/stores", timeout=10)
        if response.status_code == 200:
            stores_data = response.json()
            if stores_data.get('success'):
                stores = stores_data.get('stores', [])
                
                # 分析合作店家
                partner_stores = [s for s in stores if s.get('partner_level', 0) > 0]
                non_partner_stores = [s for s in stores if s.get('partner_level', 0) == 0]
                
                print(f"   總店家數: {len(stores)}")
                print(f"   合作店家: {len(partner_stores)} 家")
                print(f"   非合作店家: {len(non_partner_stores)} 家")
                
                if partner_stores:
                    print("\n   📋 合作店家列表:")
                    for store in partner_stores:
                        partner_status = "合作店家" if store.get('partner_level', 0) == 1 else \
                                       "VIP店家" if store.get('partner_level', 0) == 2 else "未知"
                        print(f"     - {store.get('store_name', 'Unknown')} (ID: {store.get('store_id')}, 等級: {store.get('partner_level')} - {partner_status})")
                
                if non_partner_stores:
                    print("\n   📋 非合作店家列表:")
                    for store in non_partner_stores[:5]:  # 只顯示前5個
                        print(f"     - {store.get('store_name', 'Unknown')} (ID: {store.get('store_id')}, 等級: {store.get('partner_level')})")
                    if len(non_partner_stores) > 5:
                        print(f"     ... 還有 {len(non_partner_stores) - 5} 個非合作店家")
                
                # 檢查是否有合作店家的菜單
                print("\n   🍽️ 檢查合作店家菜單...")
                for store in partner_stores[:3]:  # 檢查前3個合作店家
                    store_id = store.get('store_id')
                    menu_response = requests.get(f"{cloud_run_url}/api/menu/{store_id}", timeout=10)
                    
                    if menu_response.status_code == 200:
                        menu_data = menu_response.json()
                        if menu_data.get('success'):
                            menu = menu_data.get('menu', {})
                            items = menu.get('items', [])
                            print(f"     ✅ {store.get('store_name')}: 有菜單，{len(items)} 個項目")
                        else:
                            print(f"     ⚠️  {store.get('store_name')}: 菜單 API 回應錯誤")
                    elif menu_response.status_code == 404:
                        print(f"     ❌ {store.get('store_name')}: 沒有菜單資料")
                    else:
                        print(f"     ❌ {store.get('store_name')}: 菜單 API 失敗 ({menu_response.status_code})")
            else:
                print("   ❌ 無法取得店家資料")
        else:
            print("   ❌ 店家 API 失敗")
            
    except Exception as e:
        print(f"   ❌ 檢查合作店家邏輯錯誤: {e}")

def main():
    """主函數"""
    print("🚀 開始檢查合作店家資料...")
    print("=" * 50)
    
    # 1. 檢查 API 端點
    api_ok = check_api_endpoint()
    
    # 2. 檢查菜單 API
    check_menu_api()
    
    # 3. 檢查訂單 API
    check_order_api()
    
    # 4. 檢查合作店家邏輯
    check_partner_store_logic()
    
    print("\n" + "=" * 50)
    print("📋 檢查總結:")
    
    if api_ok:
        print("✅ API 端點: 正常")
    else:
        print("❌ API 端點: 失敗")
    
    print("\n💡 建議:")
    print("1. 檢查 LIFF 前端程式碼中的店家判斷邏輯")
    print("2. 確認前端是否正確讀取 partner_level 欄位")
    print("3. 檢查前端是否有快取問題")
    print("4. 確認 LIFF 網頁的店家選擇流程")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
