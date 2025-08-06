#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試文本預處理功能
驗證 normalize_order_text_for_tts 函數是否正確處理各種格式的訂單文本
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.helpers import normalize_order_text_for_tts

def test_text_normalization():
    """
    測試文本預處理功能
    """
    test_cases = [
        # 基本測試
        ("經典奶油夏威夷義大利麵 x1、綠茶 x1", "經典奶油夏威夷義大利麵一份、綠茶一杯"),
        ("牛肉麵 X1、可樂 *1", "牛肉麵一份、可樂一杯"),
        ("雞排飯 ×2、奶茶 x1", "雞排飯二份、奶茶一杯"),
        
        # 飲料類測試
        ("柳橙汁 x2、蘋果茶 x1", "柳橙汁二杯、蘋果茶一杯"),
        ("啤酒 x3、檸檬汁 x1", "啤酒三杯、檸檬汁一杯"),
        
        # 餐點類測試
        ("義大利麵 x1、牛排 x2", "義大利麵一份、牛排二份"),
        ("豬排飯 x1、魚排 x3", "豬排飯一份、魚排三份"),
        
        # 混合測試
        ("牛肉麵 x1、綠茶 x2、雞排 x1", "牛肉麵一份、綠茶二杯、雞排一份"),
        
        # 邊界測試
        ("", ""),  # 空字串
        ("沒有數量的文本", "沒有數量的文本"),  # 沒有 x1 格式
    ]
    
    print("=== 文本預處理測試 ===")
    print("測試 normalize_order_text_for_tts 函數\n")
    
    passed = 0
    total = len(test_cases)
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        try:
            result = normalize_order_text_for_tts(input_text)
            status = "✅ PASS" if result == expected else "❌ FAIL"
            
            print(f"測試 {i}: {status}")
            print(f"  輸入: {input_text}")
            print(f"  預期: {expected}")
            print(f"  實際: {result}")
            
            if result == expected:
                passed += 1
            else:
                print(f"  ❌ 不匹配！")
            
            print()
            
        except Exception as e:
            print(f"測試 {i}: ❌ ERROR")
            print(f"  輸入: {input_text}")
            print(f"  錯誤: {e}")
            print()
    
    print(f"=== 測試結果 ===")
    print(f"通過: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 所有測試通過！")
        return True
    else:
        print("⚠️  部分測試失敗，請檢查實現")
        return False

if __name__ == "__main__":
    success = test_text_normalization()
    sys.exit(0 if success else 1) 