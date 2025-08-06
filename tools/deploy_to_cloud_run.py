#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud Run 部署腳本
功能：部署到 Cloud Run 並初始化 MySQL 資料庫
"""

import os
import sys
import subprocess
import time

def check_environment():
    """檢查部署環境"""
    print("🔍 檢查部署環境...")
    
    # 檢查必要的環境變數
    required_env_vars = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_DATABASE']
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少環境變數: {missing_vars}")
        print("請設定以下環境變數：")
        for var in missing_vars:
            print(f"  {var}=your_value")
        return False
    
    print("✅ 環境變數檢查通過")
    return True

def build_and_deploy():
    """構建並部署到 Cloud Run"""
    print("🚀 開始部署到 Cloud Run...")
    
    try:
        # 設定環境變數
        env_vars = [
            f"DB_USER={os.getenv('DB_USER')}",
            f"DB_PASSWORD={os.getenv('DB_PASSWORD')}",
            f"DB_HOST={os.getenv('DB_HOST')}",
            f"DB_DATABASE={os.getenv('DB_DATABASE')}"
        ]
        
        # 可選的環境變數
        optional_vars = [
            'GEMINI_API_KEY',
            'LINE_CHANNEL_ACCESS_TOKEN',
            'LINE_CHANNEL_SECRET',
            'AZURE_SPEECH_KEY',
            'AZURE_SPEECH_REGION'
        ]
        
        for var in optional_vars:
            if os.getenv(var):
                env_vars.append(f"{var}={os.getenv(var)}")
        
        env_vars_str = ','.join(env_vars)
        
        # 部署命令
        deploy_cmd = [
            'gcloud', 'run', 'deploy', 'ordering-helper-backend',
            '--source', '.',
            '--platform', 'managed',
            '--region', 'asia-east1',
            '--allow-unauthenticated',
            '--set-env-vars', env_vars_str
        ]
        
        print(f"執行部署命令: {' '.join(deploy_cmd)}")
        
        # 執行部署
        result = subprocess.run(deploy_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 部署成功！")
            print(result.stdout)
            return True
        else:
            print("❌ 部署失敗！")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 部署過程中發生錯誤: {e}")
        return False

def test_deployment():
    """測試部署"""
    print("🔍 測試部署...")
    
    try:
        # 獲取服務 URL
        result = subprocess.run([
            'gcloud', 'run', 'services', 'describe', 'ordering-helper-backend',
            '--region', 'asia-east1',
            '--format', 'value(status.url)'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            service_url = result.stdout.strip()
            print(f"✅ 服務 URL: {service_url}")
            
            # 測試健康檢查端點
            import requests
            try:
                response = requests.get(f"{service_url}/api/health", timeout=10)
                if response.status_code == 200:
                    print("✅ 健康檢查通過")
                    return True
                else:
                    print(f"❌ 健康檢查失敗: {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ 健康檢查請求失敗: {e}")
                return False
        else:
            print("❌ 無法獲取服務 URL")
            return False
            
    except Exception as e:
        print(f"❌ 測試部署時發生錯誤: {e}")
        return False

def init_database():
    """初始化資料庫"""
    print("🔍 初始化 MySQL 資料庫...")
    
    try:
        # 運行資料庫初始化腳本
        result = subprocess.run([
            'python3', 'tools/init_mysql_database.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 資料庫初始化成功！")
            print(result.stdout)
            return True
        else:
            print("❌ 資料庫初始化失敗！")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 資料庫初始化時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    print("🚀 開始 Cloud Run 部署流程...")
    
    # 檢查環境
    if not check_environment():
        print("❌ 環境檢查失敗")
        sys.exit(1)
    
    # 部署到 Cloud Run
    if not build_and_deploy():
        print("❌ 部署失敗")
        sys.exit(1)
    
    # 等待服務啟動
    print("⏳ 等待服務啟動...")
    time.sleep(30)
    
    # 測試部署
    if not test_deployment():
        print("❌ 部署測試失敗")
        sys.exit(1)
    
    # 初始化資料庫
    if not init_database():
        print("❌ 資料庫初始化失敗")
        sys.exit(1)
    
    print("🎉 Cloud Run 部署完成！")
    print("\n📋 部署摘要：")
    print("✅ 環境檢查通過")
    print("✅ 部署到 Cloud Run 成功")
    print("✅ 服務測試通過")
    print("✅ 資料庫初始化完成")
    print("\n🔗 服務 URL 可在 Cloud Console 中查看")

if __name__ == "__main__":
    main() 