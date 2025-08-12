#!/usr/bin/env python3
"""
部署驗證腳本
用於在部署到 Cloud Run 之前驗證應用程式是否正常運作
"""

import os
import requests
import time
import subprocess
import sys

def check_port_availability(port):
    """檢查指定端口是否可用"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result != 0

def test_local_deployment():
    """測試本地部署"""
    print("=== 測試本地部署 ===")
    
    # 檢查端口可用性
    port = int(os.environ.get('PORT', 8080))
    if not check_port_availability(port):
        print(f"❌ 端口 {port} 已被佔用")
        return False
    
    print(f"✅ 端口 {port} 可用")
    
    # 啟動應用程式
    print("啟動 Flask 應用程式...")
    try:
        # 使用 subprocess 啟動應用程式
        process = subprocess.Popen([
            sys.executable, 'run.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待應用程式啟動
        print("等待應用程式啟動...")
        time.sleep(5)
        
        # 測試健康檢查端點
        try:
            response = requests.get(f'http://localhost:{port}/health', timeout=10)
            if response.status_code == 200:
                print("✅ 健康檢查端點正常")
                print(f"回應: {response.json()}")
            else:
                print(f"❌ 健康檢查端點異常: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 無法連接到健康檢查端點: {e}")
            return False
        
        # 測試 API 端點
        try:
            response = requests.get(f'http://localhost:{port}/api/test', timeout=10)
            if response.status_code == 200:
                print("✅ API 測試端點正常")
                print(f"回應: {response.json()}")
            else:
                print(f"❌ API 測試端點異常: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 無法連接到 API 測試端點: {e}")
            return False
        
        # 測試根路徑
        try:
            response = requests.get(f'http://localhost:{port}/', timeout=10)
            if response.status_code == 200:
                print("✅ 根路徑正常")
            else:
                print(f"❌ 根路徑異常: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 無法連接到根路徑: {e}")
            return False
        
        print("✅ 所有端點測試通過")
        
        # 停止應用程式
        process.terminate()
        process.wait()
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_docker_build():
    """測試 Docker 建置"""
    print("\n=== 測試 Docker 建置 ===")
    
    try:
        # 建置 Docker 映像
        print("建置 Docker 映像...")
        result = subprocess.run([
            'docker', 'build', '-t', 'ordering-helper-backend:test', '.'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Docker 映像建置成功")
            return True
        else:
            print("❌ Docker 映像建置失敗")
            print(f"錯誤: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ Docker 未安裝或不在 PATH 中")
        return False
    except Exception as e:
        print(f"❌ Docker 建置測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("點餐小幫手後端 - 部署驗證腳本")
    print("=" * 50)
    
    # 檢查環境變數
    print("檢查環境變數...")
    required_vars = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_DATABASE']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  缺少環境變數: {missing_vars}")
        print("這些變數在 Cloud Run 中應該已經設定")
    else:
        print("✅ 所有必要環境變數都已設定")
    
    # 測試本地部署
    local_success = test_local_deployment()
    
    # 測試 Docker 建置
    docker_success = test_docker_build()
    
    print("\n" + "=" * 50)
    print("測試結果摘要:")
    print(f"本地部署: {'✅ 通過' if local_success else '❌ 失敗'}")
    print(f"Docker 建置: {'✅ 通過' if docker_success else '❌ 失敗'}")
    
    if local_success and docker_success:
        print("\n🎉 所有測試通過！可以部署到 Cloud Run")
        return 0
    else:
        print("\n⚠️  有測試失敗，請檢查問題後再部署")
        return 1

if __name__ == '__main__':
    sys.exit(main())
