# 部署故障排除指南

## 問題：版本衝突錯誤

### 錯誤訊息
```
ERROR: (gcloud.run.deploy) ABORTED: Conflict for resource 'ordering-helper-backend': 
version '1754370786571828' was specified but current version is '1754372676663808'.
```

### 原因分析
這個錯誤表示：
1. **同時有多個部署作業在運行**
2. **資源版本過期**：你的部署引用了過時的資源版本
3. **並發衝突**：多個 GitHub Actions 作業同時嘗試部署

### 解決方案

#### 1. 立即解決
```bash
# 重新運行 GitHub Actions 作業
# 在 GitHub 倉庫頁面 -> Actions -> 找到失敗的作業 -> Re-run jobs
```

#### 2. 預防措施（已實施）
在 `.github/workflows/deploy.yml` 中添加了並發控制：

```yaml
jobs:
  deploy:
    concurrency:
      group: deploy-cloudrun
      cancel-in-progress: true
```

這確保：
- ✅ 同一時間只有一個部署作業運行
- ✅ 新的部署會取消正在進行的部署
- ✅ 避免版本衝突

#### 3. 手動清理（如果需要）
```bash
# 檢查 Cloud Run 服務狀態
gcloud run services list --region=asia-east1

# 檢查部署歷史
gcloud run revisions list --service=ordering-helper-backend --region=asia-east1

# 如果需要，可以刪除舊的修訂版本
gcloud run revisions delete [REVISION_NAME] --region=asia-east1
```

## 其他常見部署問題

### 1. 認證問題
```bash
# 檢查認證狀態
gcloud auth list
gcloud config get-value project

# 重新認證
gcloud auth login
```

### 2. 權限問題
確保 GitHub Actions 服務帳戶有正確權限：
- Cloud Run Admin
- Storage Admin
- Artifact Registry Admin

### 3. 環境變數問題
檢查 GitHub Secrets 是否正確設定：
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_DATABASE`
- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_CHANNEL_SECRET`
- `GEMINI_API_KEY`
- `AZURE_SPEECH_KEY`
- `AZURE_SPEECH_REGION`

### 4. Docker 建置問題
```bash
# 本地測試 Docker 建置
docker build -t test-image .
docker run -p 8080:8080 test-image
```

## 部署最佳實踐

### 1. 使用並發控制
```yaml
concurrency:
  group: deploy-cloudrun
  cancel-in-progress: true
```

### 2. 添加部署驗證
```yaml
- name: Verify Deployment
  run: |
    echo "等待服務啟動..."
    sleep 30
    gcloud run services describe $SERVICE_NAME --region=$REGION
```

### 3. 使用語義化版本標籤
```yaml
image: $REGION-docker.pkg.dev/$PROJECT_ID/ordering-helper-backend/$SERVICE_NAME:${{ github.sha }}
```

### 4. 監控部署狀態
```bash
# 檢查服務狀態
gcloud run services describe ordering-helper-backend --region=asia-east1

# 查看日誌
gcloud run services logs read ordering-helper-backend --region=asia-east1
```

## 緊急回滾程序

如果部署後發現問題：

### 1. 快速回滾
```bash
# 列出修訂版本
gcloud run revisions list --service=ordering-helper-backend --region=asia-east1

# 回滾到上一個版本
gcloud run services update-traffic ordering-helper-backend \
  --to-revisions=REVISION_NAME=100 \
  --region=asia-east1
```

### 2. 暫停部署
在 GitHub Actions 中：
1. 前往 Actions 頁面
2. 找到正在運行的部署作業
3. 點擊 "Cancel workflow"

## 監控和警報

### 1. 設置 Cloud Run 監控
```bash
# 啟用監控
gcloud services enable monitoring.googleapis.com

# 設置警報
gcloud alpha monitoring policies create \
  --policy-from-file=alert-policy.yaml
```

### 2. 檢查部署健康狀況
```bash
# 健康檢查端點
curl https://your-service-url/health

# 檢查響應時間
curl -w "@curl-format.txt" -o /dev/null -s https://your-service-url/
```

## 聯繫支援

如果問題持續存在：
1. 檢查 [Cloud Run 文檔](https://cloud.google.com/run/docs)
2. 查看 [GitHub Actions 文檔](https://docs.github.com/en/actions)
3. 聯繫 Google Cloud 支援

## 更新日誌

- **2024-01-XX**: 添加並發控制，解決版本衝突問題
- **2024-01-XX**: 添加部署驗證步驟
- **2024-01-XX**: 建立故障排除指南 