# 語音檔回傳問題修復總結

## 🔍 問題診斷

根據GPT的建議，我們系統性地檢查了語音檔回傳問題的每個環節：

### 1. 發現的主要問題

#### ❌ 問題1：錯誤的URL格式
- **位置**：`app/api/helpers.py` 第831行
- **問題**：使用了 `f"file://{voice_result}"` 而不是HTTPS URL
- **影響**：LINE Bot無法訪問語音檔

#### ❌ 問題2：缺少ResultReason導入
- **位置**：多個語音生成函數
- **問題**：`ResultReason` 沒有被正確導入
- **影響**：語音生成失敗

#### ❌ 問題3：過早清理語音檔案
- **位置**：`send_complete_order_notification` 函數
- **問題**：在語音發送後立即刪除檔案
- **影響**：靜態路由無法找到檔案

## ✅ 已修復的問題

### 1. 修復URL構建邏輯
```python
# 修復前
original_content_url=f"file://{voice_result}"

# 修復後
fname = os.path.basename(voice_result)
base_url = os.getenv('BASE_URL', 'https://ordering-helper-backend-1095766716155.asia-east1.run.app')
audio_url = f"{base_url}/api/voices/{fname}"
original_content_url=audio_url
```

### 2. 添加ResultReason導入
```python
# 修復前
from azure.cognitiveservices.speech import SpeechSynthesizer, AudioConfig

# 修復後
from azure.cognitiveservices.speech import SpeechSynthesizer, AudioConfig, ResultReason
```

### 3. 移除過早清理邏輯
```python
# 修復前
# 6. 清理語音檔案
if voice_result and isinstance(voice_result, str) and os.path.exists(voice_result):
    try:
        os.remove(voice_result)
        print(f"語音檔案已清理: {voice_result}")
    except Exception as e:
        print(f"清理語音檔案失敗: {e}")

# 修復後
# 6. 不立即清理語音檔案，讓靜態路由服務
# 語音檔案會在30分鐘後由cleanup_old_voice_files自動清理
```

### 4. 添加詳細日誌
```python
# 添加語音生成日誌
print(f"[TTS] Will save to {audio_path}")
print(f"[TTS] Success, file exists? {os.path.exists(audio_path)}")

# 添加URL構建日誌
print(f"[Webhook] Reply with voice URL: {audio_url}")
```

### 5. 修復靜態路由導入
```python
# 修復前
@api_bp.route('/voices/<path:filename>')
def serve_voice(filename):
    return send_from_directory(VOICE_DIR, filename, mimetype='audio/wav')

# 修復後
@api_bp.route('/voices/<path:filename>')
def serve_voice(filename):
    from .helpers import VOICE_DIR
    return send_from_directory(VOICE_DIR, filename, mimetype='audio/wav')
```

## 🧪 測試結果

### 本地測試成功
- ✅ 語音檔生成：成功
- ✅ 檔案格式：正確的WAV格式
- ✅ 靜態路由：本地測試成功
- ✅ 檔案權限：正常

### 測試腳本
- `test_voice_generation.py`：測試語音生成和URL構建
- `test_static_route.py`：測試靜態路由功能

## 🔧 修復的函數

1. `send_complete_order_notification()` - 主要語音發送函數
2. `send_voice_with_rate()` - 語速控制函數
3. `send_temp_order_notification()` - 臨時訂單語音函數
4. `send_order_to_line_bot()` - LINE Bot整合函數
5. `generate_voice_order()` - 語音生成函數
6. `generate_voice_from_temp_order()` - 臨時訂單語音生成
7. `generate_voice_with_custom_rate()` - 自定義語音生成
8. `generate_chinese_voice_with_azure()` - Azure語音生成
9. `serve_voice()` - 靜態路由服務

## 🚀 部署建議

### 1. 環境變數檢查
確保Cloud Run環境中設定了以下變數：
```bash
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=australiaeast
BASE_URL=https://ordering-helper-backend-1095766716155.asia-east1.run.app
```

### 2. 部署後驗證
部署後請檢查：
1. 應用程式日誌中的語音生成訊息
2. 靜態路由是否可訪問
3. LINE Bot是否能正確接收語音檔

### 3. 監控建議
- 監控 `/tmp/voices` 目錄中的檔案數量
- 檢查語音檔案的生成和清理週期
- 監控靜態路由的訪問日誌

## 📋 待驗證項目

1. **Cloud Run部署測試**：確認修復在生產環境中生效
2. **LINE Bot整合測試**：確認語音檔能正確發送到LINE
3. **語音控制按鈕測試**：確認不同語速的語音播放功能
4. **檔案清理機制**：確認30分鐘自動清理功能正常

## 🎯 預期結果

修復後，語音檔回傳流程應該是：
1. 生成語音檔 → `/tmp/voices/xxx.wav`
2. 構建HTTPS URL → `https://domain.com/api/voices/xxx.wav`
3. 發送到LINE Bot → `AudioSendMessage(original_content_url=url)`
4. LINE Bot訪問URL → 靜態路由返回WAV檔案
5. 用戶聽到語音 → 成功播放

## 📞 下一步

如果部署後仍有問題，請提供：
1. Cloud Run應用程式日誌
2. 靜態路由訪問測試結果
3. LINE Bot客戶端錯誤訊息 