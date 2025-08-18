#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試菜單翻譯修正
"""

import requests
import json

def test_menu_translation():
    """測試菜單翻譯功能"""
    
    # 設定環境變數
    import os
    os.environ['DB_HOST'] = '35.221.209.220'
    os.environ['DB_USER'] = 'gae252g1usr'
    os.environ['DB_PASSWORD'] = 'gae252g1PSWD!'
    os.environ['DB_DATABASE'] = 'gae252g1_db'
    os.environ['DB_PORT'] = '3306'
    
    print("🧪 測試菜單翻譯修正")
    print("=" * 60)
    
    # 測試店家 ID 4（食肆鍋）
    store_id = 4
    print(f"\n📋 測試店家 ID {store_id} 的菜單翻譯")
    print("-" * 40)
    
    try:
        # 啟動 Flask 應用程式（在背景執行）
        import subprocess
        import time
        
        print("🔄 啟動 Flask 應用程式...")
        process = subprocess.Popen(['python3', 'run.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # 等待應用程式啟動
        time.sleep(5)
        
        # 測試菜單 API 端點（中文）
        api_url_zh = f"http://localhost:8080/api/menu/{store_id}?lang=zh"
        print(f"🌐 測試中文菜單 API: {api_url_zh}")
        
        response_zh = requests.get(api_url_zh, timeout=10)
        
        if response_zh.status_code == 200:
            data_zh = response_zh.json()
            print("✅ 中文菜單 API 呼叫成功！")
            print(f"📊 回應資料摘要:")
            print(f"  - 店家 ID: {data_zh.get('store_id')}")
            print(f"  - 使用者語言: {data_zh.get('user_language')}")
            print(f"  - 菜單項目數量: {len(data_zh.get('menu_items', []))}")
            print(f"  - 翻譯統計: {data_zh.get('translation_stats')}")
            
            # 檢查前幾個菜單項目的格式
            menu_items_zh = data_zh.get('menu_items', [])
            if menu_items_zh:
                print(f"\n🍽️ 前 3 個中文菜單項目:")
                for i, item in enumerate(menu_items_zh[:3]):
                    print(f"  {i+1}. {item.get('item_name')} (ID: {item.get('menu_item_id')})")
                    print(f"     價格: {item.get('price_small')}")
                    print(f"     翻譯來源: {item.get('translation_source')}")
                    print()
            
        else:
            print(f"❌ 中文菜單 API 呼叫失敗: {response_zh.status_code}")
            print(f"錯誤訊息: {response_zh.text}")
        
        # 測試英文菜單 API 端點
        api_url_en = f"http://localhost:8080/api/menu/{store_id}?lang=en"
        print(f"\n🌐 測試英文菜單 API: {api_url_en}")
        
        response_en = requests.get(api_url_en, timeout=10)
        
        if response_en.status_code == 200:
            data_en = response_en.json()
            print("✅ 英文菜單 API 呼叫成功！")
            print(f"📊 回應資料摘要:")
            print(f"  - 店家 ID: {data_en.get('store_id')}")
            print(f"  - 使用者語言: {data_en.get('user_language')}")
            print(f"  - 菜單項目數量: {len(data_en.get('menu_items', []))}")
            print(f"  - 翻譯統計: {data_en.get('translation_stats')}")
            
            # 檢查前幾個菜單項目的格式
            menu_items_en = data_en.get('menu_items', [])
            if menu_items_en:
                print(f"\n🍽️ 前 3 個英文菜單項目:")
                for i, item in enumerate(menu_items_en[:3]):
                    print(f"  {i+1}. {item.get('item_name')} -> {item.get('translated_name')}")
                    print(f"     ID: {item.get('menu_item_id')}")
                    print(f"     價格: {item.get('price_small')}")
                    print(f"     翻譯來源: {item.get('translation_source')}")
                    print()
            
        else:
            print(f"❌ 英文菜單 API 呼叫失敗: {response_en.status_code}")
            print(f"錯誤訊息: {response_en.text}")
        
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

def test_direct_translation_function():
    """直接測試翻譯函數"""
    
    print("\n🔍 直接測試翻譯函數...")
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
            # 查詢食肆鍋的菜單項目
            store_id = 4
            print(f"🍽️ 查詢店家 ID {store_id} 的菜單項目...")
            
            menu_items_query = text("""
                SELECT mi.menu_item_id, mi.item_name, mi.price_small
                FROM menu_items mi
                JOIN menus m ON mi.menu_id = m.menu_id
                WHERE m.store_id = :store_id AND mi.price_small > 0
                ORDER BY mi.menu_item_id
                LIMIT 3
            """)
            menu_items_result = connection.execute(menu_items_query, {"store_id": store_id})
            menu_items = menu_items_result.fetchall()
            
            if menu_items:
                print(f"✅ 找到 {len(menu_items)} 個菜單項目:")
                for item in menu_items:
                    print(f"  - ID: {item[0]}, 名稱: {item[1]}, 價格: {item[2]}")
                
                # 檢查是否有翻譯資料
                print(f"\n🔍 檢查翻譯資料...")
                for item in menu_items:
                    translation_query = text("""
                        SELECT lang_code, description
                        FROM menu_translations
                        WHERE menu_item_id = :menu_item_id
                    """)
                    translation_result = connection.execute(translation_query, {"menu_item_id": item[0]})
                    translations = translation_result.fetchall()
                    
                    if translations:
                        print(f"  - 項目 {item[0]} ({item[1]}) 有翻譯:")
                        for trans in translations:
                            print(f"    * {trans[0]}: {trans[1]}")
                    else:
                        print(f"  - 項目 {item[0]} ({item[1]}) 沒有翻譯資料")
            else:
                print("❌ 沒有找到菜單項目")
        
        engine.dispose()
        
    except Exception as e:
        print(f"❌ 直接測試翻譯函數失敗: {str(e)}")

def main():
    """主函數"""
    print("🧪 菜單翻譯修正測試工具")
    print("=" * 60)
    
    # 直接測試翻譯函數
    test_direct_translation_function()
    
    # 測試菜單翻譯 API（需要 Flask 應用程式運行）
    # test_menu_translation()

if __name__ == "__main__":
    main()
