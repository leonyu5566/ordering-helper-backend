#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語音檔生成測試腳本
測試 Azure TTS 語音生成和 URL 構建功能
"""

import os
import sys
import requests
import tempfile

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_voice_generation():
    """測試語音檔生成功能"""
    print("🔍 開始測試語音檔生成功能...")
    
    try:
        # 導入必要的模組
        from app.api.helpers import (
            generate_voice_with_custom_rate,
            VOICE_DIR,
            cleanup_old_voice_files
        )
        
        # 1. 測試語音檔生成
        print("\n1️⃣ 測試語音檔生成...")
        test_text = "您好，我要點餐。經典夏威夷奶醬義大利麵一份，美國脆薯兩份，總共225元，謝謝。"
        
        # 清理舊檔案
        cleanup_old_voice_files()
        
        # 生成語音檔
        voice_path = generate_voice_with_custom_rate(test_text, 1.0)
        
        if voice_path and os.path.exists(voice_path):
            print(f"✅ 語音檔生成成功: {voice_path}")
            print(f"📁 檔案大小: {os.path.getsize(voice_path)} bytes")
            
            # 2. 測試 URL 構建
            print("\n2️⃣ 測試 URL 構建...")
            fname = os.path.basename(voice_path)
            base_url = os.getenv('BASE_URL', 'https://ordering-helper-backend-1095766716155.asia-east1.run.app')
            audio_url = f"{base_url}/api/voices/{fname}"
            print(f"🔗 構建的 URL: {audio_url}")
            
            # 3. 測試靜態路由訪問
            print("\n3️⃣ 測試靜態路由訪問...")
            try:
                response = requests.get(audio_url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ 靜態路由訪問成功: {response.status_code}")
                    print(f"📊 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                    print(f"📊 Content-Length: {response.headers.get('Content-Length', 'N/A')}")
                else:
                    print(f"❌ 靜態路由訪問失敗: {response.status_code}")
                    print(f"📄 回應內容: {response.text[:200]}")
            except Exception as e:
                print(f"❌ 靜態路由訪問異常: {e}")
            
            # 4. 檢查檔案內容
            print("\n4️⃣ 檢查檔案內容...")
            try:
                with open(voice_path, 'rb') as f:
                    header = f.read(44)  # WAV 檔案頭
                    if header.startswith(b'RIFF') and b'WAVE' in header:
                        print("✅ 檔案格式正確 (WAV)")
                    else:
                        print("❌ 檔案格式不正確")
            except Exception as e:
                print(f"❌ 檔案讀取失敗: {e}")
            
            # 5. 清理測試檔案
            print("\n5️⃣ 清理測試檔案...")
            try:
                os.remove(voice_path)
                print("✅ 測試檔案已清理")
            except Exception as e:
                print(f"❌ 檔案清理失敗: {e}")
                
        else:
            print("❌ 語音檔生成失敗")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🎉 語音檔生成測試完成！")
    return True

def test_environment_variables():
    """測試環境變數設定"""
    print("\n🔍 檢查環境變數...")
    
    required_vars = [
        'AZURE_SPEECH_KEY',
        'AZURE_SPEECH_REGION',
        'BASE_URL'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:10]}..." if len(value) > 10 else f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: 未設定")
            all_set = False
    
    return all_set

def test_voice_directory():
    """測試語音目錄"""
    print("\n🔍 檢查語音目錄...")
    
    try:
        from app.api.helpers import VOICE_DIR
        print(f"📁 語音目錄: {VOICE_DIR}")
        
        if os.path.exists(VOICE_DIR):
            print("✅ 語音目錄存在")
            files = os.listdir(VOICE_DIR)
            print(f"📄 目錄內檔案數量: {len(files)}")
            if files:
                print(f"📄 檔案列表: {files[:5]}...")
        else:
            print("❌ 語音目錄不存在")
            return False
            
    except Exception as e:
        print(f"❌ 檢查語音目錄失敗: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 開始語音檔生成測試...")
    
    # 檢查環境變數
    env_ok = test_environment_variables()
    
    # 檢查語音目錄
    dir_ok = test_voice_directory()
    
    if env_ok and dir_ok:
        # 執行語音生成測試
        test_voice_generation()
    else:
        print("\n❌ 環境設定不完整，跳過語音生成測試")
        print("請確保以下環境變數已正確設定：")
        print("- AZURE_SPEECH_KEY")
        print("- AZURE_SPEECH_REGION") 
        print("- BASE_URL") 