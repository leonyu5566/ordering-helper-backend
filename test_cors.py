#!/usr/bin/env python3
"""
CORS 測試腳本
用於測試後端 API 的 CORS 設定是否正常工作
"""

import requests
import json

def test_cors():
    """測試 CORS 設定"""
    base_url = "http://localhost:5001"  # 本地開發伺服器
    
    # 測試端點列表
    endpoints = [
        "/api/test",
        "/api/health", 
        "/api/stores",
        "/api/upload-menu-image"
    ]
    
    print("🔍 開始測試 CORS 設定...")
    print("=" * 50)
    
    for endpoint in endpoints:
        print(f"\n📡 測試端點: {endpoint}")
        
        # 測試 OPTIONS 預檢請求
        try:
            options_response = requests.options(f"{base_url}{endpoint}")
            print(f"  OPTIONS 狀態碼: {options_response.status_code}")
            print(f"  CORS Headers:")
            for header, value in options_response.headers.items():
                if 'access-control' in header.lower():
                    print(f"    {header}: {value}")
        except Exception as e:
            print(f"  ❌ OPTIONS 請求失敗: {e}")
        
        # 測試實際請求
        try:
            if endpoint == "/api/upload-menu-image":
                # 對於 POST 端點，只測試 OPTIONS
                continue
            else:
                response = requests.get(f"{base_url}{endpoint}")
                print(f"  GET 狀態碼: {response.status_code}")
                print(f"  CORS Headers:")
                for header, value in response.headers.items():
                    if 'access-control' in header.lower():
                        print(f"    {header}: {value}")
        except Exception as e:
            print(f"  ❌ GET 請求失敗: {e}")
    
    print("\n" + "=" * 50)
    print("✅ CORS 測試完成")

if __name__ == "__main__":
    test_cors() 