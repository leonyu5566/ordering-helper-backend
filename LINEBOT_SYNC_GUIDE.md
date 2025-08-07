
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
