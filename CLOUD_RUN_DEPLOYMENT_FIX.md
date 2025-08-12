# Cloud Run 部署問題修復指南

## 問題描述
Cloud Run 部署失敗，錯誤訊息顯示容器無法在指定的 PORT=8080 上啟動和監聽。

## 根本原因
1. **端口配置問題**: Flask 應用程式沒有正確處理 Cloud Run 提供的 PORT 環境變數
2. **啟動配置**: 缺少適當的健康檢查端點和啟動腳本
3. **Docker 配置**: Dockerfile 中的啟動命令需要優化

## 修復內容

### 1. 更新 Flask 應用程式配置 (`app/__init__.py`)
- 添加 PORT 配置到 Flask 應用程式設定
- 新增健康檢查端點 `/health`
- 確保應用程式能正確讀取環境變數

### 2. 優化啟動腳本 (`run.py`)
- 改進 PORT 環境變數處理
- 添加啟動日誌
- 確保生產環境配置

### 3. 創建啟動腳本 (`startup.sh`)
- 提供詳細的啟動日誌
- 確保正確的端口綁定
- 添加環境變數檢查

### 4. 更新 Dockerfile
- 設定 PORT 環境變數
- 添加健康檢查
- 使用啟動腳本
- 優化 gunicorn 配置

### 5. 新增測試端點 (`app/api/routes.py`)
- 添加 `/api/test` 端點用於 API 測試
- 提供基本的連線驗證

### 6. 創建部署驗證腳本 (`deploy_verify.py`)
- 本地部署測試
- Docker 建置測試
- 端點連線測試

## 部署步驟

### 1. 本地測試
```bash
# 安裝依賴
pip install -r requirements.txt

# 執行驗證腳本
python deploy_verify.py

# 或直接測試
python run.py
```

### 2. Docker 測試
```bash
# 建置映像
docker build -t ordering-helper-backend .

# 本地運行
docker run -p 8080:8080 -e PORT=8080 ordering-helper-backend

# 測試端點
curl http://localhost:8080/health
curl http://localhost:8080/api/test
```

### 3. Cloud Run 部署
```bash
# 建置並推送映像
gcloud builds submit --tag gcr.io/PROJECT_ID/ordering-helper-backend

# 部署到 Cloud Run
gcloud run deploy ordering-helper-backend \
  --image gcr.io/PROJECT_ID/ordering-helper-backend \
  --platform managed \
  --region REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 80
```

## 關鍵修復點

### 端口綁定
- 確保應用程式監聽 `0.0.0.0:8080`
- 正確處理 PORT 環境變數
- 使用 gunicorn 的 `--bind` 參數

### 健康檢查
- 提供 `/health` 端點
- 在 Dockerfile 中添加 HEALTHCHECK
- 確保 Cloud Run 能檢測到服務狀態

### 啟動腳本
- 詳細的啟動日誌
- 環境變數驗證
- 錯誤處理和報告

### 錯誤處理
- 添加啟動日誌
- 提供診斷資訊
- 優化 gunicorn 配置

## 驗證清單

部署前請確認：
- [ ] 本地測試通過
- [ ] Docker 建置成功
- [ ] 本地 Docker 運行正常
- [ ] 所有端點可訪問
- [ ] 環境變數正確設定
- [ ] 健康檢查端點正常

## 故障排除

### 如果仍然失敗：
1. 檢查 Cloud Run 日誌
2. 確認環境變數設定
3. 驗證資料庫連線
4. 檢查依賴套件版本

### 常見問題：
- **端口衝突**: 確保沒有其他服務使用 8080 端口
- **環境變數**: 確認 Cloud Run 中設定了必要的環境變數
- **依賴問題**: 檢查 requirements.txt 中的套件版本相容性

## 聯絡支援

如果問題持續存在，請：
1. 檢查 Cloud Run 日誌
2. 執行本地驗證腳本
3. 提供錯誤日誌和配置資訊
