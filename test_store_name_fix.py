#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試店名翻譯修正的腳本
"""

import requests
import json

# 測試配置
BASE_URL = "http://localhost:8080"  # 本地測試
# BASE_URL = "https://your-cloud-run-url"  # 生產環境

def test_check_partner_status():
    """測試店家合作狀態檢查端點"""
    print("=== 測試店家合作狀態檢查端點 ===")
    
    # 測試參數
    test_cases = [
        {
            "place_id": "ChlJ0boght2rQjQRsH-_buCo3S4",
            "name": "本家精選村",
            "lang": "en-US"
        },
        {
            "place_id": "ChlJ0boght2rQjQRsH-_buCo3S4",
            "name": "本家精選村",
            "lang": "ja-JP"
        },
        {
            "place_id": "nonexistent",
            "name": "不存在的店家",
            "lang": "en-US"
        }
    ]
    
    for case in test_cases:
        try:
            url = f"{BASE_URL}/api/stores/check-partner-status"
            params = case
            
            print(f"\n測試: {case}")
            response = requests.get(url, params=params)
            
            print(f"狀態碼: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"回應: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                # 檢查是否有翻譯欄位
                has_display_name = 'display_name' in data
                has_translated_name = 'translated_name' in data
                print(f"✅ display_name: {has_display_name}")
                print(f"✅ translated_name: {has_translated_name}")
                
                if has_display_name and data['display_name']:
                    print(f"✅ 翻譯後店名: {data['display_name']}")
                else:
                    print("❌ 缺少翻譯後店名")
                    
            else:
                print(f"錯誤: {response.text}")
                
        except Exception as e:
            print(f"請求失敗: {e}")

def test_store_resolve():
    """測試店家解析端點"""
    print("\n=== 測試店家解析端點 ===")
    
    # 測試參數
    test_cases = [
        {
            "place_id": "ChlJ0boght2rQjQRsH-_buCo3S4",
            "name": "本家精選村",
            "lang": "en-US"
        },
        {
            "place_id": "ChlJ0boght2rQjQRsH-_buCo3S4",
            "name": "本家精選村",
            "lang": "ja-JP"
        }
    ]
    
    for case in test_cases:
        try:
            url = f"{BASE_URL}/api/store/resolve"
            params = case
            
            print(f"\n測試: {case}")
            response = requests.get(url, params=params)
            
            print(f"狀態碼: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"回應: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                # 檢查是否有翻譯欄位
                has_display_name = 'display_name' in data
                has_original_name = 'original_name' in data
                print(f"✅ display_name: {has_display_name}")
                print(f"✅ original_name: {has_original_name}")
                
                if has_display_name and data['display_name']:
                    print(f"✅ 翻譯後店名: {data['display_name']}")
                else:
                    print("❌ 缺少翻譯後店名")
                    
            else:
                print(f"錯誤: {response.text}")
                
        except Exception as e:
            print(f"請求失敗: {e}")

def test_menu_endpoints():
    """測試菜單端點"""
    print("\n=== 測試菜單端點 ===")
    
    # 測試參數
    test_cases = [
        {
            "store_id": "1",
            "lang": "en-US"
        },
        {
            "store_id": "1",
            "lang": "ja-JP"
        }
    ]
    
    for case in test_cases:
        try:
            # 測試 /api/menu/<store_id>
            url = f"{BASE_URL}/api/menu/{case['store_id']}"
            params = {"lang": case['lang']}
            
            print(f"\n測試 /api/menu/{case['store_id']}: {case}")
            response = requests.get(url, params=params)
            
            print(f"狀態碼: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"回應: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                # 檢查菜單項目是否有翻譯
                if 'menu_items' in data and data['menu_items']:
                    first_item = data['menu_items'][0]
                    has_name = 'name' in first_item
                    has_original_name = 'original_name' in first_item
                    print(f"✅ 菜單項目翻譯: {has_name}")
                    print(f"✅ 原始菜名: {has_original_name}")
                    
                    if has_name and first_item['name']:
                        print(f"✅ 翻譯後菜名: {first_item['name']}")
                    else:
                        print("❌ 缺少翻譯後菜名")
                else:
                    print("⚠️ 沒有菜單項目")
                    
            else:
                print(f"錯誤: {response.text}")
                
        except Exception as e:
            print(f"請求失敗: {e}")

def test_translate_api():
    """測試翻譯 API"""
    print("\n=== 測試翻譯 API ===")
    
    try:
        url = f"{BASE_URL}/api/translate"
        params = {"target": "en"}
        data = {"text": "本家精選村"}
        
        print(f"測試翻譯: {data}")
        response = requests.post(url, params=params, json=data)
        
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"回應: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            if 'translated' in data and data['translated']:
                print(f"✅ 翻譯結果: {data['translated']}")
            else:
                print("❌ 翻譯失敗")
                
        else:
            print(f"錯誤: {response.text}")
            
    except Exception as e:
        print(f"請求失敗: {e}")

def main():
    """主測試函數"""
    print("開始測試店名翻譯修正...")
    
    test_check_partner_status()
    test_store_resolve()
    test_menu_endpoints()
    test_translate_api()
    
    print("\n=== 測試完成 ===")
    print("\n預期結果:")
    print("1. ✅ /api/stores/check-partner-status 應該回傳 display_name 和 translated_name")
    print("2. ✅ /api/store/resolve 應該回傳翻譯後的店名")
    print("3. ✅ 菜單端點應該回傳翻譯後的菜名")
    print("4. ✅ 翻譯 API 應該正常工作")

if __name__ == "__main__":
    main()
