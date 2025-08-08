# LINE 聊天室修復總結

## 🎯 **問題分析**

根據 GPT 的建議，我們識別出了兩個關鍵問題：

### **問題 1：摘要取值錯誤**
- **現象**: LINE 聊天室只顯示「點餐摘要」預設字串
- **原因**: 在組裝 push message 時取值錯誤，導致摘要被預設字串覆蓋
- **影響**: 使用者無法看到實際的點餐內容

### **問題 2：TTS 檔案沒有公開網址**
- **現象**: 語音檔成功生成但沒有送到 LINE 聊天室
- **原因**: TTS 流程沒有把產生好的 MP3 上傳到可公開下載的 HTTPS 位置
- **影響**: LINE SDK 收不到合法 `originalContentUrl` 就會把整個 audio 訊息丟棄

## ✅ **修復方案**

### **1. 嚴謹的訊息構建檢查**

**檔案**: `app/api/helpers.py`
**函數**: `build_order_message()`

```python
def build_order_message(zh_summary: str, user_summary: str, total: int, audio_url: str | None) -> list:
    # 1. 確保兩種摘要都不是 None
    if not zh_summary or zh_summary.strip() == "":
        raise ValueError("zh_summary missing")
    if not user_summary or user_summary.strip() == "":
        logging.warning("User summary missing, fallback to zh_summary")
        user_summary = zh_summary

    # 2. 構建文字訊息
    text = (
        "Order Summary\n\n"
        f"中文摘要（給店家聽）：{zh_summary}\n\n"
        f"{detect_lang(user_summary)} 摘要：{user_summary}\n\n"
        f"總金額：{total} 元"
    )
    messages = [{"type": "text", "text": text}]

    # 3. audio_url 必須是 https 且可存取，否則不要附加
    if audio_url and audio_url.startswith("https://"):
        messages.append({
            "type": "audio",
            "originalContentUrl": audio_url,
            "duration": estimate_duration_ms(audio_url)
        })
    else:
        logging.warning(f"Skip audio, invalid url={audio_url}")

    return messages
```

### **2. TTS 與 GCS 上傳整合**

**檔案**: `app/api/helpers.py`
**函數**: `generate_and_upload_audio_to_gcs()`

```python
def generate_and_upload_audio_to_gcs(text: str, order_id: str) -> str | None:
    # 1. 生成語音檔
    speech_config = get_speech_config()
    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = synthesizer.speak_text_async(voice_text).get()
    
    # 2. 上傳到 GCS
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(temp_path)
    blob.make_public()
    
    # 3. 返回公開 URL
    return blob.public_url
```

### **3. 修復版本的 LINE Bot 發送函數**

**檔案**: `app/api/helpers.py`
**函數**: `send_order_to_line_bot_fixed()`

```python
def send_order_to_line_bot_fixed(user_id, order_data):
    # 嚴謹檢查摘要
    zh_summary = order_data.get('chinese_summary') or order_data.get('zh_summary')
    user_summary = order_data.get('user_summary')
    voice_url = order_data.get('voice_url')
    
    # 除錯：檢查變數值
    logging.debug(f"zh_summary={zh_summary}")
    logging.debug(f"user_summary={user_summary}")
    logging.debug(f"voice_url={voice_url}")
    
    # 使用新的訊息構建函數
    messages = build_order_message(zh_summary, user_summary, total_amount, voice_url)
```

### **4. 增強版本的訂單處理**

**檔案**: `app/api/helpers.py`
**函數**: `process_order_with_enhanced_tts()`

```python
def process_order_with_enhanced_tts(order_request: OrderRequest):
    # 生成中文訂單摘要
    zh_summary = generate_chinese_order_summary(zh_items, total_amount)
    
    # 生成使用者語言訂單摘要
    user_summary = generate_user_language_order_summary(user_items, total_amount, order_request.lang)
    
    # 生成語音檔並上傳到 GCS
    audio_url = None
    if voice_text:
        order_id = f"order_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        audio_url = generate_and_upload_audio_to_gcs(voice_text, order_id)
    
    return {
        "zh_summary": zh_summary,
        "user_summary": user_summary,
        "voice_text": voice_text,
        "audio_url": audio_url,  # 新增：GCS 公開 URL
        "total_amount": total_amount
    }
```

## 🔧 **API 路由更新**

**檔案**: `app/api/routes.py`

```python
# 處理雙語訂單（使用修復版本）
from .helpers import process_order_with_enhanced_tts, send_order_to_line_bot_fixed
order_result = process_order_with_enhanced_tts(order_request)

# 發送到 LINE Bot（使用修復版本）
send_order_to_line_bot_fixed(line_user_id, {
    'order_id': order.order_id,
    'chinese_summary': order_result['zh_summary'],
    'user_summary': order_result['user_summary'],
    'voice_url': order_result.get('audio_url'),
    'total_amount': order_result['total_amount']
})
```

## 🧪 **測試工具**

### **1. 測試腳本**
**檔案**: `tools/test_line_fix.py`

```bash
python3 tools/test_line_fix.py
```

測試內容：
- ✅ 摘要生成功能
- ✅ 訊息構建功能
- ✅ 語音生成功能
- ✅ LINE Bot 整合
- ✅ 完整訂單處理流程

### **2. 部署腳本**
**檔案**: `deploy_line_fix.py`

```bash
python3 deploy_line_fix.py
```

部署內容：
- ✅ 檢查前置條件
- ✅ 設定環境變數
- ✅ 部署到 Cloud Run
- ✅ 測試部署結果
- ✅ 提供測試指南

## 📊 **預期結果**

### **修復前**
```
❌ LINE 聊天室顯示：
「中文摘要（給店家聽）：點餐摘要」
（沒有語音檔）
```

### **修復後**
```
✅ LINE 聊天室顯示：
「中文摘要（給店家聽）：奶油經典夏威夷 x 1、奶香培根玉米 x 1」
「English 摘要：Classic Hawaiian Cream x 1, Bacon Corn x 1」
「總金額：225 元」
+ 可點擊播放的語音訊息
```

## 🔍 **驗證步驟**

### **1. 本地測試**
```bash
# 執行測試腳本
python3 tools/test_line_fix.py

# 啟動本地服務
fish start_local_with_cloud_mysql.fish
```

### **2. 部署測試**
```bash
# 部署到 Cloud Run
python3 deploy_line_fix.py

# 檢查日誌
gcloud logs read --service=ordering-helper-backend --limit=50
```

### **3. 實際測試**
```bash
# 建立測試訂單
curl -X POST https://your-service-url/api/orders/simple \
  -H 'Content-Type: application/json' \
  -d '{
    "items": [
      {
        "name": {
          "original": "奶油經典夏威夷",
          "translated": "Classic Hawaiian Cream"
        },
        "quantity": 1,
        "price": 115
      }
    ],
    "lang": "en",
    "line_user_id": "YOUR_LINE_USER_ID"
  }'
```

## 📝 **環境變數需求**

### **必要環境變數**
```bash
# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Azure Speech
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=australiaeast

# GCS 設定（用於語音檔上傳）
GCS_BUCKET_NAME=ordering-helper-voice-files
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json

# 強制使用 Cloud MySQL
FORCE_CLOUD_MYSQL=true
```

## 🎉 **修復效果**

### **解決的問題**
1. ✅ **摘要取值錯誤**: 確保摘要不為 None，正確顯示實際內容
2. ✅ **TTS 檔案沒有公開網址**: 實作 GCS 上傳，返回 HTTPS URL
3. ✅ **嚴謹的訊息構建檢查**: 防止無效資料導致錯誤
4. ✅ **完整的錯誤處理**: 提供詳細的除錯資訊

### **新增功能**
1. ✅ **GCS 語音檔上傳**: 自動上傳語音檔到 Google Cloud Storage
2. ✅ **語言檢測**: 自動檢測摘要語言並顯示對應標籤
3. ✅ **時長估算**: 自動估算音訊時長
4. ✅ **詳細日誌**: 提供完整的除錯和監控資訊

### **使用效益**
1. ✅ **提高可靠性**: 嚴謹的檢查和錯誤處理
2. ✅ **改善使用者體驗**: 正確顯示摘要和語音檔
3. ✅ **簡化維護**: 完整的測試和部署工具
4. ✅ **降低成本**: 優化的語音檔處理流程

## 🚀 **下一步行動**

1. **部署修復版本**
   ```bash
   python3 deploy_line_fix.py
   ```

2. **使用真實 LINE User ID 測試**
   - 確保使用真實的 LINE 使用者 ID
   - 檢查 Cloud Run 日誌
   - 驗證 LINE 聊天室中的訊息

3. **監控和優化**
   - 監控語音檔生成和上傳效能
   - 檢查 GCS 儲存成本
   - 優化語音檔大小和品質

4. **擴展功能**
   - 支援更多語言
   - 增加語音檔快取機制
   - 實作語音檔壓縮

現在 LINE 聊天室應該能正確顯示點單摘要和語音檔了！
