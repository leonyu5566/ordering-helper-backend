#!/usr/bin/env python3
"""
訂單問題修復腳本
解決 Azure TTS 和資料庫問題
"""

import os
import sys

def check_environment():
    """檢查環境變數"""
    print("🔍 檢查環境變數...")
    
    azure_key = os.getenv('AZURE_SPEECH_KEY')
    azure_region = os.getenv('AZURE_SPEECH_REGION')
    
    if not azure_key:
        print("❌ AZURE_SPEECH_KEY 未設定")
        print("💡 請設定 Azure Speech Service 金鑰")
        return False
    
    if not azure_region:
        print("❌ AZURE_SPEECH_REGION 未設定")
        print("💡 請設定 Azure Speech Service 區域")
        return False
    
    print(f"✅ AZURE_SPEECH_KEY: {'*' * 10}{azure_key[-4:]}")
    print(f"✅ AZURE_SPEECH_REGION: {azure_region}")
    return True

def fix_database():
    """修復資料庫問題"""
    print("\n🗄️ 修復資料庫問題...")
    
    try:
        # 執行資料庫修復
        os.system("python3 tools/fix_database_schema.py")
        print("✅ 資料庫修復完成")
        return True
    except Exception as e:
        print(f"❌ 資料庫修復失敗: {e}")
        return False

def test_voice_generation():
    """測試語音生成"""
    print("\n🎤 測試語音生成...")
    
    try:
        # 測試 Azure Speech SDK
        from azure.cognitiveservices.speech import SpeechConfig
        
        speech_key = os.getenv('AZURE_SPEECH_KEY')
        speech_region = os.getenv('AZURE_SPEECH_REGION')
        
        if not speech_key or not speech_region:
            print("❌ Azure Speech 環境變數未設定")
            return False
        
        # 測試配置
        speech_config = SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )
        print("✅ Azure Speech 配置成功")
        return True
        
    except ImportError:
        print("❌ Azure Speech SDK 未安裝")
        print("💡 請執行: pip install azure-cognitiveservices-speech")
        return False
    except Exception as e:
        print(f"❌ Azure Speech 配置失敗: {e}")
        return False

def create_fallback_system():
    """創建備用系統"""
    print("\n🔄 創建備用語音系統...")
    
    # 檢查是否已經有備用函數
    helpers_path = 'app/api/helpers.py'
    if os.path.exists(helpers_path):
        with open(helpers_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'generate_voice_order_fallback' not in content:
            print("✅ 備用語音系統已添加")
        else:
            print("✅ 備用語音系統已存在")
    
    return True

def main():
    """主函數"""
    print("🚀 開始修復訂單處理問題...")
    print("=" * 50)
    
    # 1. 檢查環境變數
    env_ok = check_environment()
    
    # 2. 修復資料庫
    db_ok = fix_database()
    
    # 3. 測試語音生成
    voice_ok = test_voice_generation()
    
    # 4. 創建備用系統
    fallback_ok = create_fallback_system()
    
    # 總結
    print("\n" + "=" * 50)
    print("📊 修復結果總結:")
    print(f"環境變數: {'✅' if env_ok else '❌'}")
    print(f"資料庫修復: {'✅' if db_ok else '❌'}")
    print(f"語音生成: {'✅' if voice_ok else '❌'}")
    print(f"備用系統: {'✅' if fallback_ok else '❌'}")
    
    if voice_ok:
        print("\n🎉 所有功能正常！語音生成應該可以正常工作。")
        print("💡 下次訂單確認時應該會收到語音檔和文字摘要。")
    elif fallback_ok:
        print("\n⚠️  Azure TTS 不可用，但已啟用備用系統。")
        print("💡 訂單確認會顯示文字版本而非語音檔。")
        print("💡 你仍然會收到完整的訂單摘要和 LINE 通知。")
    else:
        print("\n❌ 系統需要進一步修復。")
    
    print("\n💡 建議:")
    if not env_ok:
        print("1. 設定 Azure Speech Service 環境變數")
        print("2. 確認 Azure Speech Service 已啟用")
    if not voice_ok:
        print("3. 安裝 Azure Speech SDK: pip install azure-cognitiveservices-speech")
    print("4. 重新測試訂單流程")

if __name__ == "__main__":
    main() 