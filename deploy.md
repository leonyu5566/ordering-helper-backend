# Google Cloud 部署指南

## 1. Google Cloud Run 部署

### 前置準備
1. 安裝 Google Cloud SDK
2. 啟用必要的 API：
   - Cloud Run API
   - Cloud Build API
   - Container Registry API

### 環境變數設定
在 Cloud Run 中設定以下環境變數：

```bash
# 資料庫連線設定
DB_USERNAME=gae252g1usr
DB_PASSWORD=gae252g1PSWD!
DB_HOST=35.201.153.17
DB_NAME=gae252g1_db

# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN=你的LINE_BOT_ACCESS_TOKEN
LINE_CHANNEL_SECRET=你的LINE_BOT_SECRET

# Gemini API 設定
GEMINI_API_KEY=your_gemini_api_key

# Azure Speech Service 設定
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=australiaeast
```

### 部署命令
```bash
# 建立映像
docker build -t gcr.io/YOUR_PROJECT_ID/ordering-helper-backend .

# 推送映像
docker push gcr.io/YOUR_PROJECT_ID/ordering-helper-backend

# 部署到 Cloud Run
gcloud run deploy ordering-helper-backend \
  --image gcr.io/YOUR_PROJECT_ID/ordering-helper-backend \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10
```

## 2. 其他部署選項

### App Engine（適合簡單應用）
- 更簡單的部署流程
- 自動擴展
- 適合中小型應用

### Compute Engine（適合複雜應用）
- 完全控制伺服器
- 適合需要特殊配置的應用
- 需要管理伺服器

### Cloud Functions（適合輕量級 API）
- 無伺服器函數
- 按請求付費
- 適合簡單的 API 端點

## 3. 安全建議

1. **環境變數**：使用 Secret Manager 管理敏感資訊
2. **資料庫**：確保 Cloud SQL 的網路安全設定
3. **HTTPS**：Cloud Run 自動提供 HTTPS
4. **CORS**：限制允許的來源網域

## 4. 監控和日誌

- 使用 Cloud Logging 查看應用程式日誌
- 使用 Cloud Monitoring 監控效能
- 設定告警通知

## 5. 成本優化

- 設定適當的記憶體和 CPU 限制
- 使用 Cloud Run 的冷啟動優化
- 監控使用量避免超支 