# 國際化（i18n）實現指南

## 概述

本文檔說明後端 Flask 應用程式的國際化改進，解決店名和菜單顯示語言問題，以及 API 失敗時卡在 "Preparing..." 的問題。

## 實現的功能

### 1. 語言碼正規化 (`app/api/translation_service.py`)

- 將 BCP-47 語言碼（如 `en-US`, `zh-Hant`）轉換為支援的短碼
- 支援的語言：`en`, `zh-tw`, `zh-cn`, `ja`, `ko`, `fr`, `de`, `es`, `it`, `pt`, `ru`, `ar`, `hi`, `th`, `vi`

### 2. 翻譯服務

- 單一文字翻譯：`translate_text()`
- 批次翻譯：`translate_texts()`
- 整合現有的 Google Cloud Translation API

### 3. 更新的 API 端點

#### `/api/store/resolve`
- **功能**：解析店家識別碼，回傳合作狀態和翻譯店名
- **參數**：
  - `place_id`：Google Place ID
  - `name`：店家名稱（可選）
  - `lang`：目標語言（如 `en`, `ja`, `zh-Hant`）
- **回傳**：
  ```json
  {
    "is_partner": true,
    "store_id": 123,
    "original_name": "原始店名",
    "display_name": "翻譯後店名",
    "place_id": "ChlJ0boght2rQjQRsH-_buCo3S4"
  }
  ```

#### `/api/partner/menu`
- **功能**：取得合作店家菜單（支援多語言翻譯）
- **參數**：
  - `store_id`：店家 ID
  - `lang`：目標語言
- **回傳**：
  ```json
  {
    "store_id": 123,
    "store_name": "店家名稱",
    "user_language": "en",
    "normalized_language": "en",
    "items": [
      {
        "id": 1,
        "name": "翻譯後菜名",
        "original_name": "原始菜名",
        "price_small": 50,
        "price_large": 80,
        "category": "翻譯後分類",
        "original_category": "原始分類"
      }
    ]
  }
  ```

#### `/api/stores/check-partner-status`
- **功能**：檢查店家合作狀態（永遠回傳 200）
- **參數**：
  - `store_id` 或 `place_id`：店家識別
  - `name`：店家名稱（可選）
  - `lang`：目標語言
- **回傳**：
  ```json
  {
    "store_id": 123,
    "store_name": "店家名稱",
    "display_name": "翻譯後店名",
    "original_name": "原始店名",
    "place_id": "ChlJ0boght2rQjQRsH-_buCo3S4",
    "partner_level": 1,
    "is_partner": true,
    "has_menu": true
  }
  ```

#### `/api/translate`
- **功能**：翻譯單一文字（前端 fallback 用）
- **方法**：POST
- **參數**：
  - `target`：目標語言
- **Body**：
  ```json
  {
    "text": "要翻譯的文字"
  }
  ```
- **回傳**：
  ```json
  {
    "translated": "翻譯後的文字"
  }
  ```

## 錯誤處理改進

### 1. 永遠回傳 200 狀態碼

所有端點都經過改進，即使發生錯誤也會回傳 200 狀態碼，避免前端卡在 "Preparing..." 狀態：

- 資料庫查詢失敗 → 回傳預設值
- 翻譯服務失敗 → 回傳原文
- 網路錯誤 → 回傳預設值

### 2. 快取標頭

所有端點都加入快取標頭：
```
Cache-Control: public, max-age=300
```

### 3. CORS 支援

所有端點都支援 CORS，允許來自 Azure Static Web Apps 和 LINE LIFF 的請求。

## 部署步驟

### 1. 本地測試

```bash
# 啟動後端服務
python run.py

# 執行測試腳本
python test_i18n_endpoints.py
```

### 2. Cloud Run 部署

```bash
# 構建 Docker 映像
docker build -t ordering-helper-backend .

# 推送到 Google Container Registry
docker tag ordering-helper-backend gcr.io/YOUR_PROJECT_ID/ordering-helper-backend
docker push gcr.io/YOUR_PROJECT_ID/ordering-helper-backend

# 部署到 Cloud Run
gcloud run deploy ordering-helper-backend \
  --image gcr.io/YOUR_PROJECT_ID/ordering-helper-backend \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --port 8080
```

### 3. 環境變數設定

確保以下環境變數已設定：

```bash
# Google Cloud Translation API
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# 資料庫連線
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=your-db-host
DB_DATABASE=your-db-name

# Cloud Run
PORT=8080
```

## 前端整合

### 1. 更新 API 呼叫

前端需要更新以下 API 呼叫，加入 `lang` 參數：

```javascript
// 店家解析
const response = await fetch(`/api/store/resolve?place_id=${placeId}&name=${storeName}&lang=${userLang}`);

// 合作店家菜單
const response = await fetch(`/api/partner/menu?store_id=${storeId}&lang=${userLang}`);

// 合作狀態檢查
const response = await fetch(`/api/stores/check-partner-status?place_id=${placeId}&name=${storeName}&lang=${userLang}`);
```

### 2. 語言碼來源

使用 LINE LIFF SDK 取得使用者語言：

```javascript
// 優先使用 getAppLanguage()（需要 LIFF SDK ≥ v2.24）
let userLang = 'en';
try {
  userLang = liff.getAppLanguage();
} catch (e) {
  // 回退到 getLanguage()
  userLang = liff.getLanguage();
}
```

## 測試驗證

### 1. 功能測試

- [ ] 語言碼正規化正確處理各種 BCP-47 格式
- [ ] 店名翻譯在不同語言下正確顯示
- [ ] 菜單項目翻譯正確
- [ ] 非合作店家也能正確翻譯店名
- [ ] API 失敗時不會卡在 "Preparing..."

### 2. 效能測試

- [ ] 翻譯結果有適當的快取
- [ ] 批次翻譯效能良好
- [ ] 錯誤處理不會影響正常流程

### 3. 相容性測試

- [ ] 支援各種 LINE App 語言設定
- [ ] 支援各種瀏覽器
- [ ] 支援 Azure Static Web Apps 部署

## 注意事項

1. **翻譯成本**：Google Cloud Translation API 有使用量限制和費用，建議實作翻譯結果快取
2. **語言支援**：目前支援主要語言，可根據需求擴展
3. **錯誤處理**：所有端點都有 fallback 機制，確保前端不會卡住
4. **快取策略**：翻譯結果快取 5 分鐘，可根據需求調整

## 未來改進

1. **資料庫快取**：將翻譯結果儲存到資料庫，減少 API 呼叫
2. **更多語言**：支援更多語言和地區變體
3. **翻譯品質**：整合多個翻譯服務，選擇最佳翻譯結果
4. **使用者偏好**：記住使用者的語言偏好設定
