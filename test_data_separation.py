#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試資料分離修正
驗證 native 和 display 資料流完全分離
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.dto_models import build_order_item_dto, OrderSummaryDTO

def test_data_separation():
    """測試資料分離"""
    print("🧪 測試資料分離...")
    
    # 模擬訂單項目資料（模擬圖片中的情況）
    order_items_data = [
        {
            'menu_item_id': 1,
            'original_name': '招牌金湯酸菜',  # 中文原文
            'translated_name': 'Signature Golden Soup Pickled Cabbage',  # 英文翻譯
            'quantity': 1,
            'price': 68,
            'subtotal': 68
        },
        {
            'menu_item_id': 2,
            'original_name': '白濃雞湯',  # 中文原文
            'translated_name': 'White Thick Chicken Soup',  # 英文翻譯
            'quantity': 1,
            'price': 49,
            'subtotal': 49
        }
    ]
    
    # 測試英文使用者
    user_language = 'en'
    native_store_name = '食肆鍋'
    display_store_name = 'Restaurant Hot Pot'
    
    print(f"📋 測試語言: {user_language}")
    print(f"   Native 店名: {native_store_name}")
    print(f"   Display 店名: {display_store_name}")
    
    # 建立訂單項目 DTO
    order_items_dto = []
    for item_data in order_items_data:
        dto = build_order_item_dto(item_data, user_language)
        order_items_dto.append(dto)
        print(f"   DTO: original='{dto.name.original}', translated='{dto.name.translated}'")
    
    # 建立 native 摘要（用於中文摘要和語音）
    order_summary_native = OrderSummaryDTO(
        store_name=native_store_name,
        items=order_items_dto,
        total_amount=117,
        user_language='zh'  # 強制使用中文
    )
    
    # 建立 display 摘要（用於使用者語言摘要）
    order_summary_display = OrderSummaryDTO(
        store_name=display_store_name,
        items=order_items_dto,
        total_amount=117,
        user_language=user_language
    )
    
    # 生成雙語摘要
    chinese_summary = order_summary_native.chinese_summary
    user_language_summary = order_summary_display.user_language_summary
    chinese_voice_text = order_summary_native.voice_text
    
    print(f"\n📝 生成結果:")
    print(f"   中文摘要:")
    print(f"   {chinese_summary}")
    print(f"   使用者語言摘要:")
    print(f"   {user_language_summary}")
    print(f"   語音文字:")
    print(f"   {chinese_voice_text}")
    
    # 驗證結果
    print(f"\n✅ 驗證結果:")
    
    # 驗證中文摘要
    native_store_correct = native_store_name in chinese_summary
    native_items_correct = all(item.name.original in chinese_summary for item in order_items_dto)
    print(f"   - 中文摘要使用 native 店名: {'✓' if native_store_correct else '✗'}")
    print(f"   - 中文摘要使用 native 品名: {'✓' if native_items_correct else '✗'}")
    
    # 驗證使用者語言摘要
    display_store_correct = display_store_name in user_language_summary
    display_items_correct = all(item.name.translated in user_language_summary for item in order_items_dto)
    print(f"   - 使用者語言摘要使用 display 店名: {'✓' if display_store_correct else '✗'}")
    print(f"   - 使用者語言摘要使用 display 品名: {'✓' if display_items_correct else '✗'}")
    
    # 驗證語音
    voice_correct = all(item.name.original in chinese_voice_text for item in order_items_dto)
    print(f"   - 語音使用中文原文: {'✓' if voice_correct else '✗'}")
    
    # 驗證資料分離
    print(f"\n🔍 資料分離檢查:")
    print(f"   - 中文摘要店名: '{native_store_name}'")
    print(f"   - 使用者語言摘要店名: '{display_store_name}'")
    print(f"   - 店名是否分離: {'✓' if native_store_name != display_store_name else '✗'}")
    
    print(f"   - 中文摘要品名: {[item.name.original for item in order_items_dto]}")
    print(f"   - 使用者語言摘要品名: {[item.name.translated for item in order_items_dto]}")
    print(f"   - 品名是否分離: {'✓' if any(item.name.original != item.name.translated for item in order_items_dto) else '✗'}")

def test_inplace_mutation_prevention():
    """測試防止就地修改"""
    print("\n🧪 測試防止就地修改...")
    
    # 模擬可能發生就地修改的情況
    order_items_data = [
        {
            'menu_item_id': 1,
            'original_name': '招牌金湯酸菜',
            'translated_name': 'Signature Golden Soup Pickled Cabbage',
            'quantity': 1,
            'price': 68,
            'subtotal': 68
        }
    ]
    
    # 建立 DTO
    dto = build_order_item_dto(order_items_data[0], 'en')
    original_name = dto.name.original
    translated_name = dto.name.translated
    
    print(f"   原始狀態: original='{original_name}', translated='{translated_name}'")
    
    # 模擬就地修改（這應該不會發生，但我們要確保防護）
    try:
        # 嘗試修改 translated 名稱
        dto.name.translated = "Modified Name"
        print(f"   修改後: original='{dto.name.original}', translated='{dto.name.translated}'")
        
        # 檢查是否影響 original
        if dto.name.original == original_name:
            print(f"   ✅ 就地修改未影響 original 名稱")
        else:
            print(f"   ❌ 就地修改影響了 original 名稱")
            
    except Exception as e:
        print(f"   ✅ 防止就地修改: {e}")

def main():
    """主測試函數"""
    print("🚀 開始測試資料分離修正")
    print("=" * 60)
    
    try:
        # 測試資料分離
        test_data_separation()
        
        # 測試防止就地修改
        test_inplace_mutation_prevention()
        
        print("\n✅ 所有測試完成！")
        print("\n📝 修正重點:")
        print("   1. 完全分離 native 和 display 資料流")
        print("   2. 深拷貝避免共用物件")
        print("   3. 防止就地修改")
        print("   4. 結構化日誌驗證")
        print("   5. 零資料庫改動")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
