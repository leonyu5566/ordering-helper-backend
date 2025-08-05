# 臨時訂單修復指南

## 問題描述

用戶在使用非合作店家的拍照功能時，遇到以下錯誤：

```
訂單送出失敗: 資料驗證失敗:
項目 1: 找不到菜單項目 ID temp_36_0
```

## 問題原因

1. **前端發送了臨時ID**：`temp_36_0` 這樣的臨時菜單項目ID
2. **後端期望正式ID**：`/api/orders` 端點期望資料庫中存在的正式 `menu_item_id`
3. **資料庫約束**：`OrderItem` 表的 `menu_item_id` 欄位有外鍵約束，無法接受臨時ID

## 解決方案

### 1. 修改資料庫結構

#### A. 更新 OrderItem 模型 (`app/models.py`)

```python
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    order_item_id = db.Column(db.BigInteger, primary_key=True)
    order_id = db.Column(db.BigInteger, db.ForeignKey('orders.order_id'), nullable=False)
    menu_item_id = db.Column(db.BigInteger, db.ForeignKey('menu_items.menu_item_id'), nullable=True)  # 改為可空
    quantity_small = db.Column(db.Integer, nullable=False, default=0)
    subtotal = db.Column(db.Integer, nullable=False)
    # 新增欄位用於臨時項目
    temp_item_id = db.Column(db.String(100), nullable=True)  # 臨時項目ID
    temp_item_name = db.Column(db.String(100), nullable=True)  # 臨時項目名稱
    temp_item_price = db.Column(db.Integer, nullable=True)  # 臨時項目價格
    is_temp_item = db.Column(db.Boolean, default=False)  # 是否為臨時項目
```

#### B. 執行資料庫遷移

```bash
# 運行遷移腳本
python tools/migrate_order_items.py
```

### 2. 修改訂單API邏輯

#### A. 更新 `/api/orders` 端點 (`app/api/routes.py`)

修改 `create_order()` 函數，添加臨時項目處理邏輯：

```python
# 檢查是否為臨時菜單項目（以 temp_ 開頭）
if menu_item_id.startswith('temp_'):
    # 處理臨時菜單項目
    price = item_data.get('price') or item_data.get('price_small') or item_data.get('price_unit') or 0
    item_name = item_data.get('item_name') or item_data.get('name') or item_data.get('original_name') or f"項目 {i+1}"
    
    # 驗證價格
    try:
        price = float(price)
        if price < 0:
            validation_errors.append(f"項目 {i+1}: 價格不能為負數")
            continue
    except (ValueError, TypeError):
        validation_errors.append(f"項目 {i+1}: 價格格式錯誤，必須是數字")
        continue
    
    subtotal = int(price * quantity)
    total_amount += subtotal
    
    # 為臨時項目創建 OrderItem
    order_items_to_create.append(OrderItem(
        menu_item_id=None,  # 臨時項目沒有正式的 menu_item_id
        temp_item_id=menu_item_id,  # 使用臨時ID
        temp_item_name=item_name,
        temp_item_price=int(price),
        is_temp_item=True,
        quantity_small=quantity,
        subtotal=subtotal
    ))
else:
    # 處理正式菜單項目（原有邏輯）
    menu_item = MenuItem.query.get(menu_item_id)
    if not menu_item:
        validation_errors.append(f"項目 {i+1}: 找不到菜單項目 ID {menu_item_id}")
        continue
    
    # ... 原有邏輯
```

### 3. 部署步驟

#### A. 本地測試

1. **更新代碼**：
   ```bash
   git pull origin main
   ```

2. **執行遷移**：
   ```bash
   python tools/migrate_order_items.py
   ```

3. **測試修復**：
   ```bash
   python test_temp_order_fix.py
   ```

#### B. 生產環境部署

1. **推送代碼**：
   ```bash
   git add .
   git commit -m "Fix temp order support"
   git push origin main
   ```

2. **等待自動部署**：
   - GitHub Actions 會自動部署到 Cloud Run
   - 檢查部署狀態：https://github.com/leonyu5566/ordering-helper-backend/actions

3. **驗證修復**：
   ```bash
   python test_temp_order_fix.py
   ```

### 4. 測試案例

#### A. 臨時訂單測試

```json
{
  "store_id": 1,
  "line_user_id": null,
  "language": "zh",
  "items": [
    {
      "id": "temp_36_0",
      "item_name": "奶油經典夏威夷",
      "price": 115,
      "quantity": 1
    }
  ]
}
```

#### B. 正式訂單測試

```json
{
  "store_id": 1,
  "line_user_id": null,
  "language": "zh",
  "items": [
    {
      "menu_item_id": 1,
      "quantity": 1
    }
  ]
}
```

## 預期結果

### 修復前
- ❌ 臨時訂單失敗：`找不到菜單項目 ID temp_36_0`
- ✅ 正式訂單正常

### 修復後
- ✅ 臨時訂單成功：支援 `temp_*` 格式的ID
- ✅ 正式訂單正常：繼續支援正式 `menu_item_id`

## 注意事項

1. **向後相容**：修復不會影響現有的正式訂單功能
2. **資料完整性**：臨時項目會正確記錄在資料庫中
3. **錯誤處理**：提供詳細的驗證錯誤訊息
4. **測試覆蓋**：包含臨時和正式訂單的測試案例

## 相關檔案

- `app/models.py` - 資料庫模型
- `app/api/routes.py` - API 端點
- `tools/migrate_order_items.py` - 資料庫遷移腳本
- `test_temp_order_fix.py` - 測試腳本
- `TEMP_ORDER_FIX_GUIDE.md` - 本指南 