# Google GenAI SDK 更新總結

## 問題描述

在 Cloud Run 日誌中發現兩個關鍵錯誤：
1. **`unexpected keyword argument 'response_schema'`**（舊錯誤）
2. **`Extra inputs are not permitted … input_value={'type': 'json_object'}`**（新錯誤）

這些錯誤都指向同一個問題：**後端使用的 Google Gemini Python SDK 版本太舊**，Pydantic 驗證時認不出傳入的欄位，導致整個 `GenerateContentConfig` 被擋下來，最後前端收到 422 錯誤。

## 解決方案

### 1. SDK 版本確認

檢查 `requirements.txt`，確認已使用正確的新版 SDK：
```txt
google-genai==1.28.0  # ✅ 正確的新版 SDK
```

### 2. API 呼叫格式更新

將所有舊版的 `GenerateContentConfig` 格式更新為新版格式：

#### 舊版格式（已移除）
```python
config=genai.types.GenerateContentConfig(
    response_format={"type": "json_object"},  # ❌ 舊版格式
    thinking_config=genai.types.ThinkingConfig(thinking_budget=256)
)
```

#### 新版格式（已更新）
```python
config={
    "response_mime_type": "application/json",  # ✅ 新版 JSON Mode
    "thinking_config": genai.types.ThinkingConfig(thinking_budget=256)
}
```

### 3. 修改的檔案清單

以下檔案已更新為新版 API 格式：

#### 需要 JSON 輸出的檔案
- `app/api/helpers.py` - 主要菜單 OCR 處理
- `langchain_menu_enhancement.py` - 菜單增強處理
- `app/langchain_integration.py` - 整合處理（2處）
- `app/webhook/routes.py` - Webhook 推薦處理

#### 一般文字處理檔案
- `app/langchain_acceleration.py` - 加速處理（2處）
- `app/langchain_enhancement.py` - 增強處理（3處）
- `app/webhook/routes.py` - 測試和翻譯處理
- `app/api/helpers.py` - 翻譯處理

### 4. 新版 API 參數說明

#### JSON Mode
```python
config={
    "response_mime_type": "application/json"  # 保證回傳合法 JSON
}
```

#### Schema Mode（可選）
```python
from pydantic import BaseModel

class MenuItem(BaseModel):
    name: str
    price: int

config={
    "response_mime_type": "application/json",
    "response_schema": MenuItem  # 強制遵循 schema
}
```

### 5. CORS 設定確認

確認 `app/__init__.py` 中的 CORS 設定已正確：
```python
allowed_origins = [
    "https://green-beach-0f9762500.1.azurestaticapps.net",
    "https://*.azurestaticapps.net",  # 允許所有 Azure 靜態網頁
    "http://localhost:3000",  # 本地開發
    "http://localhost:8080",  # 本地開發
    "http://127.0.0.1:3000",  # 本地開發
    "http://127.0.0.1:8080"   # 本地開發
]
```

## 部署步驟

### 1. 本地測試
```bash
# 設定環境變數
export GEMINI_API_KEY="your-api-key"

# 執行測試
python test_sdk_update.py
```

### 2. 重新部署到 Cloud Run
```bash
# 執行部署腳本
chmod +x deploy_updated_sdk.sh
./deploy_updated_sdk.sh
```

### 3. 驗證部署
```bash
# 查看服務狀態
gcloud run services describe ordering-helper-backend --region=asia-east1

# 查看日誌
gcloud logs read --project=ordering-helper-backend-456789 --filter resource.type=cloud_run_revision --limit=50
```

## 預期結果

部署完成後，Cloud Run 日誌應該不再出現：
- ❌ `unexpected keyword argument 'response_schema'`
- ❌ `Extra inputs are not permitted … input_value={'type': 'json_object'}`

前端應該能夠正常：
- ✅ 上傳菜單圖片
- ✅ 收到正確的 JSON 回應
- ✅ 不再收到 422 錯誤

## 測試建議

1. **本地測試**：使用 `test_sdk_update.py` 驗證 SDK 更新
2. **部署測試**：重新部署後測試菜單上傳功能
3. **日誌監控**：觀察 Cloud Run 日誌是否還有錯誤
4. **前端測試**：確認前端能正常接收回應

## 注意事項

1. **向後相容性**：新版 SDK 與舊版不完全相容
2. **環境變數**：確保所有必要的環境變數都已設定
3. **記憶體使用**：Cloud Run 設定為 2Gi 記憶體，確保足夠處理圖片
4. **超時設定**：設定 300 秒超時，避免長時間處理被中斷

## 相關文件

- [Google AI for Developers - Structured output](https://ai.google.dev/gemini-api/docs/structured-output)
- [Google AI for Developers - Migrate to the Google GenAI SDK](https://ai.google.dev/gemini-api/docs/migrate)
- [GitHub - Vertex AI Samples Issue #3322](https://github.com/GoogleCloudPlatform/vertex-ai-samples/issues/3322) 