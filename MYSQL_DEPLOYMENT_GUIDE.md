# MySQL Cloud Run 部署指南

## 🎯 **目標**

將您的 ordering-helper-backend 部署到 Cloud Run，並使用 MySQL 資料庫語法，直接符合同事的資料庫結構。

## 🔧 **解決方案**

### **1. 保持現有的 GeminiProcessing 模型**

您的代碼已經正確配置為在 Cloud Run 環境中使用 MySQL：

```python
# app/__init__.py
if all([db_username, db_password, db_host, db_name]):
    # 使用 MySQL 連線，添加 SSL 參數
    database_url = f"mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_name}?ssl={{'ssl': {{}}}}&ssl_verify_cert=false"
else:
    # 回退到 SQLite
    database_url = 'sqlite:///app.db'
```

### **2. 使用 MySQL 特定的初始化腳本**

我們創建了 `tools/init_mysql_database.py` 腳本，專門處理 MySQL 環境：

```bash
python3 tools/init_mysql_database.py
```

### **3. 自動化部署流程**

使用 `tools/deploy_to_cloud_run.py` 腳本進行一鍵部署：

```bash
python3 tools/deploy_to_cloud_run.py
```

## 📋 **部署步驟**

### **步驟1：設定環境變數**

```bash
export DB_USER=your_db_user
export DB_PASSWORD=your_db_password
export DB_HOST=your_mysql_host
export DB_DATABASE=gae252g1_db

# 可選的環境變數
export GEMINI_API_KEY=your_gemini_api_key
export LINE_CHANNEL_ACCESS_TOKEN=your_line_token
export LINE_CHANNEL_SECRET=your_line_secret
export AZURE_SPEECH_KEY=your_azure_speech_key
export AZURE_SPEECH_REGION=your_azure_region
```

### **步驟2：檢查環境**

```bash
python3 tools/check_cloud_run_config.py
```

### **步驟3：初始化本地資料庫（可選）**

```bash
python3 tools/init_mysql_database.py
```

### **步驟4：部署到 Cloud Run**

#### **方法A：使用自動化腳本**
```bash
python3 tools/deploy_to_cloud_run.py
```

#### **方法B：手動部署**
```bash
gcloud run deploy ordering-helper-backend \
  --source . \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --set-env-vars DB_USER=your_db_user,DB_PASSWORD=your_db_password,DB_HOST=your_mysql_host,DB_DATABASE=gae252g1_db
```

### **步驟5：驗證部署**

```bash
# 獲取服務 URL
gcloud run services describe ordering-helper-backend --region asia-east1 --format 'value(status.url)'

# 測試健康檢查
curl https://your-service-url/api/health
```

## 🗄️ **資料庫結構**

### **您的模型（保持不變）**

```python
class GeminiProcessing(db.Model):
    __tablename__ = 'gemini_processing'
    processing_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    ocr_result = db.Column(db.Text)
    structured_menu = db.Column(db.Text)
    status = db.Column(db.String(20), default='processing')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
```

### **同事的資料庫結構**

```sql
-- 同事的資料庫使用 ocr_menus 和 ocr_menu_items
CREATE TABLE ocr_menus (
    ocr_menu_id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    store_name VARCHAR(100),
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ocr_menu_items (
    ocr_menu_item_id BIGINT NOT NULL AUTO_INCREMENT,
    ocr_menu_id BIGINT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    price_big INT DEFAULT NULL,
    price_small INT NOT NULL,
    translated_desc TEXT
);
```

## 🔄 **解決方案：保持您的模型，在 Cloud Run 中自動創建表**

### **優勢：**

1. **無需修改現有代碼**：保持 `GeminiProcessing` 模型不變
2. **自動適配**：在 Cloud Run 環境中自動創建所需的表
3. **向後相容**：本地開發仍可使用 SQLite
4. **生產就緒**：Cloud Run 環境使用 MySQL

### **工作原理：**

1. **本地開發**：使用 SQLite，所有表自動創建
2. **Cloud Run 部署**：使用 MySQL，自動創建 `gemini_processing` 表
3. **資料庫初始化**：`tools/init_mysql_database.py` 確保所有表存在

## 🛠️ **故障排除**

### **如果出現資料庫錯誤**

1. **檢查環境變數**：
   ```bash
   python3 tools/check_cloud_run_config.py
   ```

2. **手動初始化資料庫**：
   ```bash
   python3 tools/init_mysql_database.py
   ```

3. **檢查 Cloud Run 日誌**：
   ```bash
   gcloud logs read --service=ordering-helper-backend
   ```

### **如果出現表不存在錯誤**

1. **確保 MySQL 連接正常**
2. **運行資料庫初始化腳本**
3. **檢查表是否創建成功**

## 📊 **監控與維護**

### **定期檢查項目**

- ✅ 資料庫連接狀態
- ✅ API 端點響應
- ✅ Cloud Run 服務狀態
- ✅ 錯誤日誌分析

### **備份策略**

- 定期備份 MySQL 資料庫
- 保存重要配置檔案
- 記錄部署版本

## 🎉 **完整使用者流程支援**

部署成功後，您的系統將完整支援：

1. **✅ 加入與語言設定** - LINE Bot 多語言介面
2. **✅ 店家探索** - GPS 定位鄰近店家
3. **✅ 選擇店家 → LIFF 點餐** - 合作/非合作店家處理
4. **✅ 點餐與確認** - LIFF 介面購物車功能
5. **✅ 生成中文語音檔** - TTS API 語音合成
6. **✅ 回傳 LINE Bot** - 訂單摘要和語音檔
7. **✅ 現場點餐** - 櫃檯播放中文語音

---

**注意：** 此方案保持您的現有代碼結構，只在 Cloud Run 環境中自動創建 MySQL 表，確保與同事的資料庫環境完美配合！ 