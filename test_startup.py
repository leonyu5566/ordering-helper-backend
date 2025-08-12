#!/usr/bin/env python3
"""
啟動測試腳本
用於驗證 Flask 應用程式是否能正常啟動
"""

import os
import sys
import time
import threading
import requests
from contextlib import contextmanager

def test_app_startup():
    """測試應用程式啟動"""
    print("=== 測試 Flask 應用程式啟動 ===")
    
    # 設定環境變數
    os.environ['PORT'] = '8080'
    os.environ['FLASK_ENV'] = 'production'
    
    # 移除可能導致問題的環境變數
    for var in ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_DATABASE']:
        if var in os.environ:
            del os.environ[var]
    
    try:
        # 導入應用程式
        from app import create_app
        
        # 創建應用程式
        print("創建 Flask 應用程式...")
        app = create_app()
        print("✓ Flask 應用程式創建成功")
        
        # 測試基本路由
        print("測試基本路由...")
        with app.test_client() as client:
            # 測試健康檢查端點
            response = client.get('/health')
            if response.status_code == 200:
                print("✓ 健康檢查端點正常")
            else:
                print(f"✗ 健康檢查端點異常: {response.status_code}")
                return False
            
            # 測試 API 測試端點
            response = client.get('/api/test')
            if response.status_code == 200:
                print("✓ API 測試端點正常")
            else:
                print(f"✗ API 測試端點異常: {response.status_code}")
                return False
            
            # 測試根路徑
            response = client.get('/')
            if response.status_code == 200:
                print("✓ 根路徑正常")
            else:
                print(f"✗ 根路徑異常: {response.status_code}")
                return False
        
        print("✓ 所有路由測試通過")
        return True
        
    except Exception as e:
        print(f"✗ 應用程式啟動失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gunicorn_startup():
    """測試 Gunicorn 啟動"""
    print("\n=== 測試 Gunicorn 啟動 ===")
    
    try:
        import gunicorn
        print(f"✓ Gunicorn 版本: {gunicorn.__version__}")
        
        # 測試 gunicorn 配置
        from gunicorn.app.wsgiapp import WSGIApplication
        
        print("✓ Gunicorn 導入成功")
        return True
        
    except Exception as e:
        print(f"✗ Gunicorn 測試失敗: {e}")
        return False

def test_dependencies():
    """測試依賴套件"""
    print("\n=== 測試依賴套件 ===")
    
    required_packages = [
        'flask',
        'flask_sqlalchemy', 
        'flask_cors',
        'gunicorn',
        'pymysql',
        'requests'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} 可用")
        except ImportError as e:
            print(f"✗ {package} 不可用: {e}")
            return False
    
    return True

def main():
    """主函數"""
    print("Flask 應用程式啟動測試")
    print("=" * 50)
    
    # 測試依賴套件
    if not test_dependencies():
        print("❌ 依賴套件測試失敗")
        return 1
    
    # 測試 Gunicorn
    if not test_gunicorn_startup():
        print("❌ Gunicorn 測試失敗")
        return 1
    
    # 測試應用程式啟動
    if not test_app_startup():
        print("❌ 應用程式啟動測試失敗")
        return 1
    
    print("\n" + "=" * 50)
    print("✅ 所有測試通過！應用程式應該能夠正常啟動")
    return 0

if __name__ == '__main__':
    sys.exit(main())
