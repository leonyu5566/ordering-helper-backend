# OCR 菜單和訂單摘要儲存功能

## 功能概述

新增了將 OCR 菜單和訂單摘要自動儲存到 Cloud MySQL 資料庫的功能。當使用者完成點餐後，系統會：

1. 生成摘要和語音檔
2. 回傳給使用者的 LINE Bot
3. **新增：** 自動將 OCR 菜單和訂單摘要儲存到資料庫

## 新增的資料庫模型

### OrderSummary 模型

```python
class OrderSummary(db.Model):
    """訂單摘要儲存模型"""
    __tablename__ = 'order_summaries'
    
    summary_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(db.BigInteger, db.ForeignKey('orders.order_id'), nullable=False)
    ocr_menu_id = db.Column(db.BigInteger, db.ForeignKey('ocr_menus.ocr_menu_id'), nullable=True)
    chinese_summary = db.Column(db.Text, nullable=False)  # 中文訂單摘要
    user_language_summary = db.Column(db.Text, nullable=False)  # 使用者語言訂單摘要
    user_language = db.Column(db.String(10), nullable=False)  # 使用者語言代碼
    total_amount = db.Column(db.Integer, nullable=False)  # 訂單總金額
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
```

## 新增的核心函數

### save_ocr_menu_and_summary_to_database()

```python
def save_ocr_menu_and_summary_to_database(
    order_id, 
    ocr_items, 
    chinese_summary, 
    user_language_summary, 
    user_language, 
    total_amount, 
    user_id, 
    store_name=None
):
    """
    將 OCR 菜單和訂單摘要儲存到 Cloud MySQL 資料庫
    
    Returns:
        dict: 包含 ocr_menu_id 和 summary_id 的結果
    """
```

## 整合點

### 1. send_complete_order_notification()

在 `app/api/helpers.py` 中的 `send_complete_order_notification()` 函數新增了：

- 檢查是否為 OCR 菜單訂單
- 自動儲存 OCR 菜單和訂單摘要到資料庫
- 不影響主要流程，即使儲存失敗也會繼續執行

### 2. send_complete_order_notification_optimized()

在 `app/api/helpers.py` 中的 `send_complete_order_notification_optimized()` 函數也新增了相同的功能。

### 3. simple_order()

在 `app/api/routes.py` 中的 `simple_order()` 函數新增了：

- 在發送 LINE Bot 通知後
- 自動儲存 OCR 菜單和訂單摘要到資料庫

### 4. create_temp_order()

在 `app/api/routes.py` 中的 `create_temp_order()` 函數也新增了相同的功能。

## 資料庫遷移

### 自動建立表格

系統會自動檢查並建立 `order_summaries` 表格，包含：

- 主鍵：`summary_id`
- 外鍵關聯：`order_id` → `orders.order_id`
- 外鍵關聯：`ocr_menu_id` → `ocr_menus.ocr_menu_id`
- 必要欄位：`chinese_summary`, `user_language_summary`, `user_language`, `total_amount`
- 時間戳記：`created_at`

### 表格結構

```sql
CREATE TABLE order_summaries (
    summary_id BIGINT NOT NULL AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    ocr_menu_id BIGINT NULL,
    chinese_summary TEXT NOT NULL,
    user_language_summary TEXT NOT NULL,
    user_language VARCHAR(10) NOT NULL,
    total_amount INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (summary_id),
    FOREIGN KEY (order_id) REFERENCES orders (order_id),
    FOREIGN KEY (ocr_menu_id) REFERENCES ocr_menus (ocr_menu_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='訂單摘要';
```

## 使用方式

### 自動觸發

功能會自動觸發，無需手動呼叫。當以下條件滿足時：

1. 訂單包含 `original_name` 欄位的項目（OCR 菜單特徵）
2. 訂單通知已成功發送到 LINE Bot
3. 系統會自動儲存 OCR 菜單和訂單摘要

### 手動呼叫

如果需要手動儲存，可以呼叫：

```python
from app.api.helpers import save_ocr_menu_and_summary_to_database

result = save_ocr_menu_and_summary_to_database(
    order_id=123,
    ocr_items=[...],
    chinese_summary="中文摘要",
    user_language_summary="English Summary",
    user_language="en",
    total_amount=150,
    user_id=456,
    store_name="店家名稱"
)
```

## 錯誤處理

- 儲存失敗不會影響主要的點餐流程
- 所有錯誤都會記錄到日誌中
- 系統會自動回滾資料庫交易

## 測試

使用 `test_ocr_storage.py` 腳本來測試功能：

```bash
python3 test_ocr_storage.py
```

## 注意事項

1. **效能考量**：儲存操作在背景執行，不影響使用者體驗
2. **資料完整性**：使用資料庫交易確保資料一致性
3. **向後相容**：不影響現有的點餐功能
4. **錯誤容忍**：即使儲存失敗，主要功能仍正常運作

## 日誌記錄

系統會記錄詳細的儲存過程：

```
🔄 檢測到 OCR 菜單訂單，開始儲存到資料庫...
✅ 已建立 OCR 菜單記錄: 123
✅ 已儲存 2 個 OCR 菜單項目
✅ 已建立訂單摘要記錄: 456
🎉 成功儲存 OCR 菜單和訂單摘要到資料庫
   OCR 菜單 ID: 123
   訂單摘要 ID: 456
```
