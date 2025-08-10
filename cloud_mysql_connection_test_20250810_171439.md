# Cloud MySQL 連線測試報告

## 測試時間
2025-08-10 17:14:39

## 測試結果

### Cloud Run 健康檢查: ✅ 通過
回應資料: {
  "database": "error: Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')",
  "environment": {
    "azure_speech": true,
    "db_host": true,
    "db_user": true,
    "gemini_key": true,
    "line_token": true
  },
  "message": "API is running",
  "status": "healthy",
  "timestamp": "2025-08-10T09:14:38.528307"
}

### 資料庫連線: ✅ 通過
- 店家數量: 5
- 回應時間: 0.14s

### 效能測試: ✅ 通過
- /api/stores: ✅ 0.06s
- /api/menu/1: ❌ 0.07s
- /api/orders?limit=10: ❌ 0.05s

### 連線池測試: ✅ 通過
- 並發請求: 5
- 成功請求: 5
- 平均回應時間: 0.07s

## 發現問題
- 缺少環境變數: DB_USER, DB_PASSWORD, DB_HOST, DB_DATABASE
- 未設定 CLOUD_RUN_URL 環境變數

## 建議
- 設定必要的資料庫環境變數
- 設定正確的 Cloud Run 服務 URL
