#!/usr/bin/env python3
"""
測試雙語訂單設計
驗證從源頭就保存 original_name 與 translated_name 的設計
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.helpers import OrderRequest, LocalisedName, OrderItemRequest, process_order_with_dual_language

def test_dual_language_order():
    """測試雙語訂單設計"""
    print("🧪 測試雙語訂單設計...")
    
    # 創建測試訂單項目
    test_items = [
        OrderItemRequest(
            name=LocalisedName(
                original="經典夏威夷奶醬義大利麵",
                translated="Creamy Classic Hawaiian"
            ),
            quantity=1,
            price=115.0
        ),
        OrderItemRequest(
            name=LocalisedName(
                original="奶油蝦仁鳳梨義大利麵",
                translated="Creamy Shrimp Pineapple"
            ),
            quantity=1,
            price=140.0
        )
    ]
    
    print("\n📋 測試項目:")
    for i, item in enumerate(test_items, 1):
        print(f"  項目 {i}:")
        print(f"    原始中文菜名: {item.name.original}")
        print(f"    翻譯菜名: {item.name.translated}")
        print(f"    數量: {item.quantity}")
        print(f"    價格: ${item.price}")
    
    # 測試英文使用者語言
    print("\n🌍 測試英文使用者語言...")
    order_request_en = OrderRequest(
        lang="en",
        items=test_items,
        line_user_id="U1234567890abcdef"
    )
    
    result_en = process_order_with_dual_language(order_request_en)
    
    if result_en:
        print("\n📤 英文結果:")
        print(f"  中文摘要: {result_en.get('zh_summary', 'N/A')}")
        print(f"  英文摘要: {result_en.get('user_summary', 'N/A')}")
        print(f"  語音文字: {result_en.get('voice_text', 'N/A')}")
        print(f"  總金額: ${result_en.get('total_amount', 0)}")
        
        # 驗證結果
        print("\n✅ 英文使用者語言驗證:")
        
        # 檢查中文摘要是否使用原始中文菜名
        zh_summary = result_en.get('zh_summary', '')
        if '經典夏威夷奶醬義大利麵' in zh_summary and '奶油蝦仁鳳梨義大利麵' in zh_summary:
            print("  ✅ 中文摘要使用原始中文菜名")
        else:
            print("  ❌ 中文摘要未使用原始中文菜名")
            print(f"     實際內容: {zh_summary}")
        
        # 檢查英文摘要是否使用翻譯菜名
        user_summary = result_en.get('user_summary', '')
        if 'Creamy Classic Hawaiian' in user_summary and 'Creamy Shrimp Pineapple' in user_summary:
            print("  ✅ 英文摘要使用翻譯菜名")
        else:
            print("  ❌ 英文摘要未使用翻譯菜名")
            print(f"     實際內容: {user_summary}")
        
        # 檢查語音文字是否使用原始中文菜名
        voice_text = result_en.get('voice_text', '')
        if '經典夏威夷奶醬義大利麵' in voice_text and '奶油蝦仁鳳梨義大利麵' in voice_text:
            print("  ✅ 語音文字使用原始中文菜名")
        else:
            print("  ❌ 語音文字未使用原始中文菜名")
            print(f"     實際內容: {voice_text}")
    else:
        print("  ❌ 英文訂單處理失敗")
    
    # 測試中文使用者語言
    print("\n🌍 測試中文使用者語言...")
    order_request_zh = OrderRequest(
        lang="zh-TW",
        items=test_items,
        line_user_id="U1234567890abcdef"
    )
    
    result_zh = process_order_with_dual_language(order_request_zh)
    
    if result_zh:
        print("\n📤 中文結果:")
        print(f"  中文摘要: {result_zh.get('zh_summary', 'N/A')}")
        print(f"  中文摘要: {result_zh.get('user_summary', 'N/A')}")
        print(f"  語音文字: {result_zh.get('voice_text', 'N/A')}")
        print(f"  總金額: ${result_zh.get('total_amount', 0)}")
        
        print("\n✅ 中文使用者語言驗證:")
        
        # 檢查中文使用者語言時是否都使用原始中文菜名
        zh_summary_zh = result_zh.get('zh_summary', '')
        user_summary_zh = result_zh.get('user_summary', '')
        voice_text_zh = result_zh.get('voice_text', '')
        
        if ('經典夏威夷奶醬義大利麵' in zh_summary_zh and 
            '奶油蝦仁鳳梨義大利麵' in zh_summary_zh and
            '經典夏威夷奶醬義大利麵' in user_summary_zh and
            '奶油蝦仁鳳梨義大利麵' in user_summary_zh and
            '經典夏威夷奶醬義大利麵' in voice_text_zh and
            '奶油蝦仁鳳梨義大利麵' in voice_text_zh):
            print("  ✅ 中文使用者語言正確使用原始中文菜名")
        else:
            print("  ❌ 中文使用者語言未正確使用原始中文菜名")
    else:
        print("  ❌ 中文訂單處理失敗")
    
    # 測試日文使用者語言
    print("\n🌍 測試日文使用者語言...")
    order_request_ja = OrderRequest(
        lang="ja",
        items=test_items,
        line_user_id="U1234567890abcdef"
    )
    
    result_ja = process_order_with_dual_language(order_request_ja)
    
    if result_ja:
        print("\n📤 日文結果:")
        print(f"  中文摘要: {result_ja.get('zh_summary', 'N/A')}")
        print(f"  日文摘要: {result_ja.get('user_summary', 'N/A')}")
        print(f"  語音文字: {result_ja.get('voice_text', 'N/A')}")
        print(f"  總金額: ${result_ja.get('total_amount', 0)}")
        
        print("\n✅ 日文使用者語言驗證:")
        
        # 檢查日文使用者語言時中文部分是否使用原始中文菜名
        zh_summary_ja = result_ja.get('zh_summary', '')
        voice_text_ja = result_ja.get('voice_text', '')
        user_summary_ja = result_ja.get('user_summary', '')
        
        if ('經典夏威夷奶醬義大利麵' in zh_summary_ja and 
            '奶油蝦仁鳳梨義大利麵' in zh_summary_ja and
            '經典夏威夷奶醬義大利麵' in voice_text_ja and
            '奶油蝦仁鳳梨義大利麵' in voice_text_ja and
            'Creamy Classic Hawaiian' in user_summary_ja and
            'Creamy Shrimp Pineapple' in user_summary_ja):
            print("  ✅ 日文使用者語言正確處理雙語菜名")
        else:
            print("  ❌ 日文使用者語言未正確處理雙語菜名")
    else:
        print("  ❌ 日文訂單處理失敗")
    
    print("\n🎉 雙語訂單設計測試完成!")

if __name__ == "__main__":
    test_dual_language_order()
