# OCR菜單流程修改說明

## 修改後的流程

根據您的需求，我們已經修改了OCR菜單的處理流程，現在按照以下順序進行：

### 1. OCR菜單先存到資料庫
- **端點**: `POST /api/menu/process-ocr`
- **功能**: 當使用者上傳菜單圖片時，系統會：
  - 使用Gemini API進行OCR辨識
  - 將辨識結果儲存到 `ocr_menus` 和 `ocr_menu_items` 表
  - 返回OCR菜單ID供後續使用
- **回應**: 包含 `ocr_menu_id` 和 `saved_to_database: true`

### 2. 使用者點餐
- **端點**: `GET /api/menu/ocr/{ocr_menu_id}` - 取得已儲存的OCR菜單
- **端點**: `POST /api/orders/ocr` - 建立OCR菜單訂單
- **功能**: 使用者可以：
  - 查看已儲存的OCR菜單內容
  - 選擇想要的菜色和數量
  - 提交訂單

### 3. 傳回Line Bot
- **功能**: 訂單建立後，系統會：
  - 生成語音檔案
  - 發送訂單摘要到Line Bot
  - 在摘要中包含OCR菜單ID和儲存狀態

### 4. 訂單存回資料庫
- **功能**: 最後系統會：
  - 將完整訂單儲存到 `orders` 和 `order_items` 表
  - 建立訂單摘要並儲存到 `order_summaries` 表
  - 關聯OCR菜單和訂單記錄

## 新增的API端點

### 1. 取得OCR菜單
```
GET /api/menu/ocr/{ocr_menu_id}
```
- 根據OCR菜單ID取得已儲存的菜單資料
- 返回前端相容的菜單格式

### 2. 查詢使用者OCR菜單歷史
```
GET /api/menu/ocr/user/{user_id}
```
- 查詢使用者的所有OCR菜單歷史
- 返回菜單列表和統計資訊

### 3. 建立OCR菜單訂單
```
POST /api/orders/ocr
```
- 專門處理OCR菜單的訂單建立
- 需要提供 `ocr_menu_id` 和訂單項目
- 自動處理OCR菜單的特殊邏輯

## 修改的現有端點

### 1. 菜單OCR處理
```
POST /api/menu/process-ocr
```
- 修改為先儲存OCR結果到資料庫
- 返回OCR菜單ID供後續使用

### 2. 訂單建立
```
POST /api/orders
```
- 支援OCR菜單項目的處理
- 自動識別OCR菜單項目（以 `ocr_` 開頭）
- 在訂單摘要中包含OCR菜單ID

### 3. Line Bot通知
- 修改 `send_complete_order_notification` 函數
- 在通知中包含OCR菜單ID和儲存狀態
- 支援多語言顯示OCR資訊

## 資料庫結構

### OCR菜單相關表格
- `ocr_menus`: OCR菜單主檔
- `ocr_menu_items`: OCR菜單項目
- `order_summaries`: 訂單摘要（關聯OCR菜單和訂單）

### 訂單相關表格
- `orders`: 訂單主檔
- `order_items`: 訂單項目（新增 `original_name` 和 `translated_name` 欄位）

## 使用流程示例

### 1. 上傳菜單圖片
```javascript
// 前端上傳菜單圖片
const formData = new FormData();
formData.append('image', file);
formData.append('user_id', userId);
formData.append('lang', 'en');

const response = await fetch('/api/menu/process-ocr', {
  method: 'POST',
  body: formData
});

const result = await response.json();
const ocrMenuId = result.ocr_menu_id; // 儲存這個ID
```

### 2. 取得菜單資料
```javascript
// 使用OCR菜單ID取得菜單資料
const menuResponse = await fetch(`/api/menu/ocr/${ocrMenuId}?lang=en`);
const menuData = await menuResponse.json();
// 顯示菜單供使用者選擇
```

### 3. 建立訂單
```javascript
// 建立OCR菜單訂單
const orderData = {
  ocr_menu_id: ocrMenuId,
  items: [
    {
      id: 'ocr_123_1',
      quantity: 2,
      price: 100
    }
  ],
  line_user_id: 'user123',
  language: 'en'
};

const orderResponse = await fetch('/api/orders/ocr', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(orderData)
});
```

## 優勢

1. **資料持久化**: OCR菜單先儲存到資料庫，避免重複處理
2. **流程清晰**: 每個步驟都有明確的職責
3. **可追蹤**: 可以追蹤OCR菜單和訂單的關聯
4. **多語言支援**: 支援多語言顯示和處理
5. **向後相容**: 保持與現有系統的相容性

## 注意事項

1. OCR菜單ID在整個流程中很重要，需要妥善保存
2. 訂單項目ID格式為 `ocr_{ocr_menu_id}_{item_id}`
3. 系統會自動處理OCR菜單的特殊邏輯
4. Line Bot通知會包含OCR菜單ID和儲存狀態
