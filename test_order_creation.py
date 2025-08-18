#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試訂單建立功能
"""

import requests
import json

def test_order_creation():
    """測試訂單建立 API"""
    
    # 設定環境變數
    import os
    os.environ['DB_HOST'] = '35.221.209.220'
    os.environ['DB_USER'] = 'gae252g1usr'
    os.environ['DB_PASSWORD'] = 'gae252g1PSWD!'
    os.environ['DB_DATABASE'] = 'gae252g1_db'
    os.environ['DB_PORT'] = '3306'
    
    print("🧪 測試訂單建立功能")
    print("=" * 60)
    
    # 模擬食肆鍋的訂單資料
    order_data = {
        "store_id": 4,
        "store_name": "食肆鍋",
        "line_user_id": "test_user_123",
        "language": "zh",
        "items": [
            {
                "menu_item_id": 1,  # 假設的菜單項目 ID
                "quantity": 1,
                "item_name": "白濃雞湯",
                "price": 49
            },
            {
                "menu_item_id": 2,  # 假設的菜單項目 ID
                "quantity": 0,
                "item_name": "14嚴選 霜降牛",
                "price": 118
            }
        ]
    }
    
    print(f"\n📋 測試訂單資料:")
    print(f"  - 店家 ID: {order_data['store_id']}")
    print(f"  - 店家名稱: {order_data['store_name']}")
    print(f"  - 使用者 ID: {order_data['line_user_id']}")
    print(f"  - 訂單項目數量: {len(order_data['items'])}")
    
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
            
        elif response.status_code == 500:
            data = response.json()
            print("❌ 訂單建立失敗:")
            print(f"  - 錯誤: {data.get('error')}")
            print(f"  - 詳細: {data.get('details')}")
            
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

def test_database_connection():
    """測試資料庫連線和基本查詢"""
    
    print("\n🔍 測試資料庫連線...")
    print("-" * 40)
    
    try:
        # 設定環境變數
        import os
        os.environ['DB_HOST'] = '35.221.209.220'
        os.environ['DB_USER'] = 'gae252g1usr'
        os.environ['DB_PASSWORD'] = 'gae252g1PSWD!'
        os.environ['DB_DATABASE'] = 'gae252g1_db'
        os.environ['DB_PORT'] = '3306'
        
        # 建立資料庫連線
        from sqlalchemy import create_engine, text
        
        connection_string = f"mysql+pymysql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_DATABASE']}?charset=utf8mb4"
        engine = create_engine(connection_string)
        
        with engine.connect() as connection:
            # 檢查必要的表格是否存在
            tables_to_check = ['users', 'stores', 'menus', 'menu_items', 'orders', 'order_items']
            
            for table in tables_to_check:
                try:
                    check_query = text(f"SELECT COUNT(*) FROM {table}")
                    result = connection.execute(check_query)
                    count = result.fetchone()[0]
                    print(f"✅ 表格 {table}: {count} 筆記錄")
                except Exception as e:
                    print(f"❌ 表格 {table} 查詢失敗: {str(e)}")
            
            # 檢查食肆鍋的菜單項目
            print(f"\n🍽️ 檢查食肆鍋的菜單項目...")
            menu_items_query = text("""
                SELECT mi.menu_item_id, mi.item_name, mi.price_small
                FROM menu_items mi
                JOIN menus m ON mi.menu_id = m.menu_id
                WHERE m.store_id = 4 AND mi.price_small > 0
                ORDER BY mi.menu_item_id
                LIMIT 5
            """)
            menu_items_result = connection.execute(menu_items_query)
            menu_items = menu_items_result.fetchall()
            
            if menu_items:
                print(f"✅ 找到 {len(menu_items)} 個菜單項目:")
                for item in menu_items:
                    print(f"  - ID: {item[0]}, 名稱: {item[1]}, 價格: {item[2]}")
            else:
                print("❌ 沒有找到菜單項目")
        
        engine.dispose()
        
    except Exception as e:
        print(f"❌ 資料庫連線測試失敗: {str(e)}")

def main():
    """主函數"""
    print("🧪 訂單建立測試工具")
    print("=" * 60)
    
    # 測試資料庫連線
    test_database_connection()
    
    # 測試訂單建立 API（需要 Flask 應用程式運行）
    # test_order_creation()

if __name__ == "__main__":
    main()
