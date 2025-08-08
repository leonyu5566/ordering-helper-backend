#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署 LINE 聊天室修復到 Cloud Run

功能：
1. 部署修復版本的程式碼
2. 設定必要的環境變數
3. 驗證部署是否成功
4. 提供測試指南

使用方法：
python3 deploy_line_fix.py
"""

import os
import sys
import subprocess
import time
import requests
from datetime import datetime

def check_prerequisites():
    """檢查部署前置條件"""
    print("🔍 檢查部署前置條件...")
    
    # 檢查 gcloud 是否安裝
    try:
        result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ gcloud CLI 已安裝")
        else:
            print("❌ gcloud CLI 未安裝或未配置")
            return False
    except FileNotFoundError:
        print("❌ gcloud CLI 未安裝")
        return False
    
    # 檢查專案設定
    try:
        result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True)
        project_id = result.stdout.strip()
        if project_id:
            print(f"✅ 專案 ID: {project_id}")
        else:
            print("❌ 未設定專案 ID")
            return False
    except Exception as e:
        print(f"❌ 檢查專案設定失敗: {e}")
        return False
    
    return True

def set_environment_variables():
    """設定必要的環境變數"""
    print("\n🔧 設定環境變數...")
    
    # 檢查必要的環境變數
    required_vars = [
        'LINE_CHANNEL_ACCESS_TOKEN',
        'LINE_CHANNEL_SECRET',
        'GEMINI_API_KEY',
        'AZURE_SPEECH_KEY',
        'AZURE_SPEECH_REGION'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ 缺少環境變數: {missing_vars}")
        print("請在 Cloud Run 中設定這些環境變數")
        return False
    
    print("✅ 環境變數檢查通過")
    return True

def deploy_to_cloud_run():
    """部署到 Cloud Run"""
    print("\n🚀 部署到 Cloud Run...")
    
    try:
        # 設定部署參數
        service_name = "ordering-helper-backend"
        region = "asia-east1"
        project_id = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                                  capture_output=True, text=True).stdout.strip()
        
        print(f"📋 部署資訊:")
        print(f"   服務名稱: {service_name}")
        print(f"   地區: {region}")
        print(f"   專案: {project_id}")
        
        # 執行部署
        cmd = [
            'gcloud', 'run', 'deploy', service_name,
            '--source', '.',
            '--region', region,
            '--platform', 'managed',
            '--allow-unauthenticated',
            '--memory', '4Gi',
            '--cpu', '2',
            '--max-instances', '10',
            '--timeout', '300',
            '--set-env-vars', 'FORCE_CLOUD_MYSQL=true'
        ]
        
        print("🔄 開始部署...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 部署成功！")
            
            # 提取服務 URL
            for line in result.stdout.split('\n'):
                if 'Service URL:' in line:
                    service_url = line.split('Service URL:')[1].strip()
                    print(f"🌐 服務 URL: {service_url}")
                    return service_url
        else:
            print(f"❌ 部署失敗: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 部署過程發生錯誤: {e}")
        return None

def test_deployment(service_url):
    """測試部署是否成功"""
    print(f"\n🧪 測試部署: {service_url}")
    
    try:
        # 測試健康檢查
        health_url = f"{service_url}/api/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ 健康檢查通過")
        else:
            print(f"❌ 健康檢查失敗: {response.status_code}")
            return False
        
        # 測試店家列表
        stores_url = f"{service_url}/api/stores"
        response = requests.get(stores_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ API 端點正常")
        else:
            print(f"❌ API 端點異常: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def create_test_order(service_url):
    """建立測試訂單"""
    print(f"\n📝 建立測試訂單...")
    
    try:
        # 測試訂單資料
        test_order = {
            "items": [
                {
                    "name": {
                        "original": "奶油經典夏威夷",
                        "translated": "Classic Hawaiian Cream"
                    },
                    "quantity": 1,
                    "price": 115
                },
                {
                    "name": {
                        "original": "奶香培根玉米",
                        "translated": "Bacon Corn"
                    },
                    "quantity": 1,
                    "price": 110
                }
            ],
            "lang": "en",
            "line_user_id": "U1234567890abcdef"  # 測試用 ID
        }
        
        # 發送測試訂單
        order_url = f"{service_url}/api/orders/simple"
        response = requests.post(order_url, json=test_order, timeout=30)
        
        if response.status_code == 201:
            result = response.json()
            print("✅ 測試訂單建立成功")
            print(f"   訂單 ID: {result.get('order_id')}")
            print(f"   總金額: {result.get('total_amount')}")
            print(f"   項目數量: {result.get('items_count')}")
            return True
        else:
            print(f"❌ 測試訂單建立失敗: {response.status_code}")
            print(f"   回應: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 測試訂單失敗: {e}")
        return False

def print_testing_guide(service_url):
    """印出測試指南"""
    print(f"\n📋 測試指南")
    print("=" * 50)
    
    print("1. 健康檢查:")
    print(f"   curl {service_url}/api/health")
    
    print("\n2. 店家列表:")
    print(f"   curl {service_url}/api/stores")
    
    print("\n3. 建立測試訂單:")
    print(f"   curl -X POST {service_url}/api/orders/simple \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{")
    print('       "items": [')
    print('         {')
    print('           "name": {')
    print('             "original": "奶油經典夏威夷",')
    print('             "translated": "Classic Hawaiian Cream"')
    print('           },')
    print('           "quantity": 1,')
    print('           "price": 115')
    print('         }')
    print('       ],')
    print('       "lang": "en",')
    print('       "line_user_id": "YOUR_LINE_USER_ID"')
    print('     }')
    
    print("\n4. 檢查 Cloud Run 日誌:")
    print("   gcloud logs read --service=ordering-helper-backend --limit=50")
    
    print("\n5. 驗證修復:")
    print("   - 檢查摘要是否正確顯示")
    print("   - 檢查語音檔是否生成")
    print("   - 檢查 LINE Bot 訊息是否發送")

def main():
    """主函數"""
    print("🚀 部署 LINE 聊天室修復")
    print("=" * 50)
    
    # 記錄開始時間
    start_time = datetime.now()
    
    # 檢查前置條件
    if not check_prerequisites():
        print("❌ 前置條件檢查失敗")
        return
    
    # 設定環境變數
    if not set_environment_variables():
        print("❌ 環境變數設定失敗")
        return
    
    # 部署到 Cloud Run
    service_url = deploy_to_cloud_run()
    if not service_url:
        print("❌ 部署失敗")
        return
    
    # 等待服務啟動
    print("\n⏳ 等待服務啟動...")
    time.sleep(30)
    
    # 測試部署
    if not test_deployment(service_url):
        print("❌ 部署測試失敗")
        return
    
    # 建立測試訂單
    if not create_test_order(service_url):
        print("⚠️ 測試訂單建立失敗，但部署可能仍然成功")
    
    # 印出測試指南
    print_testing_guide(service_url)
    
    # 總結
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n🎉 部署完成！")
    print(f"⏱️ 總耗時: {duration:.2f} 秒")
    print(f"🌐 服務 URL: {service_url}")
    
    print("\n📝 修復內容:")
    print("1. ✅ 摘要取值錯誤已修復")
    print("2. ✅ TTS 檔案上傳到 GCS 已實作")
    print("3. ✅ 嚴謹的訊息構建檢查")
    print("4. ✅ 完整的錯誤處理")
    
    print("\n🔍 下一步:")
    print("1. 使用真實的 LINE User ID 測試")
    print("2. 檢查 Cloud Run 日誌")
    print("3. 驗證 LINE 聊天室中的訊息")

if __name__ == "__main__":
    main()
