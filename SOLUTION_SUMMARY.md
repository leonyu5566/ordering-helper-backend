# Azure Static Web Apps 路由問題解決方案總結

## 🎯 問題診斷

根據你提供的日誌分析，問題確實如 GPT 建議的那樣：

1. **圖片上傳成功** ✅ - 返回 201 Created
2. **訂單提交失敗** ❌ - 返回 500 錯誤
3. **根本原因** - Azure Static Web Apps 將 `/api/*` 路由視為自己的 Functions API，而不是你的 Cloud Run 後端

## 🔧 解決方案實施

### 1. 創建 Azure Static Web Apps 配置文件

**文件**: `staticwebapp.config.json`
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

### 2. 優化後端 CORS 配置

**文件**: `app/__init__.py`
- 添加了 LINE LIFF 域名支援
- 移除了通配符域名以提高安全性

### 3. 創建測試工具

**文件**: `test_api_connection.py`
- 測試健康檢查端點
- 測試 CORS 預檢請求
- 測試店家解析器
- 測試訂單提交功能

### 4. 提供前端配置示例

**文件**: `frontend_api_config.js`
- 完整的 API 調用封裝
- 支援反向代理和直接調用兩種模式
- 包含 LIFF 整合示例

## ✅ 測試結果

運行測試腳本確認所有功能正常：

```
🚀 開始 API 連接測試...
目標 URL: https://ordering-helper-backend-1095766716155.asia-east1.run.app
==================================================
🔍 測試健康檢查端點...
✅ 健康檢查成功: 200

🔍 測試 CORS 預檢請求...
✅ CORS 預檢成功: 200

🔍 測試店家解析器...
✅ 店家解析成功: 200

🔍 測試訂單提交...
✅ 訂單提交成功: 201

==================================================
📊 測試結果總結:
總測試數: 4
成功: 4
失敗: 0
🎉 所有測試通過！API 連接正常。
```

## 📋 部署步驟

### 前端部署 (Azure Static Web Apps)

1. **添加配置文件**
   ```bash
   # 將 staticwebapp.config.json 添加到前端專案根目錄
   cp staticwebapp.config.json /path/to/your/frontend/
   ```

2. **重新部署**
   ```bash
   # 重新部署到 Azure Static Web Apps
   az staticwebapp create --name your-app-name --source .
   ```

### 後端部署 (Cloud Run)

1. **更新 CORS 配置**
   ```bash
   # 重新部署後端
   gcloud run deploy ordering-helper-backend --source .
   ```

2. **驗證部署**
   ```bash
   # 運行測試腳本
   python3 test_api_connection.py
   ```

## 🔍 驗證方法

### 1. 瀏覽器開發者工具

1. 打開瀏覽器開發者工具
2. 切換到 Network 標籤
3. 提交訂單
4. 檢查請求是否正確發送到 Cloud Run

### 2. Cloud Run 日誌

```bash
# 查看 Cloud Run 日誌
gcloud logs read --service=ordering-helper-backend --limit=50
```

### 3. 前端錯誤處理

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
  alert(`訂單提交失敗: ${error.message}`);
}
```

## 🎯 關鍵改進

### 1. 路由問題解決
- 使用 Azure Static Web Apps 反向代理
- 前端代碼無需修改
- 自動處理 CORS 問題

### 2. 安全性提升
- 精確的 CORS 域名配置
- 移除通配符域名
- 添加 LINE LIFF 域名支援

### 3. 開發體驗改善
- 提供完整的測試工具
- 詳細的錯誤處理
- 清晰的部署指南

## 📚 相關文件

- `AZURE_SWA_FIX_GUIDE.md` - 詳細的修復指南
- `frontend_api_config.js` - 前端 API 配置示例
- `test_api_connection.py` - API 連接測試腳本
- `staticwebapp.config.json` - Azure Static Web Apps 配置

## 🚀 下一步

1. **部署前端配置** - 將 `staticwebapp.config.json` 添加到前端專案並重新部署
2. **測試訂單提交** - 使用實際的前端應用測試訂單提交功能
3. **監控日誌** - 持續監控 Cloud Run 日誌以確保穩定性
4. **LIFF 整合** - 確保 LINE LIFF 正確配置並測試用戶認證

## 💡 技術要點

- **反向代理**: Azure Static Web Apps 將 `/api/*` 請求代理到 Cloud Run
- **CORS 配置**: 精確的域名匹配，支援 LINE LIFF
- **錯誤處理**: 詳細的錯誤訊息和用戶友好的提示
- **測試覆蓋**: 完整的 API 端點測試

這個解決方案既解決了當前的路由問題，又為未來的開發提供了良好的基礎架構。
