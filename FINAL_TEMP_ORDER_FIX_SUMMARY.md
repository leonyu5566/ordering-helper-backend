# 臨時訂單修復總結

## 問題描述

用戶在使用非合作店家的拍照功能時，遇到以下錯誤：

```
訂單送出失敗: 資料驗證失敗:
項目 1: 找不到菜單項目 ID temp_36_0
```

## 問題原因分析

1. **前端發送了臨時ID**：`temp_36_0` 這樣的臨時菜單項目ID
2. **後端期望正式ID**：`/api/orders` 端點期望資料庫中存在的正式 `menu_item_id`
3. **資料庫約束**：`OrderItem` 表的 `menu_item_id` 欄位有外鍵約束，無法接受臨時ID

## 解決方案

### 方法1：修改資料庫結構（已嘗試但未成功）

- 添加新的欄位：`temp_item_id`, `temp_item_name`, `temp_item_price`, `is_temp_item`
- 修改 `menu_item_id` 為可空
- 需要資料庫遷移

### 方法2：創建臨時 MenuItem 記錄（最終採用）

- 當遇到 `temp_*` 格式的ID時，動態創建 `MenuItem` 記錄
- 使用現有的資料庫結構，不需要修改表結構
- 更簡單且向後相容

## 實施的修復

### 1. 修改訂單API邏輯 (`app/api/routes.py`)

```python
# 檢查是否為臨時菜單項目（以 temp_ 開頭）
if menu_item_id.startswith('temp_'):
    # 處理臨時菜單項目
    price = item_data.get('price') or item_data.get('price_small') or item_data.get('price_unit') or 0
    item_name = item_data.get('item_name') or item_data.get('name') or item_data.get('original_name') or f"項目 {i+1}"
    
    # 為臨時項目創建一個臨時的 MenuItem 記錄
    try:
        # 檢查是否已經有對應的臨時菜單項目
        temp_menu_item = MenuItem.query.filter_by(item_name=item_name).first()
        
        if not temp_menu_item:
            # 創建新的臨時菜單項目
            from app.models import Menu
            
            # 找到或創建一個臨時菜單
            temp_menu = Menu.query.filter_by(store_id=data['store_id']).first()
            if not temp_menu:
                temp_menu = Menu(store_id=data['store_id'], version=1)
                db.session.add(temp_menu)
                db.session.flush()
            
            temp_menu_item = MenuItem(
                menu_id=temp_menu.menu_id,
                item_name=item_name,
                price_small=int(price),
                price_big=int(price)  # 使用相同價格
            )
            db.session.add(temp_menu_item)
            db.session.flush()  # 獲取 menu_item_id
        
        # 使用臨時菜單項目的 ID
        order_items_to_create.append(OrderItem(
            menu_item_id=temp_menu_item.menu_item_id,
            quantity_small=quantity,
            subtotal=subtotal
        ))
        
    except Exception as e:
        validation_errors.append(f"項目 {i+1}: 創建臨時菜單項目失敗 - {str(e)}")
        continue
```

### 2. 保持資料庫模型不變 (`app/models.py`)

```python
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    order_item_id = db.Column(db.BigInteger, primary_key=True)
    order_id = db.Column(db.BigInteger, db.ForeignKey('orders.order_id'), nullable=False)
    menu_item_id = db.Column(db.BigInteger, db.ForeignKey('menu_items.menu_item_id'), nullable=False)
    quantity_small = db.Column(db.Integer, nullable=False, default=0)
    subtotal = db.Column(db.Integer, nullable=False)
```

## 部署狀態

### 已完成的修復
- ✅ 修改了訂單API邏輯
- ✅ 移除了不必要的資料庫欄位
- ✅ 代碼已推送到 GitHub

### 待確認的狀態
- ⏳ 等待 Cloud Run 部署完成
- ⏳ 等待測試結果

## 測試案例

### 臨時訂單測試
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

### 預期結果
- ✅ 臨時訂單成功創建
- ✅ 臨時 MenuItem 記錄被創建
- ✅ 訂單項目正確關聯

## 優點

1. **向後相容**：不需要修改現有資料庫結構
2. **簡單實施**：只需要修改API邏輯
3. **資料完整性**：臨時項目會正確記錄在資料庫中
4. **可追溯性**：可以通過 MenuItem 表查詢臨時項目

## 注意事項

1. **重複項目**：相同名稱的臨時項目會重用現有的 MenuItem 記錄
2. **資料清理**：可以考慮定期清理未使用的臨時 MenuItem 記錄
3. **性能考慮**：每次臨時訂單都會查詢/創建 MenuItem 記錄

## 相關檔案

- `app/api/routes.py` - 修改的API邏輯
- `app/models.py` - 保持不變的資料庫模型
- `test_production_fix.py` - 測試腳本
- `TEMP_ORDER_FIX_GUIDE.md` - 詳細修復指南
- `FINAL_TEMP_ORDER_FIX_SUMMARY.md` - 本總結

## 下一步

1. 等待部署完成
2. 執行測試腳本驗證修復
3. 監控生產環境的訂單創建
4. 考慮添加資料清理機制 