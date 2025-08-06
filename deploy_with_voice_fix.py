#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語音修復部署腳本
重新部署修復後的應用程式到 Cloud Run
"""

import os
import subprocess
import sys

def run_command(command, description):
    """執行命令並顯示結果"""
    print(f"\n🔧 {description}...")
    print(f"執行命令: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            if result.stdout:
                print(f"輸出: {result.stdout}")
        else:
            print(f"❌ {description} 失敗")
            print(f"錯誤: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 執行命令失敗: {e}")
        return False
    
    return True

def check_environment():
    """檢查環境設定"""
    print("🔍 檢查環境設定...")
    
    # 檢查必要的環境變數
    required_vars = [
        'AZURE_SPEECH_KEY',
        'AZURE_SPEECH_REGION',
        'LINE_CHANNEL_ACCESS_TOKEN',
        'LINE_CHANNEL_SECRET',
        'GEMINI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少環境變數: {', '.join(missing_vars)}")
        print("請確保在 Cloud Run 環境中設定了這些變數")
        return False
    
    print("✅ 環境變數檢查完成")
    return True

def build_and_deploy():
    """構建並部署應用程式"""
    print("\n🚀 開始構建和部署...")
    
    # 1. 檢查 gcloud 是否已登入
    if not run_command("gcloud auth list --filter=status:ACTIVE --format='value(account)'", "檢查 gcloud 登入狀態"):
        print("❌ 請先執行: gcloud auth login")
        return False
    
    # 2. 設定專案
    project_id = "ordering-helper-backend-1095766716155"
    if not run_command(f"gcloud config set project {project_id}", f"設定專案為 {project_id}"):
        return False
    
    # 3. 啟用必要的 API
    apis = [
        "run.googleapis.com",
        "cloudbuild.googleapis.com",
        "containerregistry.googleapis.com"
    ]
    
    for api in apis:
        if not run_command(f"gcloud services enable {api}", f"啟用 {api}"):
            return False
    
    # 4. 構建並部署到 Cloud Run
    service_name = "ordering-helper-backend"
    region = "asia-east1"
    
    deploy_command = f"""
    gcloud run deploy {service_name} \
        --source . \
        --region {region} \
        --platform managed \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --timeout 300 \
        --concurrency 80 \
        --max-instances 10 \
        --set-env-vars="AZURE_SPEECH_KEY={os.getenv('AZURE_SPEECH_KEY')}" \
        --set-env-vars="AZURE_SPEECH_REGION={os.getenv('AZURE_SPEECH_REGION')}" \
        --set-env-vars="LINE_CHANNEL_ACCESS_TOKEN={os.getenv('LINE_CHANNEL_ACCESS_TOKEN')}" \
        --set-env-vars="LINE_CHANNEL_SECRET={os.getenv('LINE_CHANNEL_SECRET')}" \
        --set-env-vars="GEMINI_API_KEY={os.getenv('GEMINI_API_KEY')}" \
        --set-env-vars="BASE_URL=https://{service_name}-{project_id}.{region}.run.app"
    """
    
    if not run_command(deploy_command, "部署到 Cloud Run"):
        return False
    
    print("\n🎉 部署完成！")
    print(f"服務 URL: https://{service_name}-{project_id}.{region}.run.app")
    
    return True

def test_deployment():
    """測試部署結果"""
    print("\n🧪 測試部署結果...")
    
    # 測試健康檢查端點
    service_url = "https://ordering-helper-backend-ordering-helper-backend-1095766716155.asia-east1.run.app"
    
    test_endpoints = [
        "/api/health",
        "/api/test",
        "/"
    ]
    
    import requests
    
    for endpoint in test_endpoints:
        try:
            response = requests.get(f"{service_url}{endpoint}", timeout=10)
            print(f"✅ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def main():
    """主函數"""
    print("🚀 語音修復部署腳本")
    print("=" * 50)
    
    # 檢查環境
    if not check_environment():
        return
    
    # 構建並部署
    if build_and_deploy():
        # 測試部署
        test_deployment()
        
        print("\n📋 部署後檢查清單:")
        print("1. 檢查 Cloud Run 應用程式日誌")
        print("2. 測試語音檔生成功能")
        print("3. 驗證 LINE Bot 語音回傳")
        print("4. 確認語音控制按鈕功能")
        
        print("\n🔍 如何檢查日誌:")
        print("gcloud logs read --service=ordering-helper-backend --limit=50")
        
    else:
        print("\n❌ 部署失敗，請檢查錯誤訊息")

if __name__ == "__main__":
    main() 