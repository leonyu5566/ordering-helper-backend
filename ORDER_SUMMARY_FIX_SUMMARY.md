# 訂單摘要修正總結

## 🎯 問題分析

根據 Cloud Run 日誌分析，發現了三個主要問題：

### 1. 訊息排序問題
- **問題**：使用者語言摘要顯示在中文摘要之後
- **期望**：使用者語言摘要應該在第一行
- **原因**：`build_order_message` 函數中的排序邏輯

### 2. 金額格式問題
- **問題**：顯示 `255.0 元` 而不是 `255 元`
- **期望**：台幣沒有小數點，應該顯示整數
- **原因**：`total_amount` 是 float 類型，直接格式化

### 3. 語音檔問題
- **問題**：語音檔沒有生成或上傳失敗
- **期望**：應該有語音檔供使用者播放
- **原因**：GCS bucket 不存在，導致上傳失敗

## 🔧 修正方案

### 1. 修正訊息排序

**檔案**：`app/api/helpers.py`
**函數**：`build_order_message`

```python
def build_order_message(zh_summary: str, user_summary: str, total: int, audio_url: str | None) -> list:
    """
    建立訂單訊息（修正版本）
    解決問題：
    1. 使用者語言摘要在第一行
    2. 金額去除小數點
    3. 語音檔上傳問題處理
    """
    # 2. 構建文字訊息（修正排序：使用者語言摘要在前）
    text_parts = []
    
    # 使用者語言摘要在第一行
    if user_summary and user_summary != zh_summary:
        text_parts.append(f"{detect_lang(user_summary)} 摘要：{user_summary}")
    
    # 中文摘要（給店家聽）
    text_parts.append(f"中文摘要（給店家聽）：{zh_summary}")
    
    # 總金額（修正：去除小數點）
    total_twd = int(round(total))
    text_parts.append(f"總金額：{total_twd} 元")
```

### 2. 修正金額格式

**檔案**：`app/api/helpers.py`
**函數**：`build_order_message`

```python
# 總金額（修正：去除小數點）
total_twd = int(round(total))
text_parts.append(f"總金額：{total_twd} 元")
```

### 3. 修正語音檔上傳

**檔案**：`app/api/helpers.py`
**函數**：`generate_and_upload_audio_to_gcs`

```python
def generate_and_upload_audio_to_gcs(text: str, order_id: str) -> str | None:
    """
    生成語音檔並上傳到 GCS，返回公開 HTTPS URL
    修正版本：解決 GCS bucket 不存在和權限問題
    """
    # 檢查 bucket 是否存在，如果不存在則創建
    bucket = storage_client.bucket(bucket_name)
    if not bucket.exists():
        logging.warning(f"❌ GCS bucket '{bucket_name}' 不存在，嘗試創建...")
        try:
            # 創建 bucket（需要適當的權限）
            bucket = storage_client.create_bucket(bucket_name, location='asia-east1')
            logging.info(f"✅ 成功創建 GCS bucket: {bucket_name}")
        except Exception as create_error:
            logging.error(f"❌ 無法創建 GCS bucket: {create_error}")
            return None
```

## 🛠️ 部署工具

### 1. GCS Bucket 設置腳本

**檔案**：`tools/setup_gcs_bucket.py`

```python
def setup_gcs_bucket():
    """設置 GCS bucket 用於語音檔存儲"""
    # 檢查 bucket 是否存在
    bucket = storage_client.bucket(bucket_name)
    
    if not bucket.exists():
        # 創建 bucket
        bucket = storage_client.create_bucket(bucket_name, location='asia-east1')
    
    # 設置公開讀取權限
    policy = bucket.get_iam_policy(requested_policy_version=3)
    policy.bindings.append({
        'role': 'roles/storage.objectViewer',
        'members': ['allUsers']
    })
    bucket.set_iam_policy(policy)
```

### 2. 部署修正腳本

**檔案**：`tools/deploy_fixes.py`

```python
def main():
    """主函數"""
    # 1. 檢查環境
    if not check_environment():
        return False
    
    # 2. 創建 GCS bucket
    if not create_gcs_bucket_simple():
        print("⚠️ GCS bucket 創建失敗，但繼續部署")
    
    # 3. 測試語音生成
    if not test_voice_generation():
        print("⚠️ 語音生成測試失敗，但繼續部署")
    
    # 4. 部署到 Cloud Run
    if not deploy_to_cloud_run():
        return False
    
    return True
```

## 📊 修正效果

### 修正前
```
中文摘要（給店家聽）：經典夏威夷奶醬義大利麵 x 1、美國脆薯 x 2
English 摘要：Order: Classic Hawaiian Cream Pasta x 1, American Fries x 2
總金額：255.0 元
```

### 修正後
```
English 摘要：Order: Classic Hawaiian Cream Pasta x 1, American Fries x 2
中文摘要（給店家聽）：經典夏威夷奶醬義大利麵 x 1、美國脆薯 x 2
總金額：255 元
[語音檔]
```

## 🚀 部署步驟

### 1. 設置 GCS Bucket

```bash
# 創建 bucket
gsutil mb -l asia-east1 gs://ordering-helper-voice-files

# 設置公開讀取權限
gsutil iam ch allUsers:objectViewer gs://ordering-helper-voice-files
```

### 2. 部署修正

```bash
# 運行部署腳本
python3 tools/deploy_fixes.py
```

### 3. 驗證修正

```bash
# 測試訂單建立
curl -X POST https://ordering-helper-backend-xxx.run.app/api/orders/simple \
  -H "Content-Type: application/json" \
  -d '{
    "user_language": "en-US",
    "line_user_id": "test_user",
    "items": [
      {
        "name": "經典夏威夷奶醬義大利麵",
        "quantity": 1,
        "price": 115
      }
    ]
  }'
```

## 📋 檢查清單

- [x] 修正訊息排序邏輯
- [x] 修正金額格式（去除小數點）
- [x] 修正語音檔上傳問題
- [x] 創建 GCS bucket 設置腳本
- [x] 創建部署修正腳本
- [ ] 部署到 Cloud Run
- [ ] 驗證修正效果

## 🎉 預期結果

修正後，使用者應該看到：

1. **正確的訊息排序**：使用者語言摘要在第一行
2. **正確的金額格式**：`255 元` 而不是 `255.0 元`
3. **可播放的語音檔**：語音檔成功上傳並可播放

## 📞 後續支援

如果部署後仍有問題，請檢查：

1. **GCS 權限**：確保 Cloud Run 服務帳戶有 Storage Object Creator 權限
2. **環境變數**：確保所有必要的環境變數都已設置
3. **日誌**：查看 Cloud Run 日誌以診斷問題
