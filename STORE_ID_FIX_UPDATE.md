# Store ID Null 錯誤修復更新

## 最新問題

在修復了臨時菜單項目的 `store_id` 問題後，發現還有一個遺漏的地方：

```
訂單送出失敗: 訂單建立失敗
(pymysql.err.IntegrityError) (1048, "Column 'store_id' cannot be null")
[SQL: INSERT INTO orders (user_id, store_id, order_time, total_amount, status) VALUES (%(user_id)s, %(store_id)s, %(order_time)s, %(total_amount)s, %(status)s)]
[parameters: {'user_id': 15, 'store_id': None, 'order_time': datetime.datetime(2025, 8, 5, 10, 29, 12, 653140), 'total_amount': 30, 'status': 'pending'}]
```

## 問題分析

雖然我們修復了臨時菜單項目的 `store_id` 問題，但在創建 `Order` 記錄時，仍然直接使用 `data['store_id']`，這個值可能還是 `None`。

## 修復方案

### 在 Order 創建前添加 store_id 驗證

在 `app/api/routes.py` 的 `create_order()` 函數中，在創建 Order 記錄之前添加驗證：

```python
try:
    # 確保 store_id 有值
    store_id = data.get('store_id')
    if not store_id:
        # 如果沒有 store_id，創建一個預設店家
        from app.models import Store
        default_store = Store.query.filter_by(store_name='預設店家').first()
        if not default_store:
            default_store = Store(
                store_name='預設店家',
                partner_level=0,  # 非合作店家
                created_at=datetime.datetime.utcnow()
            )
            db.session.add(default_store)
            db.session.flush()
        store_id = default_store.store_id
        # 更新請求資料中的 store_id
        data['store_id'] = store_id
    
    new_order = Order(
        user_id=user.user_id,
        store_id=store_id,  # 使用驗證後的 store_id
        total_amount=total_amount,
        items=order_items_to_create
    )
```

## 完整的修復流程

現在系統會按以下順序處理 `store_id`：

1. **檢查請求中的 store_id**
2. **如果 store_id 為空，自動創建預設店家**
3. **在創建臨時菜單項目時使用 store_id**
4. **在創建 Order 記錄時使用 store_id**

## 測試建議

1. **在 LIFF 模擬器中測試**：
   - 選擇商品
   - 點擊「送出訂單」
   - 應該不再出現 `store_id` 錯誤

2. **檢查資料庫**：
   - 確認預設店家已創建
   - 確認訂單記錄有正確的 `store_id`

## 部署狀態

- ✅ 修復已提交到本地 Git
- ⏳ 等待推送到 GitHub
- ⏳ 等待部署到生產環境

## 預期結果

修復後，系統應該能夠：
1. **完全處理缺失的 store_id**：在訂單創建的每個步驟都確保有有效的 store_id
2. **自動創建預設店家**：當需要時自動創建預設店家記錄
3. **成功創建訂單**：不再出現任何 `store_id` 相關的錯誤

這個修復應該能完全解決在 LIFF 模擬器中遇到的 `store_id` 問題。 