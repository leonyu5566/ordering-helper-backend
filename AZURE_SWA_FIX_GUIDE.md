# Azure Static Web Apps 路由問題修復指南

## 問題描述

你的應用程式遇到了一個典型的 Azure Static Web Apps (SWA) 路由問題：

1. **前端部署在**: `https://green-beach-0f9762500.1.azurestaticapps.net`
2. **後端部署在**: `https://ordering-helper-backend-1095766716155.asia-east1.run.app`
3. **問題**: 前端調用 `/api/orders` 時，SWA 將其路由到自己的 Functions API，而不是你的 Cloud Run 後端

## 解決方案

### 方案1: 使用 Azure Static Web Apps 反向代理 (推薦)

#### 1. 創建 `staticwebapp.config.json` 文件

在你的前端專案根目錄創建 `staticwebapp.config.json`：

```json
{
  "routes": [
    {
      "route": "/api/*",
      "rewrite": "https://ordering-helper-backend-1095766716155.asia-east1.run.app/api/{*}"
    }
  ],
  "globalHeaders": {
    "Access-Control-Allow-Origin": "https://green-beach-0f9762500.1.azurestaticapps.net"
  },
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/images/*", "/css/*", "/js/*", "/api/*"]
  }
}
```

#### 2. 重新部署前端

將 `staticwebapp.config.json` 文件包含在你的前端部署中，然後重新部署到 Azure Static Web Apps。

#### 3. 前端代碼保持不變

你的前端代碼可以繼續使用相對路徑：

```javascript
// 這樣就可以正常工作
const response = await fetch('/api/orders/simple', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(orderData)
});
```

### 方案2: 直接調用 Cloud Run URL

如果反向代理方案有問題，可以修改前端代碼直接調用 Cloud Run：

```javascript
const CLOUD_RUN_URL = 'https://ordering-helper-backend-1095766716155.asia-east1.run.app';

const response = await fetch(`${CLOUD_RUN_URL}/api/orders/simple`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(orderData)
});
```

## 後端 CORS 配置

你的後端已經正確配置了 CORS，但我們進一步優化了配置：

### 更新 `app/__init__.py`

```python
allowed_origins = [
    "https://green-beach-0f9762500.1.azurestaticapps.net",
    "https://liff.line.me",  # LINE LIFF 域名
    "https://liff.line.me:443",  # LINE LIFF 域名 (HTTPS)
    "http://localhost:3000",  # 本地開發
    "http://localhost:8080",  # 本地開發
    "http://127.0.0.1:3000",  # 本地開發
    "http://127.0.0.1:8080"   # 本地開發
]
```

## 測試步驟

### 1. 測試 API 連接

運行測試腳本：

```bash
python test_api_connection.py
```

### 2. 測試前端整合

使用提供的 `frontend_api_config.js` 進行測試：

```javascript
// 引入配置
import { OrderAPI, MenuAPI, StoreAPI } from './frontend_api_config.js';

// 測試訂單提交
const orderData = {
  items: [
    {
      name: "蜂蜜茶",
      quantity: 1,
      price: 100
    }
  ],
  line_user_id: "test_user_123",
  lang: "zh-TW"
};

try {
  const result = await OrderAPI.submitOrder(orderData);
  console.log('訂單提交成功:', result);
} catch (error) {
  console.error('訂單提交失敗:', error);
}
```

### 3. 瀏覽器開發者工具檢查

1. 打開瀏覽器開發者工具
2. 切換到 Network 標籤
3. 提交訂單
4. 檢查請求是否正確發送到 Cloud Run

## 常見問題

### Q1: 為什麼會出現 404 錯誤？

**A**: 這是因為 Azure Static Web Apps 將 `/api/*` 路由視為自己的 Functions API，而不是你的外部後端。

### Q2: 反向代理方案有什麼優勢？

**A**: 
- 前端代碼不需要修改
- 自動處理 CORS 問題
- 更好的安全性（請求通過 SWA 代理）

### Q3: 如何驗證配置是否正確？

**A**: 
1. 檢查 `staticwebapp.config.json` 是否在正確位置
2. 重新部署前端應用
3. 運行測試腳本
4. 檢查瀏覽器 Network 標籤

### Q4: LIFF 整合需要注意什麼？

**A**: 
- 確保在 LINE Developers 後台添加了正確的域名
- 使用 `liff.getProfile()` 獲取用戶 ID
- 在訂單中包含 `line_user_id`

## 部署檢查清單

- [ ] 創建 `staticwebapp.config.json` 文件
- [ ] 重新部署前端到 Azure Static Web Apps
- [ ] 更新後端 CORS 配置
- [ ] 重新部署後端到 Cloud Run
- [ ] 運行 API 測試腳本
- [ ] 測試前端訂單提交功能
- [ ] 檢查瀏覽器 Network 請求
- [ ] 驗證 LIFF 整合

## 監控和日誌

### Cloud Run 日誌

檢查 Cloud Run 日誌以確認請求是否到達：

```bash
gcloud logs read --service=ordering-helper-backend --limit=50
```

### 前端錯誤處理

在前端添加詳細的錯誤處理：

```javascript
try {
  const response = await fetch('/api/orders/simple', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData)
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }
  
  const result = await response.json();
  console.log('訂單提交成功:', result);
} catch (error) {
  console.error('訂單提交失敗:', error);
  // 顯示用戶友好的錯誤訊息
  alert(`訂單提交失敗: ${error.message}`);
}
```

## 總結

通過實施反向代理方案，你的前端可以繼續使用相對路徑 `/api/*`，而 Azure Static Web Apps 會自動將這些請求代理到你的 Cloud Run 後端。這樣既解決了路由問題，又保持了代碼的簡潔性。
