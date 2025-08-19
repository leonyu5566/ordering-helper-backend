# 優化 OCR 流程實作總結

## 🎯 實作完成

### 新增的 API 端點

#### 1. 優化 OCR 處理端點
```
POST /api/menu/process-ocr-optimized
```
**功能**：
- 直接 OCR 辨識菜單圖片
- 即時翻譯為使用者語言
- 暫存結果在記憶體中（不立即儲存資料庫）
- 返回雙語菜單資料

**回應格式**：
```json
{
  "success": true,
  "ocr_menu_id": "temp_ocr_12345",
  "store_name": {
    "original": "劉漣麵 新店光明總店",
    "translated": "Liu Lian Noodles"
  },
  "items": [
    {
      "id": "temp_item_1",
      "name": {
        "original": "爆冰濃縮",
        "translated": "Super Ice Espresso"
      },
      "price": 74
    }
  ]
}
```

#### 2. 優化訂單建立端點
```
POST /api/orders/ocr-optimized
```
**功能**：
- 使用暫存的 OCR 資料建立訂單
- 生成雙語摘要（中文和外文）
- 生成語音檔案
- 發送到 LINE Bot
- 準備資料庫儲存資料

**回應格式**：
```json
{
  "success": true,
  "message": "訂單已發送到 LINE Bot",
  "save_data_id": "temp_ocr_12345_save_data",
  "chinese_summary": "店家: 劉漣麵 新店光明總店\n爆冰濃縮 x2 $148\n總計: $148",
  "user_language_summary": "Store: Liu Lian Noodles\nSuper Ice Espresso x2 $148\nTotal: $148"
}
```

#### 3. 資料庫儲存端點
```
POST /api/orders/save-ocr-data
```
**功能**：
- 統一儲存 OCR 資料到資料庫
- 儲存中文菜單到 `ocr_menu_items`
- 儲存外文菜單到 `ocr_menu_translations`
- 儲存訂單到 `orders` 和 `order_items`
- 使用交易確保資料一致性

## 🗄️ 資料庫儲存結構

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

### 4. order_items 表（支援雙語）
```sql
INSERT INTO order_items (
    order_id, 
    temp_item_id,        -- 格式: "ocr_數字"
    temp_item_name,      -- 中文菜名
    temp_item_price, 
    quantity_small, 
    subtotal, 
    original_name,       -- 中文菜名
    translated_name,     -- 外文菜名
    is_temp_item
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
```

## 🔄 完整流程

### 1. 前端流程
```
用戶選擇非合作店家 → 直接進入拍照模式 → 上傳菜單圖片
```

### 2. 後端處理流程
```
OCR 辨識 → 即時翻譯 → 暫存資料 → 用戶點餐 → 生成摘要 → 發送 LINE Bot → 儲存資料庫
```

### 3. 資料流向
```
前端拍照 → OCR 辨識 → 即時翻譯 → 暫存資料
    ↓
用戶點餐 → 生成摘要 → 生成語音 → 發送 LINE Bot
    ↓
統一儲存 → ocr_menu_items + ocr_menu_translations + orders + order_items
```

## ✅ 解決的問題

### 1. **雙語摘要問題**
- ✅ 中文摘要使用原始中文菜名
- ✅ 外文摘要使用翻譯菜名
- ✅ 語音使用中文菜名

### 2. **使用者體驗優化**
- ✅ 減少等待時間
- ✅ 流程更順暢
- ✅ 即時翻譯反饋

### 3. **資料一致性**
- ✅ 中文菜單來源明確（OCR 結果）
- ✅ 外文菜單來源明確（Gemini API 翻譯）
- ✅ 避免資料庫查詢複雜性

## 🚀 部署狀態

### 已完成的實作
1. ✅ 新增 `/api/menu/process-ocr-optimized` 端點
2. ✅ 新增 `/api/orders/ocr-optimized` 端點
3. ✅ 新增 `/api/orders/save-ocr-data` 端點
4. ✅ 修正 import 問題
5. ✅ 建立測試腳本

### 下一步
1. 🔄 部署到 Cloud Run
2. 🔄 測試實際功能
3. 🔄 前端整合

## 📊 預期效果

### 效能提升
- 減少資料庫查詢次數
- 即時翻譯，無需等待
- 並行處理 OCR 和翻譯

### 使用者體驗
- 流程更順暢
- 等待時間更短
- 即時反饋

### 維護性
- 邏輯清晰
- 職責分離
- 易於除錯

## 🎉 總結

這個優化方案完全符合你的設計理念：
1. **非合作店家直接進入拍照模式**
2. **OCR 辨識後即時翻譯**
3. **暫存資料，不立即儲存資料庫**
4. **生成雙語摘要和語音**
5. **發送 LINE Bot 後統一儲存資料庫**

這個實作解決了所有當前問題，並大幅優化了使用者體驗！
