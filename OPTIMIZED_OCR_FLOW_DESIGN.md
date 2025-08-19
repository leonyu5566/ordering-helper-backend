# 優化 OCR 流程設計

## 🎯 設計目標

### 核心概念
非合作店家直接進入拍照模式 → OCR 辨識 → 即時翻譯 → 點餐 → 生成摘要 → LINE Bot → 統一儲存資料庫

### 優點
1. **使用者體驗優化**：減少等待時間，流程更順暢
2. **資料一致性**：中文和外文菜單來源明確
3. **簡化架構**：避免複雜的資料庫查詢邏輯

## 📋 詳細流程設計

### 1. 前端流程
```
用戶選擇非合作店家 → 直接進入拍照模式 → 上傳菜單圖片
```

### 2. OCR 處理階段
```
POST /api/menu/process-ocr
```
**處理邏輯**：
- 使用 Gemini API 進行 OCR 辨識
- 即時翻譯為使用者語言
- 暫存在後端記憶體中（不立即儲存資料庫）
- 返回 OCR 結果和翻譯結果

**回應格式**：
```json
{
  "ocr_menu_id": "temp_12345",
  "items": [
    {
      "id": "temp_item_1",
      "name": {
        "original": "爆冰濃縮",
        "translated": "Super Ice Espresso"
      },
      "price": 74
    }
  ],
  "store_name": {
    "original": "劉漣麵 新店光明總店",
    "translated": "Liu Lian Noodles"
  }
}
```

### 3. 點餐階段
```
POST /api/orders/ocr-optimized
```
**處理邏輯**：
- 接收用戶選擇的菜品
- 使用暫存的 OCR 資料生成摘要
- 生成語音檔案
- 發送到 LINE Bot

### 4. 資料庫儲存階段
```
POST /api/orders/save-ocr-data
```
**處理邏輯**：
- 將中文菜單儲存到 `ocr_menu_items`
- 將外文菜單儲存到 `ocr_menu_translations`
- 將訂單儲存到 `orders` 和 `order_items`
- 將摘要儲存到 `order_summaries`

## 🗄️ 資料庫結構對應

### 1. ocr_menu_items 表
```sql
INSERT INTO ocr_menu_items (
    ocr_menu_id, 
    item_name,           -- 中文菜名
    price_small, 
    translated_desc      -- 外文菜名
) VALUES (?, ?, ?, ?)
```

### 2. ocr_menu_translations 表
```sql
INSERT INTO ocr_menu_translations (
    menu_item_id,        -- 對應 ocr_menu_items.ocr_menu_item_id
    lang_code,           -- 使用者語言 (en, ja, ko 等)
    description          -- 外文菜名
) VALUES (?, ?, ?)
```

### 3. orders 表
```sql
INSERT INTO orders (
    user_id, 
    store_id, 
    total_amount, 
    status
) VALUES (?, ?, ?, 'pending')
```

### 4. order_items 表
```sql
INSERT INTO order_items (
    order_id, 
    temp_item_id,        -- 格式: "ocr_數字"
    temp_item_name,      -- 中文菜名
    temp_item_price, 
    quantity_small, 
    subtotal, 
    is_temp_item
) VALUES (?, ?, ?, ?, ?, ?, 1)
```

### 5. order_summaries 表
```sql
INSERT INTO order_summaries (
    order_id, 
    ocr_menu_id, 
    chinese_summary,     -- 中文摘要
    user_language_summary, -- 外文摘要
    user_language, 
    total_amount
) VALUES (?, ?, ?, ?, ?, ?)
```

## 🔧 API 端點設計

### 1. 優化 OCR 處理
```python
@api_bp.route('/menu/process-ocr-optimized', methods=['POST'])
def process_menu_ocr_optimized():
    """
    優化的 OCR 處理流程
    - 直接 OCR 辨識
    - 即時翻譯
    - 暫存結果
    - 不立即儲存資料庫
    """
    # 1. OCR 辨識
    # 2. 即時翻譯
    # 3. 暫存結果
    # 4. 返回結果
```

### 2. 優化訂單建立
```python
@api_bp.route('/orders/ocr-optimized', methods=['POST'])
def create_ocr_order_optimized():
    """
    優化的 OCR 訂單建立
    - 使用暫存的 OCR 資料
    - 生成摘要和語音
    - 發送到 LINE Bot
    - 不立即儲存資料庫
    """
    # 1. 使用暫存資料
    # 2. 生成摘要
    # 3. 生成語音
    # 4. 發送 LINE Bot
```

### 3. 資料庫儲存
```python
@api_bp.route('/orders/save-ocr-data', methods=['POST'])
def save_ocr_data():
    """
    統一儲存 OCR 資料到資料庫
    - 儲存中文菜單
    - 儲存外文菜單
    - 儲存訂單
    - 儲存摘要
    """
    # 1. 儲存 ocr_menu_items
    # 2. 儲存 ocr_menu_translations
    # 3. 儲存 orders
    # 4. 儲存 order_items
    # 5. 儲存 order_summaries
```

## 📊 資料流程圖

```
前端拍照 → OCR 辨識 → 即時翻譯 → 暫存資料
    ↓
用戶點餐 → 生成摘要 → 生成語音 → 發送 LINE Bot
    ↓
統一儲存 → ocr_menu_items + ocr_menu_translations + orders + order_summaries
```

## 🎯 實作優勢

### 1. **效能優化**
- 減少資料庫查詢次數
- 即時翻譯，無需等待
- 並行處理 OCR 和翻譯

### 2. **資料一致性**
- 中文菜單：直接來自 OCR 結果
- 外文菜單：直接來自 Gemini API 翻譯
- 避免資料庫查詢的複雜性

### 3. **使用者體驗**
- 流程更順暢
- 等待時間更短
- 即時反饋

### 4. **維護性**
- 邏輯清晰
- 職責分離
- 易於除錯

## 🚀 實作步驟

1. **修改前端**：非合作店家直接進入拍照模式
2. **新增 API 端點**：`/menu/process-ocr-optimized`
3. **新增訂單端點**：`/orders/ocr-optimized`
4. **新增儲存端點**：`/orders/save-ocr-data`
5. **修改 LINE Bot 邏輯**：在發送後觸發資料庫儲存
6. **測試驗證**：確保資料正確儲存

這個設計完全符合你的想法，能夠解決當前問題並大幅優化使用者體驗！
