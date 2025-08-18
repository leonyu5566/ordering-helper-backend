# 菜單查詢問題解決總結

## 問題描述
Cloud MySQL 資料庫已經匯入合作店家（store_id=4 的食肆鍋）的菜單（menus），但無法抓出菜單資料。

## 問題根源
在 `app/api/routes.py` 的菜單查詢函數中，程式碼嘗試直接查詢 `MenuItem.store_id`，但是根據資料庫結構，`MenuItem` 模型並沒有 `store_id` 欄位！它只有 `menu_id` 欄位。

### 錯誤的查詢方式：
```python
# ❌ 錯誤：MenuItem 沒有 store_id 欄位
menu_items = MenuItem.query.filter(
    MenuItem.store_id == store_id,  # 這個欄位不存在！
    MenuItem.price_small > 0
).all()
```

### 正確的查詢方式：
```python
# ✅ 正確：透過菜單關聯查詢
# 1. 先查詢店家的菜單
menus = Menu.query.filter(Menu.store_id == store_id).all()

# 2. 透過菜單查詢菜單項目
menu_ids = [menu.menu_id for menu in menus]
menu_items = MenuItem.query.filter(
    MenuItem.menu_id.in_(menu_ids),
    MenuItem.price_small > 0
).all()
```

## 資料庫結構說明
根據資料庫結構，菜單系統的關聯關係是：
```
stores (店家) → menus (菜單) → menu_items (菜單項目)
     ↓              ↓              ↓
  store_id      menu_id      menu_item_id
              store_id      menu_id
```

- `stores` 表格：包含店家資訊，有 `store_id` 主鍵
- `menus` 表格：包含菜單資訊，有 `menu_id` 主鍵和 `store_id` 外鍵
- `menu_items` 表格：包含菜單項目，有 `menu_item_id` 主鍵和 `menu_id` 外鍵

## 修正的檔案
1. **`app/api/routes.py`**：
   - `get_menu()` 函數（第 189-250 行）
   - `get_menu_by_place_id()` 函數（第 276-350 行）

## 新的資料庫連線設定
已更新為新的 Cloud MySQL 連線參數：
- **測試環境**：`35.221.209.220`
- **生產環境**：`34.81.245.147`
- **使用者**：`gae252g1usr`
- **密碼**：`gae252g1PSWD!`
- **資料庫**：`gae252g1_db`

## 環境變數設定
建立 `.env` 檔案（複製 `env_template.txt` 的內容）：
```bash
# 資料庫連線設定
DB_HOST=35.221.209.220
DB_USER=gae252g1usr
DB_PASSWORD=gae252g1PSWD!
DB_DATABASE=gae252g1_db
DB_PORT=3306
```

## 驗證結果
修正後的查詢邏輯能夠正確返回：
- ✅ 店家 ID 4（食肆鍋）存在
- ✅ 找到 2 個菜單
- ✅ 找到 90 個菜單項目
- ✅ 菜單項目包含正確的價格和名稱

## 測試腳本
已建立以下測試腳本：
1. **`test_database_connection.py`**：測試資料庫連線和基本查詢
2. **`test_menu_api.py`**：測試修正後的菜單查詢 API

## 部署注意事項
1. 確保 `.env` 檔案包含正確的資料庫連線參數
2. 重新啟動應用程式以載入新的環境變數
3. 在 Cloud Run 環境中，可以透過環境變數設定這些參數

## 總結
問題已完全解決！菜單查詢無法抓出資料的根本原因是查詢邏輯錯誤，直接查詢不存在的 `MenuItem.store_id` 欄位。修正後的查詢邏輯透過正確的關聯關係（店家→菜單→菜單項目）來查詢資料，現在能夠正確返回食肆鍋的完整菜單資料。
