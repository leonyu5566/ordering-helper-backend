# 🚀 點餐小幫手後端 - 組員環境設定指南

## 📋 快速開始

### 1. 複製環境配置模板
```bash
# 複製模板檔案
cp env_template.txt .env

# 編輯環境配置
nano .env
```

### 2. 必須修改的配置項目

#### 🔑 Google Cloud 專案設定
```bash
# 您的 Google Cloud 專案 ID
GCP_PROJECT_ID=your-actual-project-id

# 您的 Cloud Run 服務 URL
CLOUD_RUN_SERVICE_URL=https://ordering-helper-backend-your-project-id.asia-east1.run.app

# 您的應用程式基礎 URL
BASE_URL=https://ordering-helper-backend-your-project-id.asia-east1.run.app

# 您的服務帳戶
TASKS_INVOKER_SERVICE_ACCOUNT=tasks-invoker@your-project-id.iam.gserviceaccount.com
```

#### 🤖 LINE Bot 設定
```bash
# 您的 LINE Bot 頻道存取權杖
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token

# 您的 LINE Bot 頻道密鑰
LINE_CHANNEL_SECRET=your_line_channel_secret
```

#### 🧠 AI 服務設定
```bash
# 您的 Google Gemini API 金鑰
GEMINI_API_KEY=your_gemini_api_key
```

## 🔧 詳細設定步驟

### 步驟 1：取得 Google Cloud 專案資訊

1. **登入 Google Cloud Console**
   - 前往 [Google Cloud Console](https://console.cloud.google.com/)
   - 選擇您的專案

2. **取得專案 ID**
   - 在專案選擇器中查看專案 ID
   - 例如：`solid-heaven-466011-d1`

3. **取得 Cloud Run 服務 URL**
   - 前往 Cloud Run 服務頁面
   - 複製服務的主要 URL
   - 例如：`https://ordering-helper-backend-1095766716155.asia-east1.run.app`

### 步驟 2：設定 LINE Bot

1. **前往 LINE Developers Console**
   - 登入 [LINE Developers Console](https://developers.line.biz/)
   - 選擇您的 LINE Bot 應用程式

2. **取得頻道設定**
   - 複製 Channel Access Token
   - 複製 Channel Secret

### 步驟 3：設定 Google Gemini API

1. **前往 Google AI Studio**
   - 前往 [Google AI Studio](https://makersuite.google.com/app/apikey)
   - 創建新的 API 金鑰

2. **複製 API 金鑰**
   - 將金鑰複製到 `GEMINI_API_KEY` 變數

### 步驟 4：設定 Cloud Tasks

1. **創建 Cloud Tasks 佇列**
   ```bash
   # 使用 gcloud CLI 創建佇列
   gcloud tasks queues create order-processing-queue \
     --location=asia-east1 \
     --max-concurrent-dispatches=10 \
     --max-dispatches-per-second=500
   ```

2. **創建服務帳戶**
   ```bash
   # 創建服務帳戶
   gcloud iam service-accounts create tasks-invoker \
     --display-name="Cloud Tasks Invoker"
   
   # 設定權限
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:tasks-invoker@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/run.invoker"
   ```

## ✅ 配置驗證

### 1. 啟動應用程式
```bash
python3 run.py
```

### 2. 檢查配置驗證訊息
您應該看到類似以下的訊息：
```
✅ Cloud Tasks 配置驗證通過
   - 專案 ID: your-project-id
   - 位置: asia-east1
   - 佇列名稱: order-processing-queue
   - 服務 URL: https://ordering-helper-backend-your-project-id.asia-east1.run.app
   - 服務帳戶: tasks-invoker@your-project-id.iam.gserviceaccount.com
   - 處理端點 URL: https://ordering-helper-backend-your-project-id.asia-east1.run.app/api/orders/process-task
   - Audience URL: https://ordering-helper-backend-your-project-id.asia-east1.run.app
```

### 3. 測試 API 端點
```bash
# 測試健康檢查
curl https://ordering-helper-backend-your-project-id.asia-east1.run.app/api/health

# 應該返回：
# {"message": "點餐小幫手後端 API 正常運作", "status": "healthy"}
```

## 🚨 常見問題

### 問題 1：Cloud Tasks 創建失敗
**症狀**：`❌ Cloud Tasks 創建超時（10秒）`
**解決**：
1. 檢查 `GCP_PROJECT_ID` 是否正確
2. 檢查 `CLOUD_RUN_SERVICE_URL` 是否為您的服務 URL
3. 確認 Cloud Tasks API 已啟用

### 問題 2：OIDC Token 驗證失敗
**症狀**：`❌ 任務創建失敗: Permission denied`
**解決**：
1. 檢查 `TASKS_INVOKER_SERVICE_ACCOUNT` 格式是否正確
2. 確認服務帳戶有 `Cloud Run Invoker` 權限
3. 檢查 `audience` URL 是否與服務 URL 匹配

### 問題 3：資料庫連線失敗
**症狀**：`❌ 資料庫連線失敗`
**解決**：
1. 資料庫配置是共用的，通常不需要修改
2. 確認網路連線正常
3. 檢查防火牆設定

## 📞 支援

如果遇到問題：
1. 檢查應用程式日誌
2. 確認所有環境變數都已正確設定
3. 參考 Google Cloud 和 LINE Developers 文件
4. 聯繫團隊成員尋求協助

## 🎯 成功指標

設定完成後，您應該能夠：
- ✅ 應用程式正常啟動
- ✅ 配置驗證通過
- ✅ API 端點正常回應
- ✅ Cloud Tasks 能成功創建
- ✅ 背景任務能正常執行
- ✅ 前端能正常輪詢狀態

---

**祝您設定順利！** 🚀
