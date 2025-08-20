# LIFF 輪詢架構實作指南

## 📋 概述

本文件說明為了解決 LIFF 環境中的長時間等待問題，所實作的「短請求 + 輪詢」新架構。

## 🎯 問題分析

### 原始問題
- **LIFF 環境限制**: LINE 的 LIFF 環境對長時間請求有 30-40 秒的延遲
- **使用者體驗差**: 使用者點擊確認後需要等待很長時間，感覺像當機
- **超時風險**: 長時間等待可能導致請求超時或失敗

### 根本原因
1. **同步等待模式**: 前端發送請求後等待所有處理完成
2. **耗時操作**: 語音生成、LINE 通知等操作需要數秒到數十秒
3. **LIFF 節流**: LINE 平台對長時間請求進行節流處理

## 🏗️ 新架構設計

### 架構流程

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 (LIFF)   │    │   後端 API      │    │   背景處理      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │ 1. 快速建立訂單       │                       │
         │ (1-2秒回應)          │                       │
         ├──────────────────────►│                       │
         │                       │                       │
         │ 2. 返回 order_id      │                       │
         │                       │                       │
         │◄──────────────────────┤                       │
         │                       │                       │
         │ 3. 開始輪詢狀態       │                       │
         │ (每2秒一次)          │                       │
         ├──────────────────────►│                       │
         │                       │                       │
         │ 4. 返回處理狀態       │                       │
         │                       │                       │
         │◄──────────────────────┤                       │
         │                       │                       │
         │                       │ 5. 背景處理任務       │
         │                       │ (語音生成、通知)      │
         │                       ├──────────────────────►│
         │                       │                       │
         │                       │ 6. 更新訂單狀態       │
         │                       │                       │
         │                       │◄──────────────────────┤
         │                       │                       │
         │ 7. 輪詢到完成狀態     │                       │
         │                       │                       │
         │◄──────────────────────┤                       │
         │                       │                       │
```

### 核心組件

#### 1. 快速訂單建立端點
- **路徑**: `POST /api/orders/quick`
- **功能**: 只建立訂單記錄，不處理語音和通知
- **回應時間**: 1-2 秒
- **返回資料**: `order_id`, `status`, `polling_url`

#### 2. 訂單狀態查詢端點
- **路徑**: `GET /api/orders/status/{order_id}`
- **功能**: 查詢訂單處理狀態和結果
- **回應時間**: < 1 秒
- **返回資料**: 訂單狀態、語音 URL、摘要等

#### 3. 背景處理任務
- **函式**: `process_order_background(order_id)`
- **功能**: 在背景執行緒中處理耗時操作
- **包含操作**:
  - 生成語音檔案
  - 發送 LINE 通知
  - 建立訂單摘要
  - 更新訂單狀態

#### 4. 前端輪詢機制
- **輪詢間隔**: 2 秒
- **最大輪詢次數**: 30 次（60 秒）
- **進度顯示**: 進度條和狀態更新
- **錯誤處理**: 超時和重試機制

## 🔧 實作細節

### 後端實作

#### 快速訂單建立端點
```python
@app.route('/api/orders/quick', methods=['POST'])
def create_quick_order():
    # 1. 驗證請求資料
    # 2. 建立訂單記錄 (status='pending')
    # 3. 啟動背景處理任務
    # 4. 立即返回 order_id
```

#### 訂單狀態查詢端點
```python
@app.route('/api/orders/status/<int:order_id>', methods=['GET'])
def get_order_status(order_id):
    # 1. 查詢訂單狀態
    # 2. 根據狀態返回不同資料
    # 3. 包含語音 URL 和摘要資訊
```

#### 背景處理任務
```python
def process_order_background(order_id):
    # 1. 生成語音檔案
    # 2. 發送 LINE 通知
    # 3. 更新訂單狀態為 'completed'
    # 4. 錯誤處理和狀態更新
```

### 前端實作

#### 輪詢機制
```javascript
function startPollingOrderStatus(orderId) {
    const pollInterval = setInterval(async () => {
        const status = await checkOrderStatus(orderId);
        
        if (status.processing === false) {
            clearInterval(pollInterval);
            showResultPage(status);
        } else {
            updateWaitingProgress();
        }
    }, 2000);
}
```

#### 等待頁面
```javascript
function showWaitingPage(orderId) {
    // 顯示進度條和處理中訊息
    // 提供即時反饋給使用者
}
```

## 📊 效能比較

### 原始架構
- **回應時間**: 30-40 秒
- **使用者體驗**: 差（感覺當機）
- **成功率**: 低（容易超時）
- **錯誤處理**: 困難

### 新架構
- **初始回應**: 1-2 秒
- **使用者體驗**: 優（即時反饋）
- **成功率**: 高（避免超時）
- **錯誤處理**: 完善

## 🧪 測試指南

### 1. 快速訂單建立測試
```bash
curl -X POST https://your-domain.com/api/orders/quick \
  -H "Content-Type: application/json" \
  -d '{
    "store_name": "測試店家",
    "items": [{"item_name": "測試商品", "price": 100, "quantity": 1}],
    "total_amount": 100
  }'
```

### 2. 訂單狀態查詢測試
```bash
curl https://your-domain.com/api/orders/status/123
```

### 3. 前端整合測試
1. 載入 `frontend_polling_example.js`
2. 點擊確認訂單按鈕
3. 觀察輪詢過程和結果顯示

## 🚀 部署指南

### 1. 部署後端
```bash
./deploy_polling_architecture.sh
```

### 2. 更新前端
將 `frontend_polling_example.js` 整合到您的 LIFF 前端專案中。

### 3. 配置設定
- 更新 `API_BASE_URL` 為您的 Cloud Run 網址
- 調整 `POLLING_INTERVAL` 和 `MAX_POLLING_ATTEMPTS` 參數

## 📈 監控和維護

### 日誌監控
- 快速訂單建立: `🚀 快速訂單建立請求`
- 背景處理: `🔄 開始背景處理訂單`
- 狀態查詢: `🔍 查詢訂單狀態`

### 效能指標
- 快速訂單建立時間: 目標 < 2 秒
- 背景處理時間: 目標 < 30 秒
- 輪詢成功率: 目標 > 95%

### 錯誤處理
- 訂單建立失敗: 立即返回錯誤
- 背景處理失敗: 更新狀態為 'failed'
- 輪詢超時: 顯示重試選項

## 🎯 預期效果

### 使用者體驗改善
1. **即時反饋**: 1-2 秒內看到處理中畫面
2. **進度顯示**: 清楚知道處理進度
3. **穩定可靠**: 避免超時和失敗
4. **完整功能**: 語音和通知正常運作

### 技術效益
1. **繞過 LIFF 限制**: 避免長時間請求被節流
2. **提高成功率**: 減少超時和錯誤
3. **易於維護**: 清晰的錯誤處理和日誌
4. **可擴展性**: 背景處理可獨立擴展

## 🔄 未來優化

### 短期優化
1. **WebSocket 支援**: 替代輪詢，提供即時推送
2. **快取機制**: 快取常用資料，提高查詢速度
3. **重試機制**: 自動重試失敗的背景任務

### 長期優化
1. **微服務架構**: 將背景處理拆分為獨立服務
2. **訊息佇列**: 使用 Redis 或 Cloud Tasks 處理背景任務
3. **監控儀表板**: 即時監控系統效能和錯誤率

---

## 📞 支援

如有問題或需要協助，請參考：
- 後端程式碼: `app/api/routes.py`, `app/api/helpers.py`
- 前端範例: `frontend_polling_example.js`
- 部署腳本: `deploy_polling_architecture.sh`
