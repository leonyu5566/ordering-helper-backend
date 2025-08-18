#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試修正後的訂單建立功能
"""

import requests
import json

def test_order_creation_with_correct_ids():
    """測試使用正確的菜單項目 ID 建立訂單"""
    
    # 設定環境變數
    import os
    os.environ['DB_HOST'] = '35.221.209.220'
    os.environ['DB_USER'] = 'gae252g1usr'
    os.environ['DB_PASSWORD'] = 'gae252g1PSWD!'
    os.environ['DB_DATABASE'] = 'gae252g1_db'
    os.environ['DB_PORT'] = '3306'
    
    print("🧪 測試修正後的訂單建立功能")
    print("=" * 60)
    
    # 使用正確的菜單項目 ID（從資料庫查詢結果）
    order_data = {
        "store_id": 4,
        "store_name": "食肆鍋",
        "line_user_id": "test_user_123",
        "language": "zh",
        "items": [
            {
                "menu_item_id": 123,  # 白濃雞湯的正確 ID
                "quantity": 1,
                "item_name": "白濃雞湯",
                "price": 49
            },
            {
                "menu_item_id": 124,  # 14嚴選 霜降牛的正確 ID
                "quantity": 0,
                "item_name": "14嚴選 霜降牛",
                "price": 118
            }
        ]
    }
    
    print(f"\n📋 測試訂單資料（使用正確的 ID）:")
    print(f"  - 店家 ID: {order_data['store_id']}")
    print(f"  - 店家名稱: {order_data['store_name']}")
    print(f"  - 使用者 ID: {order_data['line_user_id']}")
    print(f"  - 訂單項目數量: {len(order_data['items'])}")
    print(f"  - 菜單項目 ID: {[item['menu_item_id'] for item in order_data['items']]}")
    
    try:
        # 啟動 Flask 應用程式（在背景執行）
        import subprocess
        import time
        
        print("\n🔄 啟動 Flask 應用程式...")
        process = subprocess.Popen(['python3', 'run.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # 等待應用程式啟動
        time.sleep(5)
        
        # 測試 API 端點
        api_url = "http://localhost:8080/api/orders"
        print(f"🌐 測試 API: {api_url}")
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(api_url, 
                               json=order_data, 
                               headers=headers, 
                               timeout=30)
        
        print(f"📊 回應狀態碼: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ 訂單建立成功！")
            print(f"📊 回應資料:")
            print(f"  - 訂單 ID: {data.get('order_id')}")
            print(f"  - 總金額: {data.get('total_amount')}")
            print(f"  - 語音生成: {data.get('voice_generated')}")
            
        elif response.status_code == 400:
            data = response.json()
            print("❌ 訂單資料驗證失敗:")
            print(f"  - 錯誤: {data.get('error')}")
            print(f"  - 詳細: {data.get('details')}")
            if 'validation_errors' in data:
                print(f"  - 驗證錯誤:")
                for error in data['validation_errors']:
                    print(f"    * {error}")
            if 'received_data' in data:
                print(f"  - 接收到的資料:")
                print(f"    * 店家 ID: {data['received_data'].get('store_id')}")
                print(f"    * 店家名稱: {data['received_data'].get('store_name')}")
                print(f"    * 項目數量: {data['received_data'].get('items_count')}")
            if 'debug_info' in data:
                print(f"  - 除錯資訊:")
                print(f"    * 解析後的店家 ID: {data['debug_info'].get('resolved_store_id')}")
                print(f"    * 使用者 ID: {data['debug_info'].get('user_id')}")
            
        elif response.status_code == 500:
            data = response.json()
            print("❌ 訂單建立失敗:")
            print(f"  - 錯誤: {data.get('error')}")
            print(f"  - 詳細: {data.get('details')}")
            if 'debug_info' in data:
                print(f"  - 除錯資訊:")
                print(f"    * 店家 ID: {data['debug_info'].get('store_id')}")
                print(f"    * 使用者 ID: {data['debug_info'].get('user_id')}")
                print(f"    * 項目數量: {data['debug_info'].get('items_count')}")
                print(f"    * 總金額: {data['debug_info'].get('total_amount')}")
            
        else:
            print(f"❌ 未預期的回應: {response.status_code}")
            print(f"回應內容: {response.text}")
        
        # 停止應用程式
        process.terminate()
        process.wait()
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 Flask 應用程式")
        print("請確保應用程式正在執行，或者檢查埠號設定")
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🏁 測試完成")

def test_order_creation_with_wrong_ids():
    """測試使用錯誤的菜單項目 ID 建立訂單（應該失敗）"""
    
    print("\n🧪 測試使用錯誤的菜單項目 ID")
    print("-" * 40)
    
    # 使用錯誤的菜單項目 ID（模擬前端的錯誤）
    order_data = {
        "store_id": 4,
        "store_name": "食肆鍋",
        "line_user_id": "test_user_123",
        "language": "zh",
        "items": [
            {
                "menu_item_id": 1,  # 錯誤的 ID
                "quantity": 1,
                "item_name": "白濃雞湯",
                "price": 49
            },
            {
                "menu_item_id": 2,  # 錯誤的 ID
                "quantity": 0,
                "item_name": "14嚴選 霜降牛",
                "price": 118
            }
        ]
    }
    
    print(f"📋 測試訂單資料（使用錯誤的 ID）:")
    print(f"  - 菜單項目 ID: {[item['menu_item_id'] for item in order_data['items']]}")
    print(f"  - 預期結果: 應該失敗並顯示詳細的錯誤訊息")
    
    try:
        # 啟動 Flask 應用程式（在背景執行）
        import subprocess
        import time
        
        print("\n🔄 啟動 Flask 應用程式...")
        process = subprocess.Popen(['python3', 'run.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # 等待應用程式啟動
        time.sleep(5)
        
        # 測試 API 端點
        api_url = "http://localhost:8080/api/orders"
        print(f"🌐 測試 API: {api_url}")
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(api_url, 
                               json=order_data, 
                               headers=headers, 
                               timeout=30)
        
        print(f"📊 回應狀態碼: {response.status_code}")
        
        if response.status_code == 400:
            data = response.json()
            print("✅ 如預期般失敗！")
            print(f"📊 錯誤回應:")
            print(f"  - 錯誤: {data.get('error')}")
            if 'validation_errors' in data:
                print(f"  - 驗證錯誤:")
                for error in data['validation_errors']:
                    print(f"    * {error}")
            if 'received_data' in data:
                print(f"  - 接收到的資料:")
                print(f"    * 店家 ID: {data['received_data'].get('store_id')}")
                print(f"    * 店家名稱: {data['received_data'].get('store_name')}")
                print(f"    * 項目數量: {data['received_data'].get('items_count')}")
            if 'debug_info' in data:
                print(f"  - 除錯資訊:")
                print(f"    * 解析後的店家 ID: {data['debug_info'].get('resolved_store_id')}")
                print(f"    * 使用者 ID: {data['debug_info'].get('user_id')}")
            
        else:
            print(f"❌ 未預期的回應: {response.status_code}")
            print(f"回應內容: {response.text}")
        
        # 停止應用程式
        process.terminate()
        process.wait()
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 Flask 應用程式")
        print("請確保應用程式正在執行，或者檢查埠號設定")
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {str(e)}")

def main():
    """主函數"""
    print("🧪 修正後的訂單建立測試工具")
    print("=" * 60)
    
    # 測試使用正確的 ID
    test_order_creation_with_correct_ids()
    
    # 測試使用錯誤的 ID
    test_order_creation_with_wrong_ids()

if __name__ == "__main__":
    main()
