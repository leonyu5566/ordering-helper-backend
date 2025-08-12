# Cloud Run 部署修復指南

## 問題描述
Cloud Run 部署失敗，錯誤訊息：
```
ERROR: (gcloud.run.deploy) Revision 'ordering-helper-backend-00426-z5l' is not ready and cannot serve traffic. The user-provided container failed to start and listen on the port defined provided by the PORT=8080 environment variable within the allocated timeout.
```

## 已修復的問題

### 1. 端口監聽配置 ✅
- **run.py**: 已正確配置監聽 `PORT` 環境變數
- **Dockerfile**: 已添加 `ENV PORT=8080` 和 `EXPOSE 8080`
- **startup_simple.sh**: 已正確使用 `--bind "0.0.0.0:$PORT"`

### 2. 啟動腳本優化 ✅
- 添加了更詳細的錯誤檢查和日誌輸出
- 改進了環境變數檢查
- 添加了 `--enable-stdio-inheritance` 參數

### 3. 健康檢查端點 ✅
- 應用程式已包含 `/health` 端點
- Dockerfile 已添加健康檢查配置

## 部署步驟

### 1. 本地測試
```bash
# 運行部署驗證
python3 deploy_verify.py

# 測試應用程式啟動
python3 test_startup.py
```

### 2. 建置 Docker 映像
```bash
# 建置映像
docker build -t ordering-helper-backend .

# 本地測試容器
docker run -p 8080:8080 -e PORT=8080 ordering-helper-backend
```

### 3. 部署到 Cloud Run
```bash
# 設定專案 ID
export PROJECT_ID="your-project-id"

# 建置並推送映像
gcloud builds submit --tag gcr.io/$PROJECT_ID/ordering-helper-backend

# 部署到 Cloud Run
gcloud run deploy ordering-helper-backend \
  --image gcr.io/$PROJECT_ID/ordering-helper-backend \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars "PORT=8080"
```

### 4. 設定環境變數
在 Cloud Run 控制台中設定以下環境變數：
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_DATABASE`
- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_CHANNEL_SECRET`
- `PORT=8080`

## 關鍵修復點

### 1. 端口配置
```python
# run.py
port = int(os.environ.get('PORT', 8080))
app.run(host='0.0.0.0', port=port, debug=False)
```

### 2. Dockerfile 配置
```dockerfile
ENV PORT=8080
EXPOSE 8080
CMD ["./startup_simple.sh"]
```

### 3. 啟動腳本
```bash
# startup_simple.sh
exec gunicorn \
    --bind "0.0.0.0:$PORT" \
    --workers 1 \
    --timeout 300 \
    --enable-stdio-inheritance \
    run:app
```

## 驗證部署

### 1. 健康檢查
```bash
curl https://your-service-url/health
```

### 2. 測試端點
```bash
curl https://your-service-url/api/test
```

### 3. 查看日誌
```bash
gcloud logs read --service=ordering-helper-backend --limit=50
```

## 常見問題解決

### 1. 容器啟動超時
- 檢查啟動腳本是否有錯誤
- 確認所有依賴都已安裝
- 查看容器日誌

### 2. 端口綁定失敗
- 確認 `PORT` 環境變數已設定
- 檢查防火牆設定
- 確認應用程式監聽 `0.0.0.0`

### 3. 環境變數缺失
- 在 Cloud Run 控制台中設定所有必要環境變數
- 確認變數名稱和值正確

## 監控和除錯

### 1. 查看即時日誌
```bash
gcloud logs tail --service=ordering-helper-backend
```

### 2. 檢查服務狀態
```bash
gcloud run services describe ordering-helper-backend --region=asia-east1
```

### 3. 重新部署
```bash
gcloud run deploy ordering-helper-backend --image gcr.io/$PROJECT_ID/ordering-helper-backend
```

## 成功指標
- 服務狀態顯示為 "Ready"
- 健康檢查端點返回 200
- 應用程式日誌顯示正常啟動訊息
- 可以正常訪問 API 端點
