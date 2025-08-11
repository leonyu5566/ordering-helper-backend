# OCR API 合併功能使用指南

## 概述

我們已經成功將簡化版 OCR 端點的功能整合到主要端點中，透過 `simple_mode` 參數來控制回應格式。這樣既保持了向後相容性，又統一了程式碼結構。

## 主要端點

### `/api/menu/process-ocr`

**功能**：處理菜單圖片 OCR 和翻譯（支援兩種模式）

**方法**：`POST`

**參數**：
- `image`：圖片檔案（必需）
- `store_id`：店家ID（必需）
- `user_id`：使用者ID（可選）
- `lang`：目標語言（預設：'en'）
- `simple_mode`：簡化模式（可選，預設：false）

## 使用方式

### 1. 完整模式（預設）

```bash
POST /api/menu/process-ocr
Content-Type: multipart/form-data

# 表單資料
image: [圖片檔案]
store_id: 123
user_id: 456
lang: en
simple_mode: false  # 或省略
```

**回應格式**：
```json
{
  "message": "菜單處理成功",
  "processing_id": 789,
  "store_info": {...},
  "menu_items": [
    {
      "temp_id": "temp_789_0",
      "id": "temp_789_0",
      "original_name": "原菜名",
      "translated_name": "Translated Name",
      "en_name": "Translated Name",
      "price": 100,
      "price_small": 100,
      "price_large": 100,
      "description": "描述",
      "category": "分類",
      "image_url": "/static/images/default-dish.png",
      "imageUrl": "/static/images/default-dish.png",
      "inventory": 999,
      "available": true,
      "processing_id": 789
    }
  ],
  "total_items": 1,
  "target_language": "en",
  "processing_notes": "..."
}
```

### 2. 簡化模式

```bash
POST /api/menu/process-ocr
Content-Type: multipart/form-data

# 表單資料
image: [圖片檔案]
store_id: 123
user_id: 456
lang: en
simple_mode: true
```

**回應格式**：
```json
{
  "success": true,
  "menu_items": [
    {
      "id": "ocr_789_0",
      "name": "原菜名",
      "translated_name": "Translated Name",
      "price": 100,
      "description": "描述",
      "category": "分類"
    }
  ],
  "store_name": "店家名稱",
  "target_language": "en",
  "processing_notes": "...",
  "ocr_menu_id": 789,
  "saved_to_database": true
}
```

## 向後相容性

### 舊的簡化版端點

```bash
POST /api/menu/simple-ocr
```

**注意**：此端點已被標記為棄用（@deprecated），但仍然可用。它會自動重定向到主要端點的簡化模式。

**建議**：新專案請直接使用 `/api/menu/process-ocr?simple_mode=true`

## 參數對照表

| 參數 | 完整模式 | 簡化模式 | 說明 |
|------|----------|----------|------|
| `image` | ✅ | ✅ | 圖片檔案（必需） |
| `store_id` | ✅ | ✅ | 店家ID（必需） |
| `user_id` | ✅ | ✅ | 使用者ID（可選） |
| `lang` | ✅ | ✅ | 目標語言（預設：'en'） |
| `simple_mode` | ❌ | ✅ | 簡化模式開關 |

## 菜單項目欄位對照表

| 欄位 | 完整模式 | 簡化模式 | 說明 |
|------|----------|----------|------|
| `id` | ✅ | ✅ | 項目ID |
| `name` | ❌ | ✅ | 菜名（簡化模式） |
| `original_name` | ✅ | ❌ | 原始菜名 |
| `translated_name` | ✅ | ✅ | 翻譯後菜名 |
| `price` | ✅ | ✅ | 價格 |
| `price_small` | ✅ | ❌ | 小份價格 |
| `price_large` | ✅ | ❌ | 大份價格 |
| `description` | ✅ | ✅ | 描述 |
| `category` | ✅ | ✅ | 分類 |
| `image_url` | ✅ | ❌ | 圖片URL |
| `inventory` | ✅ | ❌ | 庫存 |
| `available` | ✅ | ❌ | 是否可用 |

## 錯誤處理

兩種模式都使用相同的錯誤處理邏輯：

- **400**：參數錯誤（如缺少檔案、店家ID等）
- **422**：可恢復的錯誤（如 JSON 解析失敗）
- **500**：系統錯誤

## 資料庫儲存

兩種模式都會將資料儲存到資料庫：
- `ocr_menus` 表：儲存菜單基本資訊
- `ocr_menu_items` 表：儲存菜單項目

## 遷移建議

### 從舊端點遷移

1. **立即遷移**：
   ```bash
   # 舊方式
   POST /api/menu/simple-ocr
   
   # 新方式
   POST /api/menu/process-ocr?simple_mode=true
   ```

2. **漸進式遷移**：
   - 舊端點仍然可用
   - 新功能使用新端點
   - 逐步更新前端程式碼

### 前端更新

```javascript
// 舊方式
const response = await fetch('/api/menu/simple-ocr', {
  method: 'POST',
  body: formData
});

// 新方式
const response = await fetch('/api/menu/process-ocr?simple_mode=true', {
  method: 'POST',
  body: formData
});
```

## 優勢

1. **功能統一**：所有 OCR 功能集中在一個端點
2. **向後相容**：舊的簡化版端點仍然可用
3. **靈活控制**：透過參數控制回應格式
4. **維護簡化**：只需要維護一個端點的邏輯
5. **程式碼重用**：避免重複的 OCR 處理邏輯

## 注意事項

1. **參數名稱**：簡化模式使用 `simple_mode=true`，不是 `simple=true`
2. **回應格式**：兩種模式的回應結構不同，前端需要相應調整
3. **向後相容**：舊端點會在未來版本中移除，建議盡早遷移
4. **錯誤處理**：兩種模式使用相同的錯誤處理邏輯

## 測試建議

1. **功能測試**：測試兩種模式的正常流程
2. **錯誤測試**：測試各種錯誤情況
3. **向後相容測試**：確保舊端點仍然正常工作
4. **效能測試**：比較兩種模式的效能差異
