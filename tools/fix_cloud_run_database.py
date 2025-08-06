#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復 Cloud Run 數據庫問題
功能：遠程修復 Cloud Run 上的數據庫表結構
"""

import os
import sys
import subprocess
import time
import requests
import json

def check_cloud_run_status():
    """檢查 Cloud Run 服務狀態"""
    print("🔍 檢查 Cloud Run 服務狀態...")
    
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
            return service_url
        else:
            print("❌ 無法獲取服務 URL")
            return None
            
    except Exception as e:
        print(f"❌ 檢查服務狀態時發生錯誤: {e}")
        return None

def trigger_database_fix():
    """觸發數據庫修復"""
    print("🔧 觸發數據庫修復...")
    
    try:
        # 獲取服務 URL
        service_url = check_cloud_run_status()
        if not service_url:
            return False
        
        # 創建一個簡單的修復端點調用
        fix_url = f"{service_url}/api/fix-database"
        
        print(f"📡 發送修復請求到: {fix_url}")
        
        # 發送請求
        response = requests.post(fix_url, timeout=30)
        
        if response.status_code == 200:
            print("✅ 數據庫修復請求成功")
            return True
        else:
            print(f"❌ 修復請求失敗，狀態碼: {response.status_code}")
            print(f"回應內容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 觸發修復時發生錯誤: {e}")
        return False

def test_service():
    """測試服務是否正常"""
    print("🧪 測試服務...")
    
    try:
        service_url = check_cloud_run_status()
        if not service_url:
            return False
        
        # 測試健康檢查端點
        health_url = f"{service_url}/api/health"
        
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ 服務健康檢查通過")
            return True
        else:
            print(f"❌ 健康檢查失敗，狀態碼: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 測試服務時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    print("🚀 開始修復 Cloud Run 數據庫問題...")
    
    # 檢查服務狀態
    if not check_cloud_run_status():
        print("❌ 無法連接到 Cloud Run 服務")
        return False
    
    # 測試服務
    if not test_service():
        print("❌ 服務測試失敗")
        return False
    
    # 觸發數據庫修復
    if trigger_database_fix():
        print("✅ 數據庫修復完成")
        
        # 等待一段時間讓修復生效
        print("⏳ 等待修復生效...")
        time.sleep(10)
        
        # 再次測試服務
        if test_service():
            print("🎉 修復成功！服務已恢復正常")
            return True
        else:
            print("⚠️  修復可能未完全生效，請檢查日誌")
            return False
    else:
        print("❌ 數據庫修復失敗")
        return False

if __name__ == "__main__":
    if main():
        print("🎉 修復流程完成")
    else:
        print("❌ 修復流程失敗")
        sys.exit(1) 