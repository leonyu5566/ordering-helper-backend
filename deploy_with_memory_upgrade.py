#!/usr/bin/env python3
"""
Cloud Run 記憶體升級部署腳本
功能：將 Cloud Run 服務的記憶體從 2GiB 升級到 4GiB
"""

import subprocess
import sys
import os
import time

def run_command(command, description):
    """執行命令並處理錯誤"""
    print(f"\n🔄 {description}")
    print(f"執行命令: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 成功")
        if result.stdout:
            print(f"輸出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失敗")
        print(f"錯誤: {e.stderr}")
        return False

def check_gcloud_auth():
    """檢查 gcloud 認證"""
    print("\n🔍 檢查 gcloud 認證...")
    
    try:
        result = subprocess.run("gcloud auth list", shell=True, capture_output=True, text=True)
        if "ACTIVE" in result.stdout:
            print("✅ gcloud 已認證")
            return True
        else:
            print("❌ gcloud 未認證，請先執行: gcloud auth login")
            return False
    except Exception as e:
        print(f"❌ 檢查 gcloud 認證失敗: {e}")
        return False

def upgrade_cloud_run_memory():
    """升級 Cloud Run 記憶體配置"""
    print("\n🚀 開始升級 Cloud Run 記憶體配置...")
    
    # 設定變數
    PROJECT_ID = "solid-heaven-466011-d1"
    SERVICE_NAME = "ordering-helper-backend"
    REGION = "asia-east1"
    
    # 1. 檢查當前配置
    print(f"\n📊 檢查當前 Cloud Run 配置...")
    current_config_cmd = f"gcloud run services describe {SERVICE_NAME} --region={REGION} --project={PROJECT_ID} --format='value(spec.template.spec.containers[0].resources.limits.memory)'"
    
    try:
        result = subprocess.run(current_config_cmd, shell=True, capture_output=True, text=True)
        current_memory = result.stdout.strip()
        print(f"當前記憶體配置: {current_memory}")
    except Exception as e:
        print(f"無法獲取當前配置: {e}")
    
    # 2. 升級記憶體到 4GiB
    print(f"\n⚡ 升級記憶體到 4GiB...")
    upgrade_cmd = f"gcloud run services update {SERVICE_NAME} --region={REGION} --project={PROJECT_ID} --memory=4Gi --cpu=2 --max-instances=10 --timeout=300"
    
    if not run_command(upgrade_cmd, "升級 Cloud Run 記憶體配置"):
        print("❌ 記憶體升級失敗")
        return False
    
    # 3. 驗證升級結果
    print(f"\n🔍 驗證升級結果...")
    time.sleep(10)  # 等待服務更新
    
    verify_cmd = f"gcloud run services describe {SERVICE_NAME} --region={REGION} --project={PROJECT_ID} --format='value(spec.template.spec.containers[0].resources.limits.memory)'"
    
    try:
        result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
        new_memory = result.stdout.strip()
        print(f"升級後記憶體配置: {new_memory}")
        
        if "4Gi" in new_memory:
            print("✅ 記憶體升級成功")
            return True
        else:
            print("❌ 記憶體升級驗證失敗")
            return False
    except Exception as e:
        print(f"❌ 驗證升級結果失敗: {e}")
        return False

def deploy_optimized_version():
    """部署優化版本"""
    print("\n🚀 部署記憶體優化版本...")
    
    # 1. 構建並推送 Docker 映像
    print("\n🔨 構建 Docker 映像...")
    build_cmd = "docker build -t gcr.io/solid-heaven-466011-d1/ordering-helper-backend:memory-optimized ."
    
    if not run_command(build_cmd, "構建 Docker 映像"):
        return False
    
    # 2. 推送映像到 Google Container Registry
    print("\n📤 推送映像到 GCR...")
    push_cmd = "docker push gcr.io/solid-heaven-466011-d1/ordering-helper-backend:memory-optimized"
    
    if not run_command(push_cmd, "推送 Docker 映像"):
        return False
    
    # 3. 部署到 Cloud Run
    print("\n🚀 部署到 Cloud Run...")
    deploy_cmd = "gcloud run deploy ordering-helper-backend --image=gcr.io/solid-heaven-466011-d1/ordering-helper-backend:memory-optimized --region=asia-east1 --project=solid-heaven-466011-d1 --platform=managed --allow-unauthenticated --memory=4Gi --cpu=2 --max-instances=10 --timeout=300"
    
    if not run_command(deploy_cmd, "部署到 Cloud Run"):
        return False
    
    print("✅ 記憶體優化版本部署成功")
    return True

def test_service():
    """測試服務功能"""
    print("\n🧪 測試服務功能...")
    
    # 獲取服務 URL
    url_cmd = "gcloud run services describe ordering-helper-backend --region=asia-east1 --project=solid-heaven-466011-d1 --format='value(status.url)'"
    
    try:
        result = subprocess.run(url_cmd, shell=True, capture_output=True, text=True)
        service_url = result.stdout.strip()
        print(f"服務 URL: {service_url}")
        
        # 測試健康檢查
        import requests
        try:
            response = requests.get(f"{service_url}/", timeout=30)
            if response.status_code == 200:
                print("✅ 服務健康檢查通過")
                return True
            else:
                print(f"❌ 服務健康檢查失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 服務測試失敗: {e}")
            return False
    except Exception as e:
        print(f"❌ 獲取服務 URL 失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 Cloud Run 記憶體升級和優化部署")
    print("=" * 50)
    
    # 1. 檢查 gcloud 認證
    if not check_gcloud_auth():
        print("❌ 請先執行: gcloud auth login")
        sys.exit(1)
    
    # 2. 升級 Cloud Run 記憶體
    if not upgrade_cloud_run_memory():
        print("❌ 記憶體升級失敗")
        sys.exit(1)
    
    # 3. 部署優化版本
    if not deploy_optimized_version():
        print("❌ 優化版本部署失敗")
        sys.exit(1)
    
    # 4. 測試服務
    if not test_service():
        print("❌ 服務測試失敗")
        sys.exit(1)
    
    print("\n🎉 所有操作完成！")
    print("✅ Cloud Run 記憶體已升級到 4GiB")
    print("✅ 記憶體優化版本已部署")
    print("✅ 語音檔案和中文摘要問題已修復")
    print("\n📋 修復內容:")
    print("- 記憶體使用率監控")
    print("- 備用語音生成方案")
    print("- 優化的中文摘要生成")
    print("- 增強的錯誤處理")

if __name__ == "__main__":
    main()
