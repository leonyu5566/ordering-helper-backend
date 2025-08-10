# Cloud MySQL 連線指南

## 🎯 **概述**

本指南說明如何設定 Cloud Run 服務連線到 Cloud MySQL 資料庫，包含完整的配置步驟、部署方法和故障排除。

## 📋 **前置需求**

- Google Cloud Platform 專案
- Cloud Run 服務已部署
- Cloud MySQL 資料庫實例
- 資料庫連線資訊（主機、使用者、密碼、資料庫名稱）

## 🔧 **設定步驟**

### **步驟 1：設定環境變數**

使用提供的腳本設定環境變數：

```bash
python3 tools/setup_cloud_mysql_env.py
```

腳本會引導你設定以下環境變數：

#### **必要環境變數**
- `DB_USER`: 資料庫使用者名稱
- `DB_PASSWORD`: 資料庫密碼
- `DB_HOST`: 資料庫主機位址（例如：34.123.45.67 或 34.123.45.67:3306）
- `DB_DATABASE`: 資料庫名稱

#### **可選環境變數**
- `DB_PORT`: 資料庫端口（預設：3306）
- `DB_SSL_CA`: SSL CA 憑證路徑
- `DB_SSL_CERT`: SSL 憑證路徑
- `DB_SSL_KEY`: SSL 金鑰路徑
- `DB_POOL_SIZE`: 連線池大小（預設：10）
- `DB_MAX_OVERFLOW`: 最大溢出連線數（預設：20）
- `DB_POOL_TIMEOUT`: 連線池超時時間（預設：30秒）
- `DB_POOL_RECYCLE`: 連線回收時間（預設：3600秒）
- `DB_CONNECT_TIMEOUT`: 連線超時時間（預設：10秒）
- `DB_READ_TIMEOUT`: 讀取超時時間（預設：30秒）
- `DB_WRITE_TIMEOUT`: 寫入超時時間（預設：30秒）

### **步驟 2：驗證配置**

腳本會自動驗證配置並生成：
- `.env` 檔案：包含所有環境變數
- `deploy_cloud_run.sh`：Cloud Run 部署腳本

### **步驟 3：部署到 Cloud Run**

#### **方法 1：使用自動生成的腳本**
```bash
./deploy_cloud_run.sh
```

#### **方法 2：手動部署**
```bash
gcloud run deploy ordering-helper-backend \
  --source . \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --max-instances 2 \
  --set-env-vars DB_USER=your_user,DB_PASSWORD=your_password,DB_HOST=your_host,DB_DATABASE=your_db \
  --timeout 300
```

#### **方法 3：使用 Cloud Build**
```bash
gcloud builds submit --config cloudbuild.yaml .
```

## 🧪 **測試連線**

### **基本連線測試**
```bash
python3 tools/test_cloud_mysql_connection_enhanced.py
```

### **測試腳本功能**
- Cloud Run 健康檢查
- 資料庫連線測試
- 效能測試
- 連線池測試
- 問題診斷

## 🔍 **故障排除**

### **常見問題**

#### **1. 連線被拒絕**
```
Error: (2003, "Can't connect to MySQL server on 'host' (timed out)")
```

**解決方案：**
- 檢查 `DB_HOST` 是否正確
- 確認 Cloud MySQL 實例是否運行
- 檢查防火牆規則和網路設定

#### **2. 認證失敗**
```
Error: (1045, "Access denied for user 'username'@'host'")
```

**解決方案：**
- 檢查 `DB_USER` 和 `DB_PASSWORD` 是否正確
- 確認使用者是否有適當的權限
- 檢查使用者主機限制

#### **3. 資料庫不存在**
```
Error: (1049, "Unknown database 'database_name'")
```

**解決方案：**
- 檢查 `DB_DATABASE` 是否正確
- 確認資料庫是否已建立
- 檢查使用者是否有資料庫存取權限

#### **4. SSL 連線問題**
```
Error: SSL connection error
```

**解決方案：**
- 檢查 SSL 憑證設定
- 使用預設 SSL 配置：`ssl={'ssl': {}}&ssl_verify_cert=false`
- 確認 Cloud MySQL 實例支援 SSL

### **連線診斷**

使用診斷功能檢查問題：

```bash
python3 tools/test_cloud_mysql_connection_enhanced.py
```

腳本會自動診斷常見問題並提供建議。

## 📊 **效能優化**

### **連線池設定**

根據負載調整連線池參數：

```bash
# 高負載環境
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=40
export DB_POOL_TIMEOUT=60

# 低負載環境
export DB_POOL_SIZE=5
export DB_MAX_OVERFLOW=10
export DB_POOL_TIMEOUT=15
```

### **超時設定**

根據網路狀況調整超時時間：

```bash
# 網路較慢的環境
export DB_CONNECT_TIMEOUT=30
export DB_READ_TIMEOUT=60
export DB_WRITE_TIMEOUT=60

# 網路較快的環境
export DB_CONNECT_TIMEOUT=5
export DB_READ_TIMEOUT=15
export DB_WRITE_TIMEOUT=15
```

## 🔒 **安全性考量**

### **環境變數管理**
- 不要在程式碼中硬編碼資料庫憑證
- 使用 Google Cloud Secret Manager 管理敏感資訊
- 定期輪換資料庫密碼

### **網路安全**
- 使用 Cloud SQL Proxy 進行安全連線
- 限制資料庫存取來源 IP
- 啟用 SSL 連線

### **權限管理**
- 使用最小權限原則
- 定期審查資料庫使用者權限
- 監控資料庫存取日誌

## 📈 **監控和日誌**

### **Cloud Run 日誌**
```bash
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=ordering-helper-backend" --limit=50
```

### **資料庫連線監控**
- 監控連線池使用率
- 追蹤查詢回應時間
- 監控錯誤率和連線失敗

## 🚀 **部署檢查清單**

- [ ] 環境變數已正確設定
- [ ] 資料庫連線測試通過
- [ ] Cloud Run 服務正常運行
- [ ] 應用程式可以存取資料庫
- [ ] 效能測試結果符合預期
- [ ] 監控和日誌已設定
- [ ] 安全性設定已完成

## 📞 **支援**

如果遇到問題：

1. 檢查本指南的故障排除部分
2. 執行診斷腳本
3. 查看 Cloud Run 和 Cloud MySQL 日誌
4. 參考 Google Cloud 官方文件

## 📚 **相關資源**

- [Cloud Run 文件](https://cloud.google.com/run/docs)
- [Cloud SQL 文件](https://cloud.google.com/sql/docs)
- [SQLAlchemy 文件](https://docs.sqlalchemy.org/)
- [PyMySQL 文件](https://pymysql.readthedocs.io/)
