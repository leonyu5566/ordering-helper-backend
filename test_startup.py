#!/usr/bin/env python3
"""
測試 Flask 應用程式啟動
用於驗證 Cloud Run 部署前的本地測試
"""

import os
import sys
import time
import requests
from threading import Thread

def test_app_startup():
    """測試應用程式啟動"""
    print("=== 測試 Flask 應用程式啟動 ===")
    
    # 設定環境變數
    os.environ['PORT'] = '8080'
    
    try:
        # 導入應用程式
        from run import app
        
        # 在背景線程中啟動應用程式
        def run_app():
            app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
        
        server_thread = Thread(target=run_app, daemon=True)
        server_thread.start()
        
        # 等待應用程式啟動
        print("等待應用程式啟動...")
        time.sleep(5)
        
        # 測試健康檢查端點
        try:
            response = requests.get('http://localhost:8080/health', timeout=10)
            if response.status_code == 200:
                print("✓ 健康檢查端點正常")
                print(f"回應: {response.json()}")
            else:
                print(f"✗ 健康檢查端點異常: {response.status_code}")
        except Exception as e:
            print(f"✗ 健康檢查端點測試失敗: {e}")
        
        # 測試根路徑
        try:
            response = requests.get('http://localhost:8080/', timeout=10)
            if response.status_code == 200:
                print("✓ 根路徑正常")
            else:
                print(f"✗ 根路徑異常: {response.status_code}")
        except Exception as e:
            print(f"✗ 根路徑測試失敗: {e}")
        
        # 測試 API 端點
        try:
            response = requests.get('http://localhost:8080/api/test', timeout=10)
            if response.status_code == 200:
                print("✓ API 測試端點正常")
            else:
                print(f"✗ API 測試端點異常: {response.status_code}")
        except Exception as e:
            print(f"✗ API 測試端點測試失敗: {e}")
        
        print("=== 測試完成 ===")
        
    except Exception as e:
        print(f"✗ 應用程式啟動失敗: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = test_app_startup()
    sys.exit(0 if success else 1)
