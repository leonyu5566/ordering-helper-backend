#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試國際化端點的腳本
"""

import requests
import json

# 測試配置
BASE_URL = "http://localhost:8080"  # 本地測試
# BASE_URL = "https://your-cloud-run-url"  # 生產環境

def test_normalize_lang():
    """測試語言碼正規化"""
    print("=== 測試語言碼正規化 ===")
    
    test_cases = [
        ("en-US", "en"),
        ("zh-Hant", "zh-tw"),
        ("zh-Hans", "zh-cn"),
        ("ja-JP", "ja"),
        ("ko-KR", "ko"),
        ("fr-FR", "fr"),
        ("de-DE", "de"),
        ("", "en"),
        ("invalid", "en")
    ]
    
    for input_lang, expected in test_cases:
        print(f"輸入: {input_lang} -> 預期: {expected}")

def test_store_resolve():
    """測試店家解析端點"""
    print("\n=== 測試店家解析端點 ===")
    
    # 測試參數
    test_cases = [
        {
            "place_id": "ChlJ0boght2rQjQRsH-_buCo3S4",
            "name": "測試店家",
            "lang": "en"
        },
        {
            "place_id": "ChlJ0boght2rQjQRsH-_buCo3S4",
            "name": "測試店家",
            "lang": "ja"
        },
        {
            "place_id": "ChlJ0boght2rQjQRsH-_buCo3S4",
            "name": "測試店家",
            "lang": "zh-Hant"
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
            else:
                print(f"錯誤: {response.text}")
                
        except Exception as e:
            print(f"請求失敗: {e}")

def test_partner_menu():
    """測試合作店家菜單端點"""
    print("\n=== 測試合作店家菜單端點 ===")
    
    # 測試參數
    test_cases = [
        {
            "store_id": "1",
            "lang": "en"
        },
        {
            "store_id": "1",
            "lang": "ja"
        },
        {
            "store_id": "999",  # 不存在的店家
            "lang": "en"
        }
    ]
    
    for case in test_cases:
        try:
            url = f"{BASE_URL}/api/partner/menu"
            params = case
            
            print(f"\n測試: {case}")
            response = requests.get(url, params=params)
            
            print(f"狀態碼: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"回應: {json.dumps(data, ensure_ascii=False, indent=2)}")
            else:
                print(f"錯誤: {response.text}")
                
        except Exception as e:
            print(f"請求失敗: {e}")

def test_check_partner_status():
    """測試合作狀態檢查端點"""
    print("\n=== 測試合作狀態檢查端點 ===")
    
    # 測試參數
    test_cases = [
        {
            "place_id": "ChlJ0boght2rQjQRsH-_buCo3S4",
            "name": "測試店家",
            "lang": "en"
        },
        {
            "place_id": "nonexistent",
            "name": "不存在的店家",
            "lang": "ja"
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
            else:
                print(f"錯誤: {response.text}")
                
        except Exception as e:
            print(f"請求失敗: {e}")

def test_translate_api():
    """測試翻譯 API"""
    print("\n=== 測試翻譯 API ===")
    
    # 測試單一文字翻譯
    try:
        url = f"{BASE_URL}/api/translate"
        params = {"target": "en"}
        data = {"text": "你好世界"}
        
        print(f"\n測試單一文字翻譯: {data}")
        response = requests.post(url, params=params, json=data)
        
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"回應: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"錯誤: {response.text}")
            
    except Exception as e:
        print(f"請求失敗: {e}")
    
    # 測試批次翻譯
    try:
        url = f"{BASE_URL}/api/translate"
        data = {
            "contents": ["你好", "世界", "測試"],
            "target": "en"
        }
        
        print(f"\n測試批次翻譯: {data}")
        response = requests.post(url, json=data)
        
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"回應: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"錯誤: {response.text}")
            
    except Exception as e:
        print(f"請求失敗: {e}")

def main():
    """主測試函數"""
    print("開始測試國際化端點...")
    
    test_normalize_lang()
    test_store_resolve()
    test_partner_menu()
    test_check_partner_status()
    test_translate_api()
    
    print("\n=== 測試完成 ===")

if __name__ == "__main__":
    main()
