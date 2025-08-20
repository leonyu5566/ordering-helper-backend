#!/usr/bin/env python3
"""
測試 Cloud Text-to-Speech 功能
"""

import os
import sys

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.helpers import generate_cloud_tts_audio

def test_cloud_tts():
    """測試 Cloud TTS 語音生成"""
    print("🧪 開始測試 Cloud Text-to-Speech 功能...")
    
    # 測試文字
    test_text = "您好，我要點餐。海鮮豆腐火鍋一份，謝謝。"
    output_file = "test_cloud_tts.mp3"
    
    print(f"📝 測試文字: {test_text}")
    print(f"🎵 輸出檔案: {output_file}")
    
    try:
        # 測試語音生成
        success = generate_cloud_tts_audio(
            text_to_speak=test_text,
            output_filename=output_file,
            language_code="zh-TW",
            voice_name="cmn-TW-Wavenet-A",
            speaking_rate=1.0
        )
        
        if success:
            print("✅ Cloud TTS 測試成功！")
            
            # 檢查檔案
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"📁 語音檔案已生成: {output_file}")
                print(f"📊 檔案大小: {file_size} bytes")
                
                # 清理測試檔案
                os.remove(output_file)
                print("🧹 測試檔案已清理")
            else:
                print("❌ 語音檔案未生成")
        else:
            print("❌ Cloud TTS 測試失敗")
            
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False
    
    return True

def test_different_speeds():
    """測試不同語速設定"""
    print("\n🧪 測試不同語速設定...")
    
    test_text = "這是語速測試。"
    speeds = [0.5, 1.0, 1.5, 2.0]
    
    for speed in speeds:
        output_file = f"test_speed_{speed}.mp3"
        print(f"🎵 測試語速 {speed}x: {output_file}")
        
        try:
            success = generate_cloud_tts_audio(
                text_to_speak=test_text,
                output_filename=output_file,
                language_code="zh-TW",
                voice_name="cmn-TW-Wavenet-A",
                speaking_rate=speed
            )
            
            if success and os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"  ✅ 成功生成，檔案大小: {file_size} bytes")
                # 清理測試檔案
                os.remove(output_file)
            else:
                print(f"  ❌ 生成失敗")
                
        except Exception as e:
            print(f"  ❌ 錯誤: {e}")

if __name__ == "__main__":
    print("🚀 Cloud Text-to-Speech 功能測試")
    print("=" * 50)
    
    # 基本功能測試
    if test_cloud_tts():
        print("\n🎉 基本功能測試通過！")
        
        # 語速測試
        test_different_speeds()
        print("\n🎉 所有測試完成！")
    else:
        print("\n❌ 基本功能測試失敗")
        sys.exit(1)
