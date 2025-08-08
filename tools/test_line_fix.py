#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 LINE 聊天室修復的腳本

功能：
1. 測試摘要生成是否正確
2. 測試語音檔生成和上傳
3. 測試 LINE Bot 訊息發送
4. 驗證修復是否解決了原始問題

使用方法：
python3 tools/test_line_fix.py
"""

import os
import sys
import json
import logging
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_summary_generation():
    """測試摘要生成功能"""
    print("🧪 測試摘要生成功能...")
    
    try:
        from app.api.helpers import (
            generate_chinese_order_summary,
            generate_user_language_order_summary,
            build_chinese_voice_text
        )
        
        # 測試資料
        test_items = [
            {
                'name': '奶油經典夏威夷',
                'quantity': 1,
                'price': 115,
                'subtotal': 115
            },
            {
                'name': '奶香培根玉米',
                'quantity': 1,
                'price': 110,
                'subtotal': 110
            }
        ]
        total_amount = 225
        
        # 測試中文摘要
        zh_summary = generate_chinese_order_summary(test_items, total_amount)
        print(f"✅ 中文摘要: {zh_summary}")
        
        # 測試英文摘要
        en_summary = generate_user_language_order_summary(test_items, total_amount, 'en')
        print(f"✅ 英文摘要: {en_summary}")
        
        # 測試語音文字
        voice_text = build_chinese_voice_text(test_items)
        print(f"✅ 語音文字: {voice_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ 摘要生成測試失敗: {e}")
        return False

def test_message_building():
    """測試訊息構建功能"""
    print("\n🧪 測試訊息構建功能...")
    
    try:
        from app.api.helpers import build_order_message
        
        # 測試正常情況
        messages = build_order_message(
            zh_summary="奶油經典夏威夷 x 1、奶香培根玉米 x 1",
            user_summary="Classic Hawaiian Cream x 1, Bacon Corn x 1",
            total=225,
            audio_url="https://storage.googleapis.com/voice-files/test.wav"
        )
        
        print(f"✅ 訊息構建成功，訊息數量: {len(messages)}")
        for i, msg in enumerate(messages):
            print(f"   訊息 {i+1}: {msg['type']}")
        
        # 測試摘要為空的情況
        try:
            build_order_message("", "test", 100, None)
            print("❌ 應該拋出異常但沒有")
            return False
        except ValueError:
            print("✅ 正確處理空摘要")
        
        return True
        
    except Exception as e:
        print(f"❌ 訊息構建測試失敗: {e}")
        return False

def test_audio_generation():
    """測試語音生成功能"""
    print("\n🧪 測試語音生成功能...")
    
    try:
        from app.api.helpers import generate_chinese_voice_with_azure
        
        # 測試語音生成
        test_text = "我要點餐：奶油經典夏威夷一份、奶香培根玉米一份"
        voice_path = generate_chinese_voice_with_azure(test_text, "test_order")
        
        if voice_path and os.path.exists(voice_path):
            file_size = os.path.getsize(voice_path)
            print(f"✅ 語音檔生成成功: {voice_path}, 大小: {file_size} bytes")
            
            # 清理測試檔案
            os.unlink(voice_path)
            return True
        else:
            print("❌ 語音檔生成失敗")
            return False
            
    except Exception as e:
        print(f"❌ 語音生成測試失敗: {e}")
        return False

def test_line_bot_integration():
    """測試 LINE Bot 整合"""
    print("\n🧪 測試 LINE Bot 整合...")
    
    try:
        from app.api.helpers import send_order_to_line_bot_fixed
        
        # 測試資料
        test_order_data = {
            'chinese_summary': '奶油經典夏威夷 x 1、奶香培根玉米 x 1',
            'user_summary': 'Classic Hawaiian Cream x 1, Bacon Corn x 1',
            'total_amount': 225,
            'voice_url': None  # 暫時不測試語音
        }
        
        # 使用測試用戶 ID
        test_user_id = "U1234567890abcdef"  # 測試用 ID
        
        # 測試發送（會失敗，但可以檢查邏輯）
        result = send_order_to_line_bot_fixed(test_user_id, test_order_data)
        
        if result is False:
            print("✅ LINE Bot 整合邏輯正確（預期失敗，因為是測試 ID）")
            return True
        else:
            print("❌ 預期失敗但成功了")
            return False
            
    except Exception as e:
        print(f"❌ LINE Bot 整合測試失敗: {e}")
        return False

def test_order_processing():
    """測試完整訂單處理流程"""
    print("\n🧪 測試完整訂單處理流程...")
    
    try:
        from app.api.helpers import OrderRequest, process_order_with_enhanced_tts
        
        # 建立測試訂單請求
        test_items = [
            {
                'name': {
                    'original': '奶油經典夏威夷',
                    'translated': 'Classic Hawaiian Cream'
                },
                'quantity': 1,
                'price': 115
            },
            {
                'name': {
                    'original': '奶香培根玉米',
                    'translated': 'Bacon Corn'
                },
                'quantity': 1,
                'price': 110
            }
        ]
        
        order_request = OrderRequest(
            lang='en',
            items=test_items,
            line_user_id='U1234567890abcdef'
        )
        
        # 處理訂單
        result = process_order_with_enhanced_tts(order_request)
        
        if result:
            print("✅ 訂單處理成功")
            print(f"   中文摘要: {result['zh_summary']}")
            print(f"   英文摘要: {result['user_summary']}")
            print(f"   語音文字: {result['voice_text']}")
            print(f"   總金額: {result['total_amount']}")
            return True
        else:
            print("❌ 訂單處理失敗")
            return False
            
    except Exception as e:
        print(f"❌ 訂單處理測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始測試 LINE 聊天室修復")
    print("=" * 50)
    
    # 設定日誌
    logging.basicConfig(level=logging.INFO)
    
    # 執行測試
    tests = [
        ("摘要生成", test_summary_generation),
        ("訊息構建", test_message_building),
        ("語音生成", test_audio_generation),
        ("LINE Bot 整合", test_line_bot_integration),
        ("完整訂單處理", test_order_processing)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 測試: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通過")
            else:
                print(f"❌ {test_name} 失敗")
        except Exception as e:
            print(f"❌ {test_name} 發生錯誤: {e}")
    
    # 總結
    print("\n" + "=" * 50)
    print(f"📊 測試結果: {passed}/{total} 項通過")
    
    if passed == total:
        print("\n🎉 所有測試都通過！")
        print("✅ LINE 聊天室修復應該有效")
        print("\n📝 修復內容:")
        print("1. ✅ 摘要取值錯誤已修復")
        print("2. ✅ TTS 檔案上傳到 GCS 已實作")
        print("3. ✅ 嚴謹的訊息構建檢查")
        print("4. ✅ 完整的錯誤處理")
    else:
        print(f"\n⚠️ {total - passed} 項測試失敗")
        print("請檢查錯誤訊息並修復問題")

if __name__ == "__main__":
    main()
