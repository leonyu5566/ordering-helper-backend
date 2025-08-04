# CORS 部署指南

## 🎯 問題描述

你的前端應用程式在 Azure 靜態網頁上運行，而後端 API 部署在 Google Cloud Run 上。當前端嘗試呼叫後端 API 時，遇到了 CORS（跨來源資源共用）錯誤：

```
CORS policy: No 'Access-Control-Allow-Origin'
Failed to load resource: status of 400
OCR 處理失敗: Error: AI 辨識失敗
```

## ✅ 解決方案

### 1. 後端 CORS 設定已更新

我們已經在 Flask 應用程式中進行了以下更新：

#### 📝 `app/__init__.py` 更新
```python
# 更完整的 CORS 設定
CORS(app, 
     origins=allowed_origins, 
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     supports_credentials=True,
     max_age=3600)
```

#### 📝 `app/api/routes.py` 更新
- 添加了 `handle_cors_preflight()` 函數來統一處理 OPTIONS 請求
- 為所有重要端點添加了 OPTIONS 方法支援
- 為所有響應添加了 `Access-Control-Allow-Origin` header

### 2. 支援的端點

以下端點現在都支援 CORS：

| 端點 | 方法 | 功能 |
|------|------|------|
| `/api/test` | GET, OPTIONS | API 連線測試 |
| `/api/health` | GET, OPTIONS | 健康檢查 |
| `/api/stores` | GET, OPTIONS | 取得所有店家 |
| `/api/upload-menu-image` | POST, OPTIONS | 上傳菜單圖片 |
| `/api/menu/process-ocr` | POST, OPTIONS | 處理菜單 OCR |
| `/api/orders` | POST, OPTIONS | 建立訂單 |
| `/api/orders/temp` | POST, OPTIONS | 建立臨時訂單 |

### 3. 部署步驟

#### 🚀 本地測試
```bash
# 1. 啟動後端服務
python run.py

# 2. 測試 CORS 設定
python test_cors.py
```

#### 🚀 部署到 Google Cloud Run
```bash
# 1. 構建 Docker 映像
docker build -t ordering-helper-backend .

# 2. 推送到 Google Container Registry
docker tag ordering-helper-backend gcr.io/YOUR_PROJECT_ID/ordering-helper-backend
docker push gcr.io/YOUR_PROJECT_ID/ordering-helper-backend

# 3. 部署到 Cloud Run
gcloud run deploy ordering-helper-backend \
  --image gcr.io/YOUR_PROJECT_ID/ordering-helper-backend \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated
```

### 4. 驗證 CORS 設定

#### 🔍 使用瀏覽器開發者工具
1. 打開瀏覽器開發者工具 (F12)
2. 切換到 Network 標籤
3. 嘗試上傳菜單圖片
4. 檢查 OPTIONS 和 POST 請求的 Response Headers

應該看到以下 headers：
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS
Access-Control-Allow-Headers: Content-Type,Authorization,X-Requested-With
Access-Control-Max-Age: 3600
```

#### 🔍 使用 curl 測試
```bash
# 測試 OPTIONS 預檢請求
curl -X OPTIONS -H "Origin: https://green-beach-0f9762500.1.azurestaticapps.net" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v https://your-api-url/api/upload-menu-image
```

### 5. 常見問題排除

#### ❌ 問題：仍然收到 CORS 錯誤
**解決方案：**
1. 確認後端服務已重新部署
2. 清除瀏覽器快取
3. 檢查 Cloud Run 服務的環境變數設定

#### ❌ 問題：OPTIONS 請求返回 404
**解決方案：**
1. 確認所有端點都添加了 OPTIONS 方法
2. 檢查 `handle_cors_preflight()` 函數是否正確實作

#### ❌ 問題：生產環境中 CORS 不工作
**解決方案：**
1. 確認 Cloud Run 服務的環境變數正確設定
2. 檢查防火牆和網路設定
3. 確認域名和 SSL 憑證設定

### 6. 監控和日誌

#### 📊 監控 CORS 請求
```python
# 在 app/__init__.py 中添加日誌
import logging
logging.basicConfig(level=logging.INFO)

@app.before_request
def log_request_info():
    logging.info('Headers: %s', dict(request.headers))
    logging.info('Body: %s', request.get_data())
```

#### 📊 查看 Cloud Run 日誌
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ordering-helper-backend" --limit=50
```

## 🎉 預期結果

修復後，你的前端應該能夠：
1. ✅ 成功發送 OPTIONS 預檢請求
2. ✅ 收到正確的 CORS headers
3. ✅ 成功上傳菜單圖片
4. ✅ 收到 OCR 處理結果

如果仍然遇到問題，請檢查：
- 後端服務是否已重新部署
- 瀏覽器快取是否已清除
- 網路連線是否正常 