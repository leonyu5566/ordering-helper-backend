# Store ID Null 錯誤修復指南

## 問題描述

在使用 LIFF 模擬器測試時，遇到以下錯誤：

```
訂單送出失敗: 資料驗證失敗:
項目 1: 創建臨時菜單項目失敗 - (pymysql.err.IntegrityError) (1048, "Column 'store_id' cannot be null")
[SQL: INSERT INTO menus (store_id, version, created_at) VALUES (%(store_id)s, %(version)s, %(created_at)s)]
[parameters: {'store_id': None, 'version': 1, 'created_at': datetime.datetime(2025, 8, 5, 9, 48, 5, 411975)}]
```

## 問題原因

1. **前端在模擬環境中沒有正確的 `store_id`**：
   - 在 LIFF 模擬器中測試時，URL 沒有 `store_id` 參數
   - `getCurrentStoreId()` 函數返回預設值 `1`
   - 但資料庫中可能沒有 `store_id=1` 的店家記錄

2. **後端嘗試創建 Menu 記錄時失敗**：
   - 當處理臨時菜單項目時，後端嘗試創建 Menu 記錄
   - 但 `store_id=1` 對應的 Store 記錄不存在
   - 觸發外鍵約束錯誤：`Column 'store_id' cannot be null`

## 解決方案

### 1. 修改後端邏輯（已完成）

在 `app/api/routes.py` 的 `create_order()` 函數中，添加了自動創建預設店家的邏輯：

```python
# 確保店家存在，如果不存在則創建預設店家
store_id = data.get('store_id')
if not store_id:
    # 如果沒有 store_id，創建一個預設店家
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
```

### 2. 初始化預設資料（推薦執行）

運行預設資料初始化腳本：

```bash
python tools/init_default_data.py
```

這個腳本會：
- 創建預設店家（store_id 會自動分配）
- 創建對應的預設菜單
- 創建一些測試用的菜單項目
- 確保語言資料存在

### 3. 前端改進（可選）

修改 `frontend_order_example.js` 中的 `getCurrentStoreId()` 函數：

```javascript
function getCurrentStoreId() {
    // 從 URL 參數或全域變數取得
    const urlParams = new URLSearchParams(window.location.search);
    const storeId = urlParams.get('store_id');
    
    if (storeId) {
        return parseInt(storeId);
    }
    
    // 如果沒有 store_id 參數，返回 null 讓後端處理
    return null;
}
```

然後修改訂單提交邏輯：

```javascript
const orderData = {
    line_user_id: lineUserId,
    store_id: getCurrentStoreId(), // 可能為 null
    language: getUserLanguage(),
    items: orderItems,
    total: total
};
```

## 測試方法

### 1. 在模擬器中測試

1. 直接在 Azure Static Web Apps 打開頁面
2. 選擇一些商品
3. 點擊「送出訂單」
4. 應該不再出現 `store_id` 錯誤

### 2. 使用 URL 參數測試

1. 在 URL 中添加 `?store_id=1`
2. 重複上述測試步驟
3. 應該能正常提交訂單

### 3. 檢查資料庫

```bash
# 檢查店家資料
python tools/check_database.py

# 查看店家列表
python -c "
from app import create_app, db
from app.models import Store
app = create_app()
with app.app_context():
    stores = Store.query.all()
    for store in stores:
        print(f'Store ID: {store.store_id}, Name: {store.store_name}')
"
```

## 預期結果

修復後，系統應該能夠：

1. **在模擬環境中正常運行**：即使沒有 `store_id` 參數也能正常提交訂單
2. **自動創建預設店家**：當需要時自動創建預設店家記錄
3. **向後相容**：支援帶有 `store_id` 參數的正常流程
4. **錯誤處理**：提供清晰的錯誤訊息而不是資料庫約束錯誤

## 注意事項

1. **預設店家**：系統會創建一個名為「預設店家」的記錄，用於測試環境
2. **資料庫變更**：會自動創建必要的店家、菜單和菜單項目記錄
3. **生產環境**：在正式環境中，應該通過正常的 LIFF 流程獲取正確的 `store_id`

## 相關檔案

- `app/api/routes.py` - 修改的訂單創建邏輯
- `tools/init_default_data.py` - 預設資料初始化腳本
- `frontend_order_example.js` - 前端範例代碼
- `app/models.py` - 資料庫模型定義 