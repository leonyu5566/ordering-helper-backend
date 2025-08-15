# URL 配置管理指南
### **1. 建立統一的 URL 配置模組**

已建立 `app/config/urls.py` 檔案，提供統一的 URL 管理：

```python
from app.config import URLConfig

# 取得基礎 URL
base_url = URLConfig.get_base_url()

# 取得語音檔 URL
voice_url = URLConfig.get_voice_url(filename)

# 取得 API 基礎 URL
api_url = URLConfig.get_api_base_url()
```

### **2. 環境變數配置**

在 Cloud Run 環境變數中設定：

```bash
BASE_URL=https://your-new-domain.com
```

### **3. 支援的 URL 類型**

- `URLConfig.get_base_url()` - 基礎 URL
- `URLConfig.get_api_base_url()` - API 基礎 URL
- `URLConfig.get_voice_url(filename)` - 語音檔 URL
- `URLConfig.get_webhook_url()` - Webhook URL
- `URLConfig.get_health_check_url()` - 健康檢查 URL
- `URLConfig.get_stores_url()` - 店家列表 URL
- `URLConfig.get_menu_url(store_id)` - 菜單 URL
- `URLConfig.get_order_url(order_id)` - 訂單 URL
- `URLConfig.get_upload_url()` - 上傳 URL

### **4. 環境檢測功能**

```python
# 檢查是否為生產環境
if URLConfig.is_production():
    print("生產環境")

# 檢查是否部署在 Cloud Run
if URLConfig.is_cloud_run():
    print("Cloud Run 環境")
```

## 📝 **使用範例**

### **原本的寫法（不推薦）**
```python
base_url = os.getenv('BASE_URL', 'https://ordering-helper-backend-1095766716155.asia-east1.run.app')
audio_url = f"{base_url}/api/voices/{fname}"
```

### **新的寫法（推薦）**
```python
from app.config import URLConfig
audio_url = URLConfig.get_voice_url(fname)
```

## 🔄 **修改 URL 的方法**

### **方法 1：環境變數（推薦）**
```bash
# 在 Cloud Run 中設定環境變數
BASE_URL=https://your-new-domain.com
```

### **方法 2：修改配置檔案**
編輯 `app/config/urls.py` 中的 `DEFAULT_CLOUD_RUN_URL`：

```python
DEFAULT_CLOUD_RUN_URL = "https://your-new-domain.com"
```

## ✅ **已更新的檔案**

- ✅ `app/api/routes.py` - 語音生成 API
- ✅ `app/api/helpers.py` - 語音處理函數
- ✅ `app/webhook/routes.py` - Webhook 處理
- ✅ `app/config/urls.py` - 新增 URL 配置模組
- ✅ `app/config/__init__.py` - 配置模組初始化

## 🎉 **優點**

1. **集中管理**：所有 URL 配置都在一個地方
2. **易於維護**：修改 URL 只需要改一個地方
3. **環境支援**：支援不同環境的 URL 配置
4. **類型安全**：提供明確的 API 介面
5. **向後相容**：保持原有功能不變

## 🚀 **下一步**

1. 部署更新後的程式碼
2. 在 Cloud Run 中設定 `BASE_URL` 環境變數
3. 測試所有功能正常運作
