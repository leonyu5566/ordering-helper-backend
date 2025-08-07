# 欄位名稱同步建議

## 概述
本文檔提供了後端Flask、前端點餐介面（liff-web）和Line Bot之間的欄位名稱同步建議，以確保系統間的一致性。

## 當前欄位對照表

### 1. 菜單項目欄位

| 用途 | 後端Flask | 前端liff-web | 建議統一 |
|------|-----------|--------------|----------|
| 項目ID | `menu_item_id` | `id`, `menu_item_id`, `temp_id` | `menu_item_id` |
| 項目名稱 | `item_name` | `translated_name`, `original_name`, `item_name` | `item_name` |
| 小份價格 | `price_small` | `price`, `price_small`, `price_unit` | `price_small` |
| 大份價格 | `price_big` | 未使用 | `price_big` |
| 描述 | `description` | `description` | `description` |

### 2. 訂單欄位

| 用途 | 後端Flask | 前端liff-web | 建議統一 |
|------|-----------|--------------|----------|
| 訂單ID | `order_id` | `order_id` | `order_id` |
| 使用者ID | `user_id` | `line_user_id` | `user_id` |
| 店家ID | `store_id` | `store_id` | `store_id` |
| 數量 | `quantity_small` | `quantity`, `qty` | `quantity` |
| 小計 | `subtotal` | `subtotal` | `subtotal` |
| 總金額 | `total_amount` | `total` | `total_amount` |

### 3. 店家欄位

| 用途 | 後端Flask | Line Bot | 建議統一 |
|------|-----------|----------|----------|
| 店家ID | `store_id` | `store_id` | `store_id` |
| 店家名稱 | `store_name` | `store_name` | `store_name` |
| 合作等級 | `partner_level` | `partner_level` | `partner_level` |
| 緯度 | `gps_lat` | `gps_lat` | `gps_lat` |
| 經度 | `gps_lng` | `gps_lng` | `gps_lng` |

## 建議的修正方案

### 1. 前端liff-web修正建議

```javascript
// 發送訂單時的欄位統一
const orderItem = {
    menu_item_id: item.menu_item_id || item.id || item.temp_id,
    quantity: quantity,  // 統一使用 quantity
    price_small: priceUnit,  // 統一使用 price_small
    item_name: item.item_name || item.translated_name || item.original_name,
    subtotal: itemTotal
};

// 接收菜單資料時的欄位統一
const menuItem = {
    menu_item_id: item.menu_item_id || item.id || item.temp_id,
    item_name: item.item_name || item.translated_name || item.original_name,
    price_small: item.price_small || item.price || item.price_unit,
    price_big: item.price_big,
    description: item.description
};
```

### 2. 後端Flask API修正建議

```python
# 訂單API回應欄位統一
order_item = {
    'menu_item_id': item.menu_item_id,
    'quantity': item.quantity_small,  # 統一使用 quantity
    'price_small': item.price_small,
    'price_big': item.price_big,
    'item_name': item.item_name,
    'subtotal': item.subtotal
}

# 菜單API回應欄位統一
menu_item = {
    'menu_item_id': item.menu_item_id,
    'item_name': item.item_name,
    'price_small': item.price_small,
    'price_big': item.price_big,
    'description': item.description,
    'translated_name': translated_name  # 保留翻譯欄位
}
```

### 3. Line Bot修正建議

```python
# 訂單資料結構統一
order_data = {
    "order_id": order_id,
    "user_id": user_id,  # 統一使用 user_id
    "store_id": store_id,
    "total_amount": total_amount,
    "voice_url": voice_url,
    "chinese_summary": chinese_summary,
    "user_summary": user_summary,
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

## 實施步驟

### 階段1：後端Flask修正
1. 修改 `/api/orders` 端點，統一使用 `quantity` 而非 `quantity_small`
2. 修改 `/api/menu/<store_id>` 端點，確保回應欄位一致性
3. 更新資料庫查詢，確保欄位對應正確

### 階段2：前端liff-web修正
1. 修改訂單提交邏輯，統一使用建議的欄位名稱
2. 修改菜單渲染邏輯，確保欄位對應正確
3. 更新購物車邏輯，統一數量欄位名稱

### 階段3：Line Bot修正
1. 更新訂單接收邏輯，統一欄位名稱
2. 修改店家查詢回應，確保欄位一致性
3. 更新使用者管理，統一ID欄位名稱

## 測試建議

### 1. 訂單流程測試
- 測試合作店家訂單提交
- 測試非合作店家訂單提交
- 驗證Line Bot接收訂單資料的正確性

### 2. 菜單顯示測試
- 測試合作店家菜單載入
- 測試OCR菜單處理
- 驗證多語言翻譯功能

### 3. 資料一致性測試
- 驗證所有API端點的欄位名稱一致性
- 測試資料庫欄位對應正確性
- 確認前端顯示與後端資料一致

## 注意事項

1. **向後相容性**：在過渡期間，建議保留舊欄位名稱作為備用
2. **分階段實施**：建議按照階段逐步實施，避免一次性大規模修改
3. **充分測試**：每個階段完成後都要進行充分測試
4. **文檔更新**：同步更新API文檔和使用說明

## 結論

通過統一欄位名稱，可以：
- 提高系統間的一致性
- 減少開發和維護成本
- 降低資料傳輸錯誤的風險
- 提升整體系統的穩定性

建議按照上述方案逐步實施欄位名稱同步，確保系統的穩定性和一致性。
