# API 端點參考文檔

## 🎯 後端 API 端點總覽

### 合作店家系統 API

#### 店家相關
```
GET /api/stores                    # 取得所有店家列表
GET /api/stores/{store_id}         # 取得特定店家資訊
GET /api/stores/check-partner-status # 檢查店家合作狀態
```

#### 菜單相關
```
GET /api/menu/{store_id}           # 取得店家菜單
```

#### 訂單相關
```
POST /api/orders                   # 建立正式訂單
GET /api/orders/{order_id}/confirm # 取得訂單確認資訊
GET /api/orders/{order_id}/voice   # 取得訂單語音檔
GET /api/orders/history            # 取得訂單歷史
GET /api/orders/{order_id}/details # 取得訂單詳情
```

### 非合作店家系統 API

#### 拍照辨識
```
POST /api/menu/simple-ocr          # 拍照辨識菜單
```

#### 簡化訂單
```
POST /api/orders/simple            # 建立簡化訂單
```

### 通用 API

#### 語音生成
```
POST /api/voice/generate           # 生成自定義語音
```

#### 使用者管理
```
POST /api/users/register           # 使用者註冊
```

#### 系統狀態
```
GET /api/health                    # 健康檢查
```

## 📋 詳細 API 說明

### 1. 合作店家系統

#### GET /api/stores
**功能**：取得所有合作店家列表
**回應**：
```json
{
    "stores": [
        {
            "store_id": 1,
            "store_name": "披薩店",
            "description": "美味的披薩"
        }
    ]
}
```

#### GET /api/menu/{store_id}
**功能**：取得店家菜單
**參數**：`lang` - 語言代碼（可選）
**回應**：
```json
{
    "store_id": 1,
    "menu_items": [
        {
            "menu_item_id": 1,
            "item_name": "夏威夷披薩",
            "price": 150,
            "description": "夏威夷風味"
        }
    ]
}
```

#### POST /api/orders
**功能**：建立正式訂單
**請求體**：
```json
{
    "store_id": 1,
    "user_id": 123,
    "items": [
        {
            "menu_item_id": 1,
            "quantity": 2
        }
    ]
}
```

### 2. 非合作店家系統

#### POST /api/menu/simple-ocr
**功能**：拍照辨識菜單
**請求體**：`multipart/form-data`
- `image`：菜單圖片檔案
- `target_lang`：目標語言（可選，預設 'en'）

**回應**：
```json
{
    "success": true,
    "menu_items": [
        {
            "id": "simple_0",
            "name": "夏威夷披薩",
            "translated_name": "Hawaiian Pizza",
            "price": 150,
            "description": "夏威夷風味披薩"
        }
    ],
    "store_name": "披薩店"
}
```

#### POST /api/orders/simple
**功能**：建立簡化訂單
**請求體**：
```json
{
    "items": [
        {
            "name": "夏威夷披薩",
            "quantity": 1,
            "price": 150
        }
    ],
    "user_language": "en"
}
```

**回應**：
```json
{
    "success": true,
    "order_id": "simple_20250105_001",
    "total_amount": 150,
    "voice_url": "/voice/simple_20250105_001.mp3",
    "summary": "訂單摘要...",
    "order_details": [...]
}
```

## 🔧 錯誤處理

### 統一錯誤回應格式
```json
{
    "success": false,
    "error": "錯誤訊息",
    "details": "詳細資訊"
}
```

### 常見 HTTP 狀態碼
- `200` - 成功
- `201` - 創建成功
- `400` - 請求錯誤
- `404` - 找不到資源
- `422` - 處理失敗
- `500` - 伺服器錯誤

## 📱 LIFF 前端整合

### 合作店家流程
```javascript
// 1. 取得店家列表
const storesResponse = await fetch('/api/stores');
const stores = await storesResponse.json();

// 2. 取得菜單
const menuResponse = await fetch(`/api/menu/${storeId}?lang=${userLang}`);
const menu = await menuResponse.json();

// 3. 建立訂單
const orderResponse = await fetch('/api/orders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData)
});
```

### 非合作店家流程
```javascript
// 1. 拍照辨識
const formData = new FormData();
formData.append('image', imageFile);
formData.append('target_lang', userLanguage);

const ocrResponse = await fetch('/api/menu/simple-ocr', {
    method: 'POST',
    body: formData
});

// 2. 建立簡化訂單
const orderResponse = await fetch('/api/orders/simple', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData)
});
```

## 🎯 使用建議

### 1. 系統選擇
- LIFF 前端負責系統選擇介面
- 根據使用者選擇調用對應 API
- 後端只提供純 API 端點

### 2. 錯誤處理
- 統一使用 JSON 錯誤回應
- 前端根據錯誤碼顯示適當訊息
- 記錄詳細錯誤資訊供除錯

### 3. 資料驗證
- 後端負責所有資料驗證
- 前端可預先驗證提升體驗
- 統一驗證規則和錯誤訊息

這個 API 設計完全分離了前後端職責，讓後端專注於提供穩定的 API 服務，前端負責使用者體驗和介面設計。 