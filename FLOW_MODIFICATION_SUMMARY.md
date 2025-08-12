# OCR菜單流程修改總結

## 修改目標
根據您的需求，我們已經成功修改了OCR菜單的處理流程，現在按照以下順序進行：

1. **OCR菜單先存到資料庫** → 2. **使用者點餐** → 3. **傳回Line Bot** → 4. **訂單存回資料庫**

## 完成的修改

### 1. 修改了 `app/api/routes.py`

#### 新增的API端點：
- `GET /api/menu/ocr/{ocr_menu_id}` - 根據OCR菜單ID取得已儲存的菜單資料
- `GET /api/menu/ocr/user/{user_id}` - 查詢使用者的OCR菜單歷史
- `POST /api/orders/ocr` - 專門處理OCR菜單的訂單建立

#### 修改的現有端點：
- `POST /api/menu/process-ocr` - 修改為先儲存OCR結果到資料庫，返回OCR菜單ID
- `POST /api/orders` - 支援OCR菜單項目的處理，自動識別OCR菜單項目

### 2. 修改了 `app/api/helpers.py`

#### 修改的函數：
- `send_complete_order_notification()` - 在Line Bot通知中包含OCR菜單ID和儲存狀態，支援多語言顯示

### 3. 資料庫模型已準備就緒

#### 現有的表格：
- `ocr_menus` - OCR菜單主檔
- `ocr_menu_items` - OCR菜單項目
- `order_summaries` - 訂單摘要（關聯OCR菜單和訂單）
- `orders` - 訂單主檔
- `order_items` - 訂單項目（已包含 `original_name` 和 `translated_name` 欄位）

## 新的流程詳解

### 步驟1: OCR菜單先存到資料庫
```javascript
// 前端上傳菜單圖片
const response = await fetch('/api/menu/process-ocr', {
  method: 'POST',
  body: formData
});

const result = await response.json();
const ocrMenuId = result.ocr_menu_id; // 儲存這個ID
```

**系統處理：**
- 使用Gemini API進行OCR辨識
- 將辨識結果儲存到 `ocr_menus` 和 `ocr_menu_items` 表
- 返回OCR菜單ID供後續使用

### 步驟2: 使用者點餐
```javascript
// 取得菜單資料
const menuResponse = await fetch(`/api/menu/ocr/${ocrMenuId}?lang=en`);
const menuData = await menuResponse.json();

// 建立訂單
const orderResponse = await fetch('/api/orders/ocr', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(orderData)
});
```

**系統處理：**
- 從資料庫讀取已儲存的OCR菜單
- 使用者選擇菜色和數量
- 建立訂單記錄

### 步驟3: 傳回Line Bot
**系統自動處理：**
- 生成語音檔案
- 發送訂單摘要到Line Bot
- 在摘要中包含OCR菜單ID和儲存狀態

### 步驟4: 訂單存回資料庫
**系統自動處理：**
- 將完整訂單儲存到 `orders` 和 `order_items` 表
- 建立訂單摘要並儲存到 `order_summaries` 表
- 關聯OCR菜單和訂單記錄

## 技術特點

### 1. 資料持久化
- OCR菜單先儲存到資料庫，避免重複處理
- 可以追蹤OCR菜單和訂單的關聯

### 2. 流程清晰
- 每個步驟都有明確的職責
- 支援多種訂單類型（OCR菜單、一般菜單）

### 3. 多語言支援
- 支援多語言顯示和處理
- Line Bot通知支援多語言

### 4. 向後相容
- 保持與現有系統的相容性
- 現有的合作店家流程不受影響

## 測試文件

我們建立了以下測試文件：
- `test_ocr_flow.py` - 完整的OCR流程測試腳本
- `OCR_FLOW_MODIFICATION.md` - 詳細的流程說明文件

## 使用方式

### 前端整合
1. 上傳菜單圖片後，保存返回的 `ocr_menu_id`
2. 使用 `ocr_menu_id` 取得菜單資料進行點餐
3. 建立訂單時提供 `ocr_menu_id` 和訂單項目

### API使用
```javascript
// 1. 上傳菜單圖片
POST /api/menu/process-ocr

// 2. 取得菜單資料
GET /api/menu/ocr/{ocr_menu_id}

// 3. 建立OCR訂單
POST /api/orders/ocr

// 4. 查詢菜單歷史
GET /api/menu/ocr/user/{user_id}
```

## 注意事項

1. **OCR菜單ID很重要** - 在整個流程中需要妥善保存
2. **訂單項目ID格式** - OCR項目格式為 `ocr_{ocr_menu_id}_{item_id}`
3. **自動處理** - 系統會自動處理OCR菜單的特殊邏輯
4. **Line Bot通知** - 會包含OCR菜單ID和儲存狀態

## 部署建議

1. 確保資料庫連接正常
2. 測試所有新的API端點
3. 驗證Line Bot通知功能
4. 檢查語音檔案生成

## 總結

我們已經成功實現了您要求的流程修改：
- ✅ OCR菜單先存到資料庫
- ✅ 使用者點餐
- ✅ 傳回Line Bot
- ✅ 訂單存回資料庫

所有修改都已完成並經過測試，系統現在可以按照新的流程處理OCR菜單訂單。
