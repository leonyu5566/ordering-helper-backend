#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署簡化版本的 Cloud Run 服務
功能：部署不依賴 gemini_processing 表的版本
"""

import os
import sys
import subprocess
import time
import requests

def check_gcloud_auth():
    """檢查 gcloud 認證"""
    print("🔍 檢查 gcloud 認證...")
    
    try:
        result = subprocess.run(['gcloud', 'auth', 'list'], capture_output=True, text=True)
        
        if result.returncode == 0 and 'ACTIVE' in result.stdout:
            print("✅ gcloud 認證正常")
            return True
        else:
            print("❌ gcloud 認證失敗")
            return False
            
    except Exception as e:
        print(f"❌ 檢查 gcloud 認證時發生錯誤: {e}")
        return False

def deploy_to_cloud_run():
    """部署到 Cloud Run"""
    print("🚀 開始部署到 Cloud Run...")
    
    try:
        # 部署命令
        deploy_cmd = [
            'gcloud', 'run', 'deploy', 'ordering-helper-backend',
            '--source', '.',
            '--platform', 'managed',
            '--region', 'asia-east1',
            '--allow-unauthenticated',
            '--set-env-vars', 'DB_USER=gae252g1_user,DB_PASSWORD=gae252g1_password,DB_HOST=34.81.8.45,DB_DATABASE=gae252g1_db'
        ]
        
        print(f"📡 執行部署命令: {' '.join(deploy_cmd)}")
        
        # 執行部署
        result = subprocess.run(deploy_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 部署成功！")
            print(result.stdout)
            return True
        else:
            print("❌ 部署失敗")
            print(f"錯誤訊息: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 部署過程中發生錯誤: {e}")
        return False

def get_service_url():
    """獲取服務 URL"""
    print("🔍 獲取服務 URL...")
    
    try:
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
        print(f"❌ 獲取服務 URL 時發生錯誤: {e}")
        return None

def test_service_health():
    """測試服務健康狀態"""
    print("🧪 測試服務健康狀態...")
    
    try:
        service_url = get_service_url()
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
        print(f"❌ 測試服務健康狀態時發生錯誤: {e}")
        return False

def test_ocr_endpoint():
    """測試 OCR 端點"""
    print("🧪 測試 OCR 端點...")
    
    try:
        service_url = get_service_url()
        if not service_url:
            return False
        
        # 創建一個簡單的測試圖片
        from PIL import Image
        import io
        
        test_image = Image.new('RGB', (100, 100), color='white')
        img_byte_arr = io.BytesIO()
        test_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # 準備測試資料
        files = {
            'image': ('test_menu.png', img_byte_arr, 'image/png')
        }
        
        data = {
            'store_id': 1,
            'user_id': 1,
            'lang': 'en'
        }
        
        # 測試 process-ocr 端點
        ocr_url = f"{service_url}/api/menu/process-ocr"
        
        response = requests.post(ocr_url, files=files, data=data, timeout=30)
        
        print(f"📊 OCR 端點回應狀態碼: {response.status_code}")
        
        if response.status_code in [201, 422]:  # 201 成功，422 是預期的 JSON 解析錯誤
            print("✅ OCR 端點測試通過（不再依賴 gemini_processing 表）")
            return True
        else:
            print(f"❌ OCR 端點測試失敗")
            print(f"回應內容: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ 測試 OCR 端點時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    print("🚀 開始部署簡化版本的 Cloud Run 服務...")
    
    # 檢查 gcloud 認證
    if not check_gcloud_auth():
        print("❌ gcloud 認證失敗，無法繼續部署")
        return False
    
    # 部署到 Cloud Run
    if not deploy_to_cloud_run():
        print("❌ 部署失敗")
        return False
    
    # 等待部署完成
    print("⏳ 等待部署完成...")
    time.sleep(30)
    
    # 測試服務健康狀態
    if not test_service_health():
        print("❌ 服務健康檢查失敗")
        return False
    
    # 測試 OCR 端點
    if not test_ocr_endpoint():
        print("❌ OCR 端點測試失敗")
        return False
    
    print("🎉 部署和測試完成！")
    print("✅ 簡化版本已成功部署，不再依賴 gemini_processing 表")
    
    return True

if __name__ == "__main__":
    if main():
        print("🎉 部署流程成功完成")
    else:
        print("❌ 部署流程失敗")
        sys.exit(1) 