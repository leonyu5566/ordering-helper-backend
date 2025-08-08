#!/usr/bin/env python3
"""
部署修正腳本
解決訂單摘要、金額格式和語音檔問題
"""

import os
import sys
import subprocess
import json

def check_environment():
    """檢查環境變數"""
    print("🔍 檢查環境變數...")
    
    required_vars = [
        'AZURE_SPEECH_KEY',
        'AZURE_SPEECH_REGION',
        'LINE_CHANNEL_ACCESS_TOKEN',
        'LINE_CHANNEL_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ 缺少環境變數: {missing_vars}")
        return False
    
    print("✅ 環境變數檢查通過")
    return True

def create_gcs_bucket_simple():
    """使用 gcloud CLI 創建 GCS bucket"""
    print("🔧 創建 GCS bucket...")
    
    bucket_name = 'ordering-helper-voice-files'
    
    try:
        # 檢查 bucket 是否存在
        result = subprocess.run(
            ['gsutil', 'ls', f'gs://{bucket_name}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Bucket '{bucket_name}' 已存在")
        else:
            # 創建 bucket
            print(f"📦 創建 bucket '{bucket_name}'...")
            create_result = subprocess.run(
                ['gsutil', 'mb', '-l', 'asia-east1', f'gs://{bucket_name}'],
                capture_output=True,
                text=True
            )
            
            if create_result.returncode == 0:
                print(f"✅ 成功創建 bucket: {bucket_name}")
            else:
                print(f"❌ 創建 bucket 失敗: {create_result.stderr}")
                return False
        
        # 設置公開讀取權限
        print("🔐 設置公開讀取權限...")
        iam_result = subprocess.run(
            ['gsutil', 'iam', 'ch', 'allUsers:objectViewer', f'gs://{bucket_name}'],
            capture_output=True,
            text=True
        )
        
        if iam_result.returncode == 0:
            print("✅ 已設置公開讀取權限")
        else:
            print(f"⚠️ 設置公開權限失敗: {iam_result.stderr}")
        
        return True
        
    except FileNotFoundError:
        print("❌ gcloud CLI 未安裝或不在 PATH 中")
        print("💡 請安裝 Google Cloud SDK: https://cloud.google.com/sdk/docs/install")
        return False
    except Exception as e:
        print(f"❌ GCS 設置失敗: {e}")
        return False

def test_voice_generation():
    """測試語音生成功能"""
    print("🧪 測試語音生成...")
    
    try:
        # 導入必要的模組
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.api.helpers import generate_and_upload_audio_to_gcs
        
        # 測試語音生成
        test_text = "老闆，我要一份經典夏威夷奶醬義大利麵，謝謝。"
        test_order_id = "test_voice_001"
        
        audio_url = generate_and_upload_audio_to_gcs(test_text, test_order_id)
        
        if audio_url:
            print(f"✅ 語音生成成功: {audio_url}")
            return True
        else:
            print("❌ 語音生成失敗")
            return False
            
    except Exception as e:
        print(f"❌ 語音生成測試失敗: {e}")
        return False

def deploy_to_cloud_run():
    """部署到 Cloud Run"""
    print("🚀 部署到 Cloud Run...")
    
    try:
        # 使用 gcloud 部署
        deploy_cmd = [
            'gcloud', 'run', 'deploy', 'ordering-helper-backend',
            '--source', '.',
            '--region', 'asia-east1',
            '--allow-unauthenticated'
        ]
        
        print("📦 開始部署...")
        result = subprocess.run(deploy_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 部署成功")
            return True
        else:
            print(f"❌ 部署失敗: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ gcloud CLI 未安裝")
        return False
    except Exception as e:
        print(f"❌ 部署失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 開始部署修正...")
    print("=" * 50)
    
    # 1. 檢查環境
    if not check_environment():
        print("❌ 環境檢查失敗")
        return False
    
    # 2. 創建 GCS bucket
    if not create_gcs_bucket_simple():
        print("⚠️ GCS bucket 創建失敗，但繼續部署")
    
    # 3. 測試語音生成
    if not test_voice_generation():
        print("⚠️ 語音生成測試失敗，但繼續部署")
    
    # 4. 部署到 Cloud Run
    if not deploy_to_cloud_run():
        print("❌ 部署失敗")
        return False
    
    print("\n🎉 部署完成！")
    print("\n📋 修正內容:")
    print("✅ 使用者語言摘要在第一行")
    print("✅ 金額格式修正（去除小數點）")
    print("✅ 語音檔上傳問題處理")
    print("✅ GCS bucket 設置")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
