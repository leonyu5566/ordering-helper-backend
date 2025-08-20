# Cloud Tasks 設定指南

## 1. 在 Google Cloud Console 中創建佇列

### 步驟 1：開啟 Cloud Tasks
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 選擇您的專案：`solid-heaven-466011-d1`
3. 在左側選單中找到 **Cloud Tasks**
4. 點擊 **創建佇列**

### 步驟 2：設定佇列
- **佇列名稱**：`order-processing-queue`
- **位置**：`asia-east1` (與您的 Cloud Run 服務相同)
- **最大並發數**：`10` (可根據需求調整)
- **最大重試次數**：`5`
- **重試間隔**：`10 秒`

### 步驟 3：設定服務帳戶
- 確保 Cloud Tasks 有權限調用您的 Cloud Run 服務
- 服務帳戶需要 `Cloud Tasks Invoker` 角色

**重要：** 您提供的服務帳戶 `tasks-invoker@solid-heaven-466011-d1.iam.gserviceaccount.com` 已經在配置檔案中設定好了。

## 2. 設定 Cloud Run 服務權限

### 步驟 1：啟用 Cloud Tasks API
```bash
gcloud services enable cloudtasks.googleapis.com
```

### 步驟 2：設定服務帳戶權限
```bash
# 獲取 Cloud Run 服務的服務帳戶
gcloud run services describe ordering-helper-backend \
    --region=asia-east1 \
    --format="value(spec.template.spec.serviceAccountName)"

# 授予 Cloud Tasks 權限
gcloud projects add-iam-policy-binding solid-heaven-466011-d1 \
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT@solid-heaven-466011-d1.iam.gserviceaccount.com" \
    --role="roles/cloudtasks.taskRunner"
```

## 3. 驗證設定

### 測試 Cloud Tasks 連接
```bash
# 列出佇列
gcloud tasks queues list --location=asia-east1

# 查看佇列詳細資訊
gcloud tasks queues describe order-processing-queue --location=asia-east1
```

## 4. 程式碼中的設定

### 重要參數
- **專案 ID**：`solid-heaven-466011-d1`
- **佇列名稱**：`order-processing-queue`
- **位置**：`asia-east1`
- **目標 URL**：`https://ordering-helper-backend-00690-mh5-asia-east1.run.app/api/orders/process-task`

### 注意事項
1. 確保 Cloud Run 服務的 URL 是正確的
2. 確保服務帳戶有適當的權限
3. 測試時可以查看 Cloud Tasks 的日誌來確認任務是否被正確執行

## 5. 故障排除

### 常見問題
1. **權限錯誤**：確保服務帳戶有 `Cloud Tasks Invoker` 角色
2. **URL 錯誤**：確保目標 URL 是正確的 Cloud Run 服務 URL
3. **佇列不存在**：確保佇列名稱和位置正確

### 查看日誌
```bash
# 查看 Cloud Tasks 日誌
gcloud logging read "resource.type=cloud_tasks_queue" --limit=50

# 查看 Cloud Run 日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ordering-helper-backend" --limit=50
```
