
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
