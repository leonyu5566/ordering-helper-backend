#!/usr/bin/env python3
"""
GCS Bucket 設置腳本
解決語音檔上傳問題
"""

import os
import sys
from google.cloud import storage
from google.cloud.exceptions import Conflict

def setup_gcs_bucket():
    """設置 GCS bucket 用於語音檔存儲"""
    try:
        # 初始化 GCS 客戶端
        storage_client = storage.Client()
        
        # Bucket 名稱
        bucket_name = 'ordering-helper-voice-files'
        
        print(f"🔧 設置 GCS bucket: {bucket_name}")
        
        # 檢查 bucket 是否存在
        bucket = storage_client.bucket(bucket_name)
        
        if bucket.exists():
            print(f"✅ Bucket '{bucket_name}' 已存在")
        else:
            print(f"📦 創建 bucket '{bucket_name}'...")
            try:
                # 創建 bucket
                bucket = storage_client.create_bucket(bucket_name, location='asia-east1')
                print(f"✅ 成功創建 bucket: {bucket_name}")
            except Conflict:
                print(f"⚠️ Bucket '{bucket_name}' 已存在（可能是並發創建）")
            except Exception as e:
                print(f"❌ 創建 bucket 失敗: {e}")
                return False
        
        # 設置公開讀取權限
        try:
            # 設置 IAM 政策，允許公開讀取
            policy = bucket.get_iam_policy(requested_policy_version=3)
            
            # 添加公開讀取權限
            policy.bindings.append({
                'role': 'roles/storage.objectViewer',
                'members': ['allUsers']
            })
            
            bucket.set_iam_policy(policy)
            print("✅ 已設置公開讀取權限")
            
        except Exception as e:
            print(f"⚠️ 設置公開權限失敗: {e}")
            print("💡 這可能需要手動設置或使用不同的權限策略")
        
        # 測試上傳
        print("🧪 測試上傳功能...")
        try:
            test_blob = bucket.blob('test/hello.txt')
            test_blob.upload_from_string('Hello, World!')
            test_blob.make_public()
            
            public_url = test_blob.public_url
            print(f"✅ 測試上傳成功: {public_url}")
            
            # 清理測試檔案
            test_blob.delete()
            print("🧹 已清理測試檔案")
            
        except Exception as e:
            print(f"❌ 測試上傳失敗: {e}")
            return False
        
        print("🎉 GCS bucket 設置完成！")
        return True
        
    except Exception as e:
        print(f"❌ GCS 設置失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 開始設置 GCS Bucket...")
    
    # 檢查環境變數
    required_vars = ['GOOGLE_APPLICATION_CREDENTIALS']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️ 缺少環境變數: {missing_vars}")
        print("💡 請確保已設置 Google Cloud 認證")
        return False
    
    success = setup_gcs_bucket()
    
    if success:
        print("\n📋 設置完成！")
        print("✅ GCS bucket 已創建並配置")
        print("✅ 語音檔上傳功能已啟用")
        print("✅ 公開讀取權限已設置")
    else:
        print("\n❌ 設置失敗！")
        print("💡 請檢查 Google Cloud 權限和認證")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
