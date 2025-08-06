#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Azure Speech SDK Docker 環境測試腳本
測試 Azure Speech SDK 在容器環境中的初始化
"""

import os
import sys
import platform

def test_azure_speech_initialization():
    """測試 Azure Speech SDK 初始化"""
    print("🔍 開始測試 Azure Speech SDK 初始化...")
    
    try:
        # 1. 檢查系統資訊
        print(f"\n1️⃣ 系統資訊:")
        print(f"   OS: {platform.system()} {platform.release()}")
        print(f"   Python: {platform.python_version()}")
        print(f"   Architecture: {platform.machine()}")
        
        # 2. 檢查 OpenSSL 版本
        print(f"\n2️⃣ OpenSSL 版本檢查:")
        try:
            import ssl
            print(f"   OpenSSL 版本: {ssl.OPENSSL_VERSION}")
        except Exception as e:
            print(f"   ❌ 無法取得 OpenSSL 版本: {e}")
        
        # 3. 檢查 Azure Speech SDK 導入
        print(f"\n3️⃣ Azure Speech SDK 導入測試:")
        try:
            from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig, ResultReason
            print("   ✅ Azure Speech SDK 導入成功")
            
            # 4. 測試 SpeechConfig 初始化
            print(f"\n4️⃣ SpeechConfig 初始化測試:")
            try:
                # 使用測試金鑰（如果有的話）
                speech_key = os.getenv('AZURE_SPEECH_KEY', 'test_key')
                speech_region = os.getenv('AZURE_SPEECH_REGION', 'eastus')
                
                speech_config = SpeechConfig(subscription=speech_key, region=speech_region)
                print("   ✅ SpeechConfig 初始化成功")
                
                # 5. 測試語音合成器初始化
                print(f"\n5️⃣ SpeechSynthesizer 初始化測試:")
                try:
                    # 使用記憶體輸出進行測試
                    audio_config = AudioConfig(use_default_speaker=False)
                    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
                    print("   ✅ SpeechSynthesizer 初始化成功")
                    
                    # 6. 測試簡單的語音合成
                    print(f"\n6️⃣ 語音合成測試:")
                    try:
                        result = synthesizer.speak_text_async("測試").get()
                        if result.reason == ResultReason.SynthesizingAudioCompleted:
                            print("   ✅ 語音合成測試成功")
                        else:
                            print(f"   ⚠️ 語音合成測試部分成功: {result.reason}")
                    except Exception as e:
                        print(f"   ⚠️ 語音合成測試失敗（可能是金鑰問題）: {e}")
                        
                except Exception as e:
                    print(f"   ❌ SpeechSynthesizer 初始化失敗: {e}")
                    
            except Exception as e:
                print(f"   ❌ SpeechConfig 初始化失敗: {e}")
                
        except Exception as e:
            print(f"   ❌ Azure Speech SDK 導入失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 7. 檢查系統庫依賴
        print(f"\n7️⃣ 系統庫依賴檢查:")
        import ctypes
        import ctypes.util
        
        # 檢查 libssl
        ssl_path = ctypes.util.find_library('ssl')
        if ssl_path:
            print(f"   ✅ libssl 找到: {ssl_path}")
        else:
            print("   ❌ libssl 未找到")
        
        # 檢查 libcrypto
        crypto_path = ctypes.util.find_library('crypto')
        if crypto_path:
            print(f"   ✅ libcrypto 找到: {crypto_path}")
        else:
            print("   ❌ libcrypto 未找到")
        
        # 檢查 libasound
        asound_path = ctypes.util.find_library('asound')
        if asound_path:
            print(f"   ✅ libasound 找到: {asound_path}")
        else:
            print("   ⚠️ libasound 未找到（在容器環境中可能不需要）")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variables():
    """測試環境變數"""
    print(f"\n🔍 環境變數檢查:")
    
    required_vars = [
        'AZURE_SPEECH_KEY',
        'AZURE_SPEECH_REGION'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {value[:10]}..." if len(value) > 10 else f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: 未設定")
            all_set = False
    
    return all_set

def test_file_permissions():
    """測試檔案權限"""
    print(f"\n🔍 檔案權限檢查:")
    
    # 檢查 /tmp/voices 目錄
    voice_dir = "/tmp/voices"
    if os.path.exists(voice_dir):
        print(f"   ✅ {voice_dir} 目錄存在")
        if os.access(voice_dir, os.R_OK | os.W_OK):
            print(f"   ✅ {voice_dir} 目錄可讀寫")
        else:
            print(f"   ❌ {voice_dir} 目錄權限不足")
            return False
    else:
        print(f"   ❌ {voice_dir} 目錄不存在")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 開始 Azure Speech SDK Docker 環境測試...")
    
    # 檢查環境變數
    env_ok = test_environment_variables()
    
    # 檢查檔案權限
    perm_ok = test_file_permissions()
    
    # 執行 Azure Speech SDK 測試
    if env_ok and perm_ok:
        test_azure_speech_initialization()
    else:
        print("\n❌ 環境設定不完整，跳過 Azure Speech SDK 測試")
        print("請確保以下環境變數已正確設定：")
        print("- AZURE_SPEECH_KEY")
        print("- AZURE_SPEECH_REGION") 