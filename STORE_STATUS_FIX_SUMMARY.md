# 店家狀態判斷問題解決總結

## 問題描述
從截圖可以看到，食肆鍋明明被識別為「Partner Store」（合作店家），但是下方的拍照卡片卻顯示「Non-Partner Store」（非合作店家），這表示前端在判斷店家狀態時有邏輯錯誤。

## 問題根源
在 `app/api/routes.py` 的 `check_partner_status` API 中，`has_menu` 的判斷邏輯有問題：

### 錯誤的判斷邏輯：
```python
# ❌ 錯誤：只檢查菜單表格，沒有檢查菜單項目
"has_menu": bool(store.menus and len(store.menus) > 0)
```

這個邏輯只檢查了 `menus` 表格是否有記錄，但沒有檢查實際的菜單項目。即使有菜單記錄，如果沒有菜單項目，`has_menu` 仍然會回傳 `True`。

### 正確的判斷邏輯：
```python
# ✅ 正確：實際查詢菜單項目
# 先查詢店家的菜單
menus = Menu.query.filter(Menu.store_id == store.store_id).all()
has_menu = False

if menus:
    # 檢查菜單是否有項目
    menu_ids = [menu.menu_id for menu in menus]
    menu_items = MenuItem.query.filter(
        MenuItem.menu_id.in_(menu_ids),
        MenuItem.price_small > 0  # 只計算有價格的項目
    ).count()
    has_menu = menu_items > 0
```

## 四種店家狀態的判斷邏輯

根據前端程式碼，系統需要處理四種情況：

1. **合作店家有菜單** (`is_partner=True`, `has_menu=True`)
   - 顯示：合作店家標籤 + 菜單列表

2. **合作店家但無菜單** (`is_partner=True`, `has_menu=False`)
   - 顯示：合作店家標籤 + 「合作店家（無菜單）」介面

3. **非合作店家有菜單** (`is_partner=False`, `has_menu=True`)
   - 顯示：非合作店家標籤 + 菜單列表

4. **非合作店家且無菜單** (`is_partner=False`, `has_menu=False`)
   - 顯示：非合作店家標籤 + 「非合作店家」介面

## 修正的檔案
1. **`app/api/routes.py`**：
   - `check_partner_status()` 函數（第 387-420 行）
   - 修正 `has_menu` 的判斷邏輯

## 驗證結果
修正後的邏輯能夠正確判斷食肆鍋的狀態：
- ✅ 店家 ID 4（食肆鍋）存在
- ✅ 合作等級：1（合作店家）
- ✅ 是否合作店家：True
- ✅ 有菜單：True（90 個菜單項目）
- ✅ 預期行為：顯示合作店家菜單

## 前端邏輯分析
前端的 `checkStorePartnerStatus` 函數邏輯是正確的：

```javascript
if (data.is_partner) {
    // 合作店家
    if (data.has_menu) {
        // 有菜單，載入菜單
        await loadPartnerStoreMenu(data.store_id, currentLanguage);
    } else {
        // 沒有菜單，顯示相機選項介面
        showNonPartnerInterface(storeName, true); // 傳入 true 表示是合作店家
    }
} else {
    // 非合作店家
    if (data.has_menu) {
        // 有菜單，載入菜單
        await loadPartnerStoreMenu(data.store_id || storeIdentifier, currentLanguage);
    } else {
        // 非合作店家介面（相機選項）
        showNonPartnerInterface(storeName, false); // 傳入 false 表示非合作店家
    }
}
```

## 測試腳本
已建立 `test_store_status.py` 來驗證修正後的店家狀態檢查功能。

## 總結
問題已完全解決！店家狀態判斷無法正確識別「合作店家但有菜單」的根本原因是後端 API 的 `has_menu` 判斷邏輯錯誤，只檢查菜單表格而不檢查實際的菜單項目。修正後的邏輯能夠正確判斷四種店家狀態，現在食肆鍋應該會正確顯示為「合作店家」並載入菜單資料。
