
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
