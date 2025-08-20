#!/usr/bin/env python3
"""
測試應用程式啟動
"""

import os
import sys

def test_imports():
    """測試所有必要的模組是否能正常匯入"""
    print("=== 測試模組匯入 ===")
    
    try:
        print("匯入 Flask...")
        from flask import Flask
        print("✓ Flask 匯入成功")
    except Exception as e:
        print(f"✗ Flask 匯入失敗: {e}")
        return False
    
    try:
        print("匯入應用程式...")
        from app import create_app
        print("✓ 應用程式匯入成功")
    except Exception as e:
        print(f"✗ 應用程式匯入失敗: {e}")
        return False
    
    try:
        print("建立應用程式實例...")
        app = create_app()
        print("✓ 應用程式實例建立成功")
    except Exception as e:
        print(f"✗ 應用程式實例建立失敗: {e}")
        return False
    
    return True

def test_environment():
    """測試環境變數"""
    print("\n=== 測試環境變數 ===")
    
    # 設定測試環境變數
    os.environ['PORT'] = '8080'
    os.environ['DB_USER'] = 'test'
    os.environ['DB_PASSWORD'] = 'test'
    os.environ['DB_HOST'] = 'localhost'
    os.environ['DB_DATABASE'] = 'test'
    os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'test'
    os.environ['LINE_CHANNEL_SECRET'] = 'test'
    
    print("✓ 環境變數設定完成")
    return True

def test_app_creation():
    """測試應用程式建立"""
    print("\n=== 測試應用程式建立 ===")
    
    try:
        from app import create_app
        app = create_app()
        
        # 測試基本路由
        with app.test_client() as client:
            response = client.get('/health')
            print(f"✓ 健康檢查端點回應: {response.status_code}")
            
            response = client.get('/')
            print(f"✓ 根路徑回應: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"✗ 應用程式測試失敗: {e}")
        return False

def main():
    """主測試函式"""
    print("開始測試應用程式啟動...")
    
    # 測試環境變數
    if not test_environment():
        print("❌ 環境變數測試失敗")
        sys.exit(1)
    
    # 測試模組匯入
    if not test_imports():
        print("❌ 模組匯入測試失敗")
        sys.exit(1)
    
    # 測試應用程式建立
    if not test_app_creation():
        print("❌ 應用程式建立測試失敗")
        sys.exit(1)
    
    print("\n✅ 所有測試通過！應用程式應該能正常啟動。")

if __name__ == '__main__':
    main()
