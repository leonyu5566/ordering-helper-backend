#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試雙語訂單處理功能
驗證中文摘要和語音使用原文，使用者語言摘要使用翻譯
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, MenuItem, Menu, Store
from app.api.dto_models import build_menu_item_dto, build_order_item_dto, OrderSummaryDTO

def test_bilingual_menu_items():
    """測試雙語菜單項目處理"""
    print("🧪 測試雙語菜單項目處理...")
    
    # 模擬資料庫查詢結果
    class MockMenuItem:
        def __init__(self, menu_item_id, item_name, price_small, price_big=None):
            self.menu_item_id = menu_item_id
            self.item_name = item_name
            self.price_small = price_small
            self.price_big = price_big
    
    # 測試資料
    test_items = [
        MockMenuItem(1, "Kimchi Pot", 160, 200),
        MockMenuItem(2, "Satay Fish Head Pot", 180, 220),
        MockMenuItem(3, "牛肉麵", 120, 150),
        MockMenuItem(4, "滷肉飯", 80, 100)
    ]
    
    # 測試不同語言
    test_languages = ['zh', 'en', 'ja']
    
    for lang in test_languages:
        print(f"\n📋 測試語言: {lang}")
        for item in test_items:
            dto = build_menu_item_dto(item, lang)
            print(f"   {item.item_name} -> DTO: original='{dto.name_source}', ui='{dto.name_ui}'")

def test_bilingual_order_summary():
    """測試雙語訂單摘要生成"""
    print("\n🧪 測試雙語訂單摘要生成...")
    
    # 模擬訂單項目資料
    order_items_data = [
        {
            'menu_item_id': 1,
            'original_name': 'Kimchi Pot',
            'translated_name': '泡菜鍋',
            'quantity': 1,
            'price': 160,
            'subtotal': 160
        },
        {
            'menu_item_id': 2,
            'original_name': 'Satay Fish Head Pot',
            'translated_name': '沙爹魚頭鍋',
            'quantity': 1,
            'price': 180,
            'subtotal': 180
        }
    ]
    
    # 測試不同語言
    test_languages = ['zh', 'en', 'ja']
    
    for lang in test_languages:
        print(f"\n📋 測試語言: {lang}")
        
        # 建立訂單項目 DTO
        order_items_dto = []
        for item_data in order_items_data:
            dto = build_order_item_dto(item_data, lang)
            order_items_dto.append(dto)
            print(f"   DTO: original='{dto.name.original}', translated='{dto.name.translated}'")
        
        # 建立訂單摘要 DTO
        order_summary_dto = OrderSummaryDTO(
            store_name="葉來香50年古早味麵飯美食",
            items=order_items_dto,
            total_amount=340,
            user_language=lang
        )
        
        print(f"   中文摘要:")
        print(f"   {order_summary_dto.chinese_summary}")
        print(f"   使用者語言摘要:")
        print(f"   {order_summary_dto.user_language_summary}")
        print(f"   語音文字:")
        print(f"   {order_summary_dto.voice_text}")

def test_cjk_detection():
    """測試中日韓字符檢測"""
    print("\n🧪 測試中日韓字符檢測...")
    
    from app.api.dto_models import contains_cjk
    
    test_texts = [
        "Kimchi Pot",
        "泡菜鍋",
        "牛肉麵",
        "Satay Fish Head Pot",
        "沙爹魚頭鍋",
        "Hello World",
        "こんにちは",
        "안녕하세요"
    ]
    
    for text in test_texts:
        is_cjk = contains_cjk(text)
        print(f"   '{text}' -> CJK: {is_cjk}")

def main():
    """主測試函數"""
    print("🚀 開始測試雙語訂單處理功能")
    print("=" * 50)
    
    try:
        # 測試中日韓字符檢測
        test_cjk_detection()
        
        # 測試雙語菜單項目處理
        test_bilingual_menu_items()
        
        # 測試雙語訂單摘要生成
        test_bilingual_order_summary()
        
        print("\n✅ 所有測試完成！")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
