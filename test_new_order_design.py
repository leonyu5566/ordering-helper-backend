#!/usr/bin/env python3
"""
測試新的訂單設計思路
驗證分離中文訂單和使用者語言訂單的處理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.helpers import generate_order_summary_with_gemini

def test_new_order_design():
    """測試新的訂單設計"""
    print("🧪 測試新的訂單設計思路...")
    
    # 模擬訂單項目（包含原始中文菜名和翻譯菜名）
    test_items = [
        {
            'name': 'Creamy Classic Hawaiian',  # 翻譯菜名
            'original_name': '經典夏威夷奶醬義大利麵',  # 原始中文菜名
            'translated_name': 'Creamy Classic Hawaiian',  # 翻譯菜名
            'quantity': 1,
            'price': 115,
            'subtotal': 115
        },
        {
            'name': 'Creamy Shrimp Pineapple',  # 翻譯菜名
            'original_name': '奶油蝦仁鳳梨義大利麵',  # 原始中文菜名
            'translated_name': 'Creamy Shrimp Pineapple',  # 翻譯菜名
            'quantity': 1,
            'price': 140,
            'subtotal': 140
        }
    ]
    
    print("\n📋 測試項目:")
    for i, item in enumerate(test_items, 1):
        print(f"  項目 {i}:")
        print(f"    原始中文菜名: {item['original_name']}")
        print(f"    翻譯菜名: {item['translated_name']}")
        print(f"    數量: {item['quantity']}")
        print(f"    價格: ${item['price']}")
    
    # 測試英文使用者語言
    print("\n🌍 測試英文使用者語言...")
    result_en = generate_order_summary_with_gemini(test_items, 'en')
    
    print("\n📤 英文結果:")
    print(f"  中文語音: {result_en.get('chinese_voice', 'N/A')}")
    print(f"  中文摘要: {result_en.get('chinese_summary', 'N/A')}")
    print(f"  英文摘要: {result_en.get('user_summary', 'N/A')}")
    
    # 驗證結果
    print("\n✅ 英文使用者語言驗證:")
    
    # 檢查中文語音是否使用原始中文菜名
    chinese_voice = result_en.get('chinese_voice', '')
    if '經典夏威夷奶醬義大利麵' in chinese_voice and '奶油蝦仁鳳梨義大利麵' in chinese_voice:
        print("  ✅ 中文語音使用原始中文菜名")
    else:
        print("  ❌ 中文語音未使用原始中文菜名")
        print(f"     實際內容: {chinese_voice}")
    
    # 檢查中文摘要是否使用原始中文菜名
    chinese_summary = result_en.get('chinese_summary', '')
    if '經典夏威夷奶醬義大利麵' in chinese_summary and '奶油蝦仁鳳梨義大利麵' in chinese_summary:
        print("  ✅ 中文摘要使用原始中文菜名")
    else:
        print("  ❌ 中文摘要未使用原始中文菜名")
        print(f"     實際內容: {chinese_summary}")
    
    # 檢查英文摘要是否使用翻譯菜名
    user_summary = result_en.get('user_summary', '')
    if 'Creamy Classic Hawaiian' in user_summary and 'Creamy Shrimp Pineapple' in user_summary:
        print("  ✅ 英文摘要使用翻譯菜名")
    else:
        print("  ❌ 英文摘要未使用翻譯菜名")
        print(f"     實際內容: {user_summary}")
    
    # 測試中文使用者語言
    print("\n🌍 測試中文使用者語言...")
    result_zh = generate_order_summary_with_gemini(test_items, 'zh')
    
    print("\n📤 中文結果:")
    print(f"  中文語音: {result_zh.get('chinese_voice', 'N/A')}")
    print(f"  中文摘要: {result_zh.get('chinese_summary', 'N/A')}")
    print(f"  中文摘要: {result_zh.get('user_summary', 'N/A')}")
    
    print("\n✅ 中文使用者語言驗證:")
    
    # 檢查中文使用者語言時是否都使用原始中文菜名
    chinese_voice_zh = result_zh.get('chinese_voice', '')
    chinese_summary_zh = result_zh.get('chinese_summary', '')
    user_summary_zh = result_zh.get('user_summary', '')
    
    if ('經典夏威夷奶醬義大利麵' in chinese_voice_zh and 
        '奶油蝦仁鳳梨義大利麵' in chinese_voice_zh and
        '經典夏威夷奶醬義大利麵' in chinese_summary_zh and
        '奶油蝦仁鳳梨義大利麵' in chinese_summary_zh):
        print("  ✅ 中文使用者語言正確使用原始中文菜名")
    else:
        print("  ❌ 中文使用者語言未正確使用原始中文菜名")
    
    # 測試日文使用者語言
    print("\n🌍 測試日文使用者語言...")
    result_ja = generate_order_summary_with_gemini(test_items, 'ja')
    
    print("\n📤 日文結果:")
    print(f"  中文語音: {result_ja.get('chinese_voice', 'N/A')}")
    print(f"  中文摘要: {result_ja.get('chinese_summary', 'N/A')}")
    print(f"  日文摘要: {result_ja.get('user_summary', 'N/A')}")
    
    print("\n✅ 日文使用者語言驗證:")
    
    # 檢查日文使用者語言時中文部分是否使用原始中文菜名
    chinese_voice_ja = result_ja.get('chinese_voice', '')
    chinese_summary_ja = result_ja.get('chinese_summary', '')
    
    if ('經典夏威夷奶醬義大利麵' in chinese_voice_ja and 
        '奶油蝦仁鳳梨義大利麵' in chinese_voice_ja and
        '經典夏威夷奶醬義大利麵' in chinese_summary_ja and
        '奶油蝦仁鳳梨義大利麵' in chinese_summary_ja):
        print("  ✅ 日文使用者語言的中文部分正確使用原始中文菜名")
    else:
        print("  ❌ 日文使用者語言的中文部分未正確使用原始中文菜名")
    
    print("\n🎉 新設計測試完成!")

if __name__ == "__main__":
    test_new_order_design()
