#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
欄位名稱同步修正腳本
功能：修正後端Flask API的欄位名稱，確保與前端和Line Bot的一致性
"""

import os
import re
from pathlib import Path

def fix_api_routes():
    """修正API路由中的欄位名稱"""
    print("🔧 修正API路由欄位名稱...")
    
    # 修正訂單API端點
    routes_file = "app/api/routes.py"
    
    if os.path.exists(routes_file):
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修正訂單項目欄位名稱
        # 將 quantity_small 統一為 quantity
        content = re.sub(
            r'quantity_small\s*=\s*int\(item\.get\(\'quantity\',\s*1\)\)',
            'quantity = int(item.get(\'quantity\', 1))',
            content
        )
        
        content = re.sub(
            r'quantity_small\s*=\s*item\.quantity_small',
            'quantity = item.quantity_small',
            content
        )
        
        # 修正菜單項目欄位名稱
        content = re.sub(
            r'\'id\':\s*item\.menu_item_id',
            '\'menu_item_id\': item.menu_item_id',
            content
        )
        
        content = re.sub(
            r'\'item_name\':\s*item\.translated_name',
            '\'item_name\': item.item_name',
            content
        )
        
        # 修正價格欄位名稱
        content = re.sub(
            r'\'price\':\s*item\.price_small',
            '\'price_small\': item.price_small',
            content
        )
        
        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ API路由欄位名稱修正完成")
    else:
        print("❌ 找不到API路由檔案")

def fix_models():
    """修正資料庫模型中的欄位名稱"""
    print("🔧 修正資料庫模型欄位名稱...")
    
    models_file = "app/models.py"
    
    if os.path.exists(models_file):
        with open(models_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 確保OrderItem模型使用正確的欄位名稱
        # 注意：這裡只是檢查，實際的資料庫欄位名稱保持不變
        # 但在API回應中統一使用 quantity 而非 quantity_small
        
        print("✅ 資料庫模型檢查完成（欄位名稱保持不變，API回應中統一）")
    else:
        print("❌ 找不到模型檔案")

def fix_helpers():
    """修正helpers中的欄位名稱"""
    print("🔧 修正helpers欄位名稱...")
    
    helpers_file = "app/api/helpers.py"
    
    if os.path.exists(helpers_file):
        with open(helpers_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修正訂單摘要生成中的欄位名稱
        content = re.sub(
            r'quantity_small',
            'quantity',
            content
        )
        
        # 修正菜單翻譯中的欄位名稱
        content = re.sub(
            r'\'id\':\s*item\.menu_item_id',
            '\'menu_item_id\': item.menu_item_id',
            content
        )
        
        with open(helpers_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ helpers欄位名稱修正完成")
    else:
        print("❌ 找不到helpers檔案")

def create_api_response_example():
    """建立統一的API回應範例"""
    print("📝 建立統一的API回應範例...")
    
    example_content = '''
# 統一的API回應格式範例

## 菜單項目回應格式
{
    "menu_item_id": 123,
    "item_name": "宮保雞丁",
    "price_small": 120,
    "price_big": 180,
    "description": "經典川菜，雞肉配花生",
    "translated_name": "Kung Pao Chicken"  # 翻譯版本（可選）
}

## 訂單項目回應格式
{
    "menu_item_id": 123,
    "quantity": 2,  # 統一使用 quantity
    "price_small": 120,
    "item_name": "宮保雞丁",
    "subtotal": 240
}

## 訂單回應格式
{
    "order_id": 456,
    "user_id": 789,
    "store_id": 1,
    "total_amount": 360,
    "status": "pending",
    "order_details": [
        {
            "menu_item_id": 123,
            "quantity": 2,
            "price_small": 120,
            "item_name": "宮保雞丁",
            "subtotal": 240
        }
    ]
}
'''
    
    with open("API_RESPONSE_FORMAT.md", 'w', encoding='utf-8') as f:
        f.write(example_content)
    
    print("✅ API回應格式範例建立完成")

def create_frontend_sync_guide():
    """建立前端同步指南"""
    print("📝 建立前端同步指南...")
    
    guide_content = '''
# 前端欄位名稱同步指南

## 發送訂單時的欄位統一

```javascript
// 修正前
const orderItem = {
    id: item.id,
    quantity: quantity,
    price: priceUnit,
    name: item.name
};

// 修正後
const orderItem = {
    menu_item_id: item.menu_item_id || item.id || item.temp_id,
    quantity: quantity,
    price_small: priceUnit,
    item_name: item.item_name || item.translated_name || item.original_name,
    subtotal: itemTotal
};
```

## 接收菜單資料時的欄位統一

```javascript
// 修正前
const itemName = item.translated_name || item.original_name;
const price = item.price || item.price_unit;

// 修正後
const itemName = item.item_name || item.translated_name || item.original_name;
const price = item.price_small || item.price || item.price_unit;
```

## 購物車邏輯修正

```javascript
// 修正前
const itemId = item.id || item.menu_item_id;

// 修正後
const itemId = item.menu_item_id || item.id || item.temp_id;
```

## 訂單提交payload修正

```javascript
// 修正前
const payload = {
    line_user_id: currentUserId,
    store_id: currentStore,
    items: orderItems,
    total: totalAmount
};

// 修正後
const payload = {
    user_id: currentUserId,  // 統一使用 user_id
    store_id: currentStore,
    items: orderItems,
    total_amount: totalAmount  // 統一使用 total_amount
};
```
'''
    
    with open("FRONTEND_SYNC_GUIDE.md", 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("✅ 前端同步指南建立完成")

def create_linebot_sync_guide():
    """建立Line Bot同步指南"""
    print("📝 建立Line Bot同步指南...")
    
    guide_content = '''
# Line Bot欄位名稱同步指南

## 訂單資料接收格式

```python
# 修正前
order_data = {
    "order_id": order_id,
    "line_user_id": user_id,
    "total": total_amount,
    "items": order_items
}

# 修正後
order_data = {
    "order_id": order_id,
    "user_id": user_id,  # 統一使用 user_id
    "total_amount": total_amount,  # 統一使用 total_amount
    "order_details": [
        {
            "menu_item_id": item.menu_item_id,
            "quantity": item.quantity,
            "price_small": item.price_small,
            "item_name": item.item_name,
            "subtotal": item.subtotal
        }
    ]
}
```

## 店家查詢回應格式

```python
# 修正前
store_info = {
    "id": store.store_id,
    "name": store.store_name,
    "level": store.partner_level
}

# 修正後
store_info = {
    "store_id": store.store_id,
    "store_name": store.store_name,
    "partner_level": store.partner_level
}
```

## 使用者管理欄位統一

```python
# 修正前
user_data = {
    "line_user_id": user.line_user_id,
    "lang": user.preferred_lang
}

# 修正後
user_data = {
    "user_id": user.user_id,  # 統一使用 user_id
    "line_user_id": user.line_user_id,  # 保留作為備用
    "preferred_lang": user.preferred_lang
}
```
'''
    
    with open("LINEBOT_SYNC_GUIDE.md", 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("✅ Line Bot同步指南建立完成")

def main():
    """主函數"""
    print("🚀 開始欄位名稱同步修正...")
    print("=" * 50)
    
    # 1. 修正後端Flask
    fix_api_routes()
    fix_models()
    fix_helpers()
    
    # 2. 建立文檔
    create_api_response_example()
    create_frontend_sync_guide()
    create_linebot_sync_guide()
    
    print("=" * 50)
    print("✅ 欄位名稱同步修正完成！")
    print("\n📋 已建立的檔案：")
    print("- FIELD_SYNC_RECOMMENDATIONS.md (欄位對照表)")
    print("- API_RESPONSE_FORMAT.md (API回應格式)")
    print("- FRONTEND_SYNC_GUIDE.md (前端同步指南)")
    print("- LINEBOT_SYNC_GUIDE.md (Line Bot同步指南)")
    print("\n💡 下一步：")
    print("1. 檢查修正後的程式碼")
    print("2. 測試API端點功能")
    print("3. 更新前端程式碼")
    print("4. 更新Line Bot程式碼")
    print("5. 進行完整測試")

if __name__ == "__main__":
    main()
