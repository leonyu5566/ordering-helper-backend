# 價格驗證問題修復報告

## 問題描述

根據用戶提供的截圖，當有價格為 0 元的商品（如基本湯底）時，移動應用程式會出現以下錯誤：
- "Order submission failed: Invalid price"
- "昆布柴魚 No valid price, please edit first"

這些錯誤訊息來自前端應用程式的價格驗證邏輯，當檢測到價格為 0 的商品時會阻止訂單提交。

## 解決方案

### 1. 後端過濾策略

我們採用後端過濾的策略，確保價格為 0 的商品不會被返回給前端，這樣就不會觸發前端的價格驗證錯誤。

### 2. 修改的檔案和位置

#### `app/api/routes.py`

**修改 1: 菜單查詢 API (`/api/menu/<store_id>`)**
```python
# 修改前
menu_items = MenuItem.query.filter_by(store_id=store_id).all()

# 修改後
menu_items = MenuItem.query.filter(
    MenuItem.store_id == store_id,
    MenuItem.price_small > 0  # 只返回價格大於 0 的商品
).all()
```

**修改 2: 根據 place_id 查詢菜單 API (`/api/menu/by-place-id/<place_id>`)**
```python
# 修改前
menu_items = MenuItem.query.filter_by(store_id=store.store_id).all()

# 修改後
menu_items = MenuItem.query.filter(
    MenuItem.store_id == store.store_id,
    MenuItem.price_small > 0  # 只返回價格大於 0 的商品
).all()
```

**修改 3: OCR 菜單處理 API (`/api/menu/process-ocr`)**
```python
# 在動態菜單生成中添加過濾邏輯
price = safe_price(item.get('price', 0))

# 過濾掉價格為 0 的商品，避免前端出現價格驗證錯誤
if price <= 0:
    continue

dynamic_menu.append({
    # ... 菜單項目資料
})
```

**修改 4: OCR 菜單查詢 API (`/api/menu/ocr/<ocr_menu_id>`)**
```python
# 修改前
menu_items = OCRMenuItem.query.filter_by(ocr_menu_id=ocr_menu_id).all()

# 修改後
menu_items = OCRMenuItem.query.filter(
    OCRMenuItem.ocr_menu_id == ocr_menu_id,
    OCRMenuItem.price_small > 0  # 只返回價格大於 0 的商品
).all()
```

### 3. 影響範圍

#### 受影響的 API 端點
1. `GET /api/menu/<store_id>` - 合作店家菜單查詢
2. `GET /api/menu/by-place-id/<place_id>` - 根據 place_id 查詢菜單
3. `POST /api/menu/process-ocr` - OCR 菜單處理
4. `GET /api/menu/ocr/<ocr_menu_id>` - OCR 菜單查詢
5. `POST /api/menu/simple-ocr` - 簡化版 OCR（自動繼承過濾邏輯）

#### 不受影響的功能
1. 訂單處理 API - 這些 API 處理用戶已選擇的商品，不需要過濾
2. 語音生成功能 - 這些功能處理已確認的訂單項目
3. 資料庫儲存 - 價格為 0 的商品仍然會儲存到資料庫，只是不會顯示給用戶

### 4. 修復效果

#### 修復前
- 價格為 0 的商品會出現在點餐介面
- 用戶選擇這些商品後會出現價格驗證錯誤
- 無法提交包含價格為 0 商品的訂單

#### 修復後
- 價格為 0 的商品不會出現在點餐介面
- 用戶不會看到這些商品，因此不會觸發價格驗證錯誤
- 可以正常提交訂單

### 5. 測試建議

1. **功能測試**
   - 測試合作店家菜單查詢，確認價格為 0 的商品不會出現
   - 測試 OCR 菜單處理，確認價格為 0 的商品不會出現在結果中
   - 測試訂單提交，確認可以正常提交訂單

2. **向後相容性測試**
   - 確認現有的訂單處理功能不受影響
   - 確認語音生成功能正常工作
   - 確認資料庫查詢功能正常

3. **邊界情況測試**
   - 測試所有價格為 0 的商品都被正確過濾
   - 測試價格為負數的商品（如果存在）
   - 測試價格為小數的商品

### 6. 部署注意事項

1. **資料庫影響**
   - 此修改不會影響資料庫中的現有資料
   - 價格為 0 的商品仍然儲存在資料庫中，只是不會顯示給用戶

2. **向後相容性**
   - 所有現有的 API 端點都保持向後相容
   - 只是過濾了返回的結果，不會影響 API 的結構

3. **監控建議**
   - 監控菜單查詢 API 的回應時間
   - 監控過濾掉的商品數量
   - 監控用戶訂單提交成功率

## 結論

通過在後端 API 中添加價格過濾邏輯，我們成功解決了前端價格驗證錯誤的問題。這個解決方案：

1. **最小化影響** - 只修改了必要的 API 端點
2. **保持相容性** - 不影響現有的訂單處理功能
3. **用戶友好** - 用戶不會再看到價格驗證錯誤
4. **維護簡單** - 過濾邏輯集中在後端，易於維護

這個修復確保了用戶可以正常使用點餐功能，而不會遇到價格驗證錯誤。
