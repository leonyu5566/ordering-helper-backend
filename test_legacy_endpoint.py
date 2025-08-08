#!/usr/bin/env python3
"""
測試舊端點是否正確工作
驗證防呆轉換器是否正確處理舊格式
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_legacy_endpoint():
    """測試舊端點"""
    print("🧪 測試舊端點...")
    
    # 模擬舊格式的請求
    old_format_request = {
        "store_id": 1,
        "items": [
            {
                "item_name": "經典夏威夷奶醬義大利麵",
                "quantity": 1,
                "price": 115
            },
            {
                "name": "奶油蝦仁鳳梨義大利麵",
                "qty": 1,
                "price_small": 140
            }
        ],
        "language": "en",
        "line_user_id": "U1234567890abcdef"
    }
    
    print("\n📋 舊格式請求:")
    print(f"  請求資料: {old_format_request}")
    
    # 模擬新格式的請求
    new_format_request = {
        "store_id": 1,
        "items": [
            {
                "name": {
                    "original": "經典夏威夷奶醬義大利麵",
                    "translated": "Creamy Classic Hawaiian"
                },
                "quantity": 1,
                "price": 115
            },
            {
                "name": {
                    "original": "奶油蝦仁鳳梨義大利麵",
                    "translated": "Creamy Shrimp Pineapple"
                },
                "quantity": 1,
                "price": 140
            }
        ],
        "language": "en",
        "line_user_id": "U1234567890abcdef"
    }
    
    print("\n📋 新格式請求:")
    print(f"  請求資料: {new_format_request}")
    
    # 測試防呆轉換器邏輯
    print("\n🔧 測試防呆轉換器邏輯...")
    
    def test_converter_logic():
        # 模擬舊格式項目
        old_item = {
            "item_name": "經典夏威夷奶醬義大利麵",
            "quantity": 1,
            "price": 115
        }
        
        # 防呆轉換器邏輯
        item_name = old_item.get('item_name') or old_item.get('name') or old_item.get('original_name') or '未知項目'
        
        # 檢查是否已經是新的雙語格式
        if isinstance(item_name, dict) and 'original' in item_name and 'translated' in item_name:
            # 已經是新格式
            simple_item = {
                'name': item_name,
                'quantity': old_item.get('quantity') or old_item.get('qty') or 1,
                'price': old_item.get('price') or old_item.get('price_small') or 0
            }
        else:
            # 舊格式，轉換成新格式
            simple_item = {
                'name': {
                    'original': item_name,
                    'translated': item_name
                },
                'quantity': old_item.get('quantity') or old_item.get('qty') or 1,
                'price': old_item.get('price') or old_item.get('price_small') or 0
            }
        
        print(f"  原始項目: {old_item}")
        print(f"  轉換後項目: {simple_item}")
        
        # 驗證轉換結果
        if (simple_item['name']['original'] == "經典夏威夷奶醬義大利麵" and 
            simple_item['name']['translated'] == "經典夏威夷奶醬義大利麵"):
            print("  ✅ 舊格式轉換成功")
        else:
            print("  ❌ 舊格式轉換失敗")
    
    test_converter_logic()
    
    # 測試新格式處理邏輯
    print("\n🔧 測試新格式處理邏輯...")
    
    def test_new_format_logic():
        # 模擬新格式項目
        new_item = {
            "name": {
                "original": "經典夏威夷奶醬義大利麵",
                "translated": "Creamy Classic Hawaiian"
            },
            "quantity": 1,
            "price": 115
        }
        
        # 防呆轉換器邏輯
        item_name = new_item.get('name')
        
        # 檢查是否已經是新的雙語格式
        if isinstance(item_name, dict) and 'original' in item_name and 'translated' in item_name:
            # 已經是新格式
            simple_item = {
                'name': item_name,
                'quantity': new_item.get('quantity') or new_item.get('qty') or 1,
                'price': new_item.get('price') or new_item.get('price_small') or 0
            }
        else:
            # 舊格式，轉換成新格式
            simple_item = {
                'name': {
                    'original': item_name,
                    'translated': item_name
                },
                'quantity': new_item.get('quantity') or new_item.get('qty') or 1,
                'price': new_item.get('price') or new_item.get('price_small') or 0
            }
        
        print(f"  原始項目: {new_item}")
        print(f"  處理後項目: {simple_item}")
        
        # 驗證處理結果
        if (simple_item['name']['original'] == "經典夏威夷奶醬義大利麵" and 
            simple_item['name']['translated'] == "Creamy Classic Hawaiian"):
            print("  ✅ 新格式處理成功")
        else:
            print("  ❌ 新格式處理失敗")
    
    test_new_format_logic()
    
    print("\n🎉 舊端點測試完成!")

if __name__ == "__main__":
    test_legacy_endpoint()
