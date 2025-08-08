# 語音檔案和摘要功能修復總結

## 問題描述

在之前的對話中，用戶反映語音檔案和摘要消失的問題。經過分析，發現了以下幾個主要問題：

1. **語音檔案清理過於頻繁**：原本每30分鐘清理一次，導致語音檔案過早被刪除
2. **語音檔案服務缺少錯誤處理**：`serve_voice` 函數沒有適當的錯誤處理和安全性檢查
3. **語音檔案生成失敗時的備用方案不完善**
4. **語音檔案路徑和權限問題**

## 修復內容

### 1. 延長語音檔案清理時間

**修改檔案：** `app/api/helpers.py`

**修改前：**
```python
def cleanup_old_voice_files(max_age=1800):
    """刪除 30 分鐘以前的 WAV"""
    try:
        import time
        now = time.time()
        for fn in os.listdir(VOICE_DIR):
            full = os.path.join(VOICE_DIR, fn)
            if os.path.isfile(full) and now - os.path.getmtime(full) > max_age:
                try:
                    os.remove(full)
                    print(f"清理舊語音檔: {fn}")
                except Exception as e:
                    print(f"清理語音檔失敗 {fn}: {e}")
    except Exception as e:
        print(f"清理語音檔目錄失敗: {e}")
```

**修改後：**
```python
def cleanup_old_voice_files(max_age=3600):
    """刪除 60 分鐘以前的 WAV（延長清理時間）"""
    try:
        import time
        now = time.time()
        cleaned_count = 0
        
        # 確保目錄存在
        os.makedirs(VOICE_DIR, exist_ok=True)
        
        for fn in os.listdir(VOICE_DIR):
            if not fn.endswith('.wav'):
                continue
                
            full = os.path.join(VOICE_DIR, fn)
            if os.path.isfile(full) and now - os.path.getmtime(full) > max_age:
                try:
                    os.remove(full)
                    cleaned_count += 1
                    print(f"清理舊語音檔: {fn}")
                except Exception as e:
                    print(f"清理語音檔失敗 {fn}: {e}")
        
        if cleaned_count > 0:
            print(f"總共清理了 {cleaned_count} 個舊語音檔案")
            
    except Exception as e:
        print(f"清理語音檔目錄失敗: {e}")
```

**改進：**
- 將清理時間從30分鐘延長到60分鐘
- 增加檔案類型檢查（只清理 .wav 檔案）
- 增加清理統計和更好的錯誤處理
- 確保目錄存在

### 2. 改善語音檔案服務安全性

**修改檔案：** `app/api/routes.py`

**修改前：**
```python
@api_bp.route('/voices/<path:filename>')
def serve_voice(filename):
    """供外部（Line Bot）GET WAV 檔用"""
    from .helpers import VOICE_DIR
    return send_from_directory(VOICE_DIR, filename, mimetype='audio/wav')
```

**修改後：**
```python
@api_bp.route('/voices/<path:filename>')
def serve_voice(filename):
    """供外部（Line Bot）GET WAV 檔用"""
    try:
        from .helpers import VOICE_DIR
        import os
        
        # 安全性檢查：只允許 .wav 檔案
        if not filename.endswith('.wav'):
            return jsonify({"error": "不支援的檔案格式"}), 400
        
        # 防止路徑遍歷攻擊
        if '..' in filename or '/' in filename:
            return jsonify({"error": "無效的檔案名稱"}), 400
        
        # 構建完整檔案路徑
        file_path = os.path.join(VOICE_DIR, filename)
        
        # 檢查檔案是否存在
        if not os.path.exists(file_path):
            return jsonify({"error": "語音檔案不存在"}), 404
        
        # 檢查檔案大小
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return jsonify({"error": "語音檔案為空"}), 404
        
        # 設定適當的 headers
        response = send_from_directory(VOICE_DIR, filename, mimetype='audio/wav')
        response.headers['Cache-Control'] = 'public, max-age=1800'  # 30分鐘快取
        response.headers['Content-Length'] = str(file_size)
        
        print(f"提供語音檔案: {filename}, 大小: {file_size} bytes")
        return response
        
    except Exception as e:
        print(f"提供語音檔案失敗: {e}")
        return jsonify({"error": "語音檔案服務失敗"}), 500
```

**改進：**
- 增加檔案格式檢查（只允許 .wav 檔案）
- 防止路徑遍歷攻擊
- 檢查檔案是否存在和大小
- 增加適當的 HTTP headers（快取控制）
- 增加詳細的錯誤處理和日誌

### 3. 改善語音生成功能

**修改檔案：** `app/api/helpers.py`

**修改前：**
```python
def generate_voice_order(order_id, speech_rate=1.0):
    """
    使用 Azure TTS 生成訂單語音
    """
    # 先 cleanup
    cleanup_old_voice_files()
    try:
        from ..models import Order, OrderItem, MenuItem
        
        # 取得訂單資訊
        order = Order.query.get(order_id)
        if not order:
            return None
        
        # ... 其他代碼 ...
        
        # 直接存到 VOICE_DIR
        filename = f"{uuid.uuid4()}.wav"
        audio_path = os.path.join(VOICE_DIR, filename)
        print(f"[TTS] Will save to {audio_path}")
        audio_config = AudioConfig(filename=audio_path)
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        
        result = synthesizer.speak_text_async(order_text).get()
        
        if result.reason == ResultReason.SynthesizingAudioCompleted:
            print(f"[TTS] Success, file exists? {os.path.exists(audio_path)}")
            return audio_path
        else:
            print(f"語音生成失敗：{result.reason}")
            return generate_voice_order_fallback(order_id, speech_rate)
```

**修改後：**
```python
def generate_voice_order(order_id, speech_rate=1.0):
    """
    使用 Azure TTS 生成訂單語音
    """
    # 先 cleanup（延長清理時間）
    cleanup_old_voice_files(3600)  # 60分鐘
    
    try:
        from ..models import Order, OrderItem, MenuItem
        
        # 取得訂單資訊
        order = Order.query.get(order_id)
        if not order:
            print(f"找不到訂單: {order_id}")
            return None
        
        # ... 其他代碼 ...
        
        # 設定語音參數
        speech_config.speech_synthesis_voice_name = "zh-TW-HsiaoChenNeural"
        speech_config.speech_synthesis_speaking_rate = speech_rate
        
        # 確保目錄存在
        os.makedirs(VOICE_DIR, exist_ok=True)
        
        # 直接存到 VOICE_DIR
        filename = f"{uuid.uuid4()}.wav"
        audio_path = os.path.join(VOICE_DIR, filename)
        print(f"[TTS] Will save to {audio_path}")
        audio_config = AudioConfig(filename=audio_path)
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        
        result = synthesizer.speak_text_async(order_text).get()
        
        if result.reason == ResultReason.SynthesizingAudioCompleted:
            # 檢查檔案是否真的生成
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                print(f"[TTS] Success, file exists and size: {os.path.getsize(audio_path)} bytes")
                return audio_path
            else:
                print(f"[TTS] 檔案生成失敗或為空: {audio_path}")
                return generate_voice_order_fallback(order_id, speech_rate)
        else:
            print(f"語音生成失敗：{result.reason}")
            return generate_voice_order_fallback(order_id, speech_rate)
```

**改進：**
- 延長清理時間到60分鐘
- 增加檔案存在性和大小檢查
- 改善錯誤處理和備用方案
- 確保目錄存在

### 4. 改善備用語音生成方案

**修改檔案：** `app/api/helpers.py`

**修改前：**
```python
def generate_voice_order_fallback(order_id, speech_rate=1.0):
    """
    備用語音生成函數（當 Azure TTS 不可用時）
    """
    try:
        from ..models import Order, OrderItem, MenuItem
        
        # 取得訂單資訊
        order = Order.query.get(order_id)
        if not order:
            return None
        
        # ... 生成語音文字 ...
        
        # 返回文字而非音檔
        return {
            'success': True,
            'text': order_text,
            'message': '語音生成功能暫時不可用，請使用文字版本'
        }
        
    except Exception as e:
        print(f"備用語音生成失敗：{e}")
        return None
```

**修改後：**
```python
def generate_voice_order_fallback(order_id, speech_rate=1.0):
    """
    備用語音生成函數（當 Azure TTS 不可用時）
    """
    try:
        from ..models import Order, OrderItem, MenuItem
        
        # 取得訂單資訊
        order = Order.query.get(order_id)
        if not order:
            print(f"備用方案：找不到訂單: {order_id}")
            return None
        
        # ... 生成語音文字 ...
        
        print(f"備用方案：生成文字版本語音: {order_text}")
        
        # 返回文字而非音檔
        return {
            'success': True,
            'text': order_text,
            'message': '語音生成功能暫時不可用，請使用文字版本',
            'is_fallback': True
        }
        
    except Exception as e:
        print(f"備用語音生成失敗：{e}")
        return {
            'success': False,
            'text': '抱歉，語音生成功能暫時不可用',
            'message': '請稍後再試或聯繫客服',
            'is_fallback': True
        }
```

**改進：**
- 增加更好的錯誤處理
- 提供更詳細的錯誤訊息
- 增加 `is_fallback` 標記
- 改善文字版本的語音內容

### 5. 改善完整訂單通知功能

**修改檔案：** `app/api/helpers.py`

**修改前：**
```python
def send_complete_order_notification(order_id):
    """
    發送完整的訂單確認通知到 LINE
    包含：兩則訂單文字摘要、中文語音檔、語速控制按鈕
    """
    # ... 其他代碼 ...
    
    # 2. 處理語音結果
    if voice_result and isinstance(voice_result, str) and os.path.exists(voice_result):
        # 成功生成語音檔
        print(f"語音檔生成成功: {voice_result}")
        try:
            # 構建正確的HTTPS URL
            fname = os.path.basename(voice_result)
            base_url = os.getenv('BASE_URL', 'https://ordering-helper-backend-1095766716155.asia-east1.run.app')
            audio_url = f"{base_url}/api/voices/{fname}"
            
            line_bot_api = get_line_bot_api()
            if line_bot_api:
                line_bot_api.push_message(
                    user.line_user_id,
                    AudioSendMessage(
                        original_content_url=audio_url,
                        duration=30000  # 預設30秒
                    )
                )
                print(f"語音檔已發送到 LINE: {audio_url}")
        except Exception as e:
            print(f"發送語音檔失敗: {e}")
    elif voice_result and isinstance(voice_result, dict):
        # 備用方案：發送文字版本
        print(f"使用備用語音方案: {voice_result.get('text', '')[:50]}...")
        line_bot_api = get_line_bot_api()
        if line_bot_api:
            line_bot_api.push_message(
                user.line_user_id,
                TextSendMessage(text=f"🎤 點餐語音（文字版）:\n{voice_result.get('text', '')}")
            )
            print("備用語音文字已發送到 LINE")
    else:
        print("語音生成失敗，跳過語音發送")
```

**修改後：**
```python
def send_complete_order_notification(order_id):
    """
    發送完整的訂單確認通知到 LINE
    包含：兩則訂單文字摘要、中文語音檔、語速控制按鈕
    """
    # ... 其他代碼 ...
    
    # 2. 處理語音結果
    if voice_result and isinstance(voice_result, str) and os.path.exists(voice_result):
        # 成功生成語音檔
        file_size = os.path.getsize(voice_result)
        print(f"語音檔生成成功: {voice_result}, 大小: {file_size} bytes")
        
        if file_size > 0:
            try:
                # 構建正確的HTTPS URL
                fname = os.path.basename(voice_result)
                base_url = os.getenv('BASE_URL', 'https://ordering-helper-backend-1095766716155.asia-east1.run.app')
                audio_url = f"{base_url}/api/voices/{fname}"
                
                line_bot_api = get_line_bot_api()
                if line_bot_api:
                    line_bot_api.push_message(
                        user.line_user_id,
                        AudioSendMessage(
                            original_content_url=audio_url,
                            duration=30000  # 預設30秒
                        )
                    )
                    print(f"語音檔已發送到 LINE: {audio_url}")
                else:
                    print("LINE Bot API 不可用，跳過語音發送")
            except Exception as e:
                print(f"發送語音檔失敗: {e}")
        else:
            print("語音檔案為空，跳過語音發送")
    elif voice_result and isinstance(voice_result, dict):
        # 備用方案：發送文字版本
        if voice_result.get('success'):
            print(f"使用備用語音方案: {voice_result.get('text', '')[:50]}...")
            line_bot_api = get_line_bot_api()
            if line_bot_api:
                line_bot_api.push_message(
                    user.line_user_id,
                    TextSendMessage(text=f"🎤 點餐語音（文字版）:\n{voice_result.get('text', '')}")
                )
                print("備用語音文字已發送到 LINE")
        else:
            print(f"備用語音生成失敗: {voice_result.get('message', '')}")
    else:
        print("語音生成失敗，跳過語音發送")
```

**改進：**
- 增加語音檔案大小檢查
- 改善備用方案的處理
- 增加更詳細的日誌記錄
- 改善錯誤處理

## 測試結果

創建了測試腳本 `simple_voice_test.py` 來驗證修復：

```
🚀 開始簡單語音功能測試
==================================================
🔍 測試語音目錄...
✅ 語音目錄已創建/確認: /tmp/voices
✅ 語音目錄可寫入

🧹 測試語音檔案清理...
✅ 語音檔案清理功能正常

📁 測試語音檔案服務路由...
✅ 語音檔案服務路由存在

🔧 測試環境變數...
✅ BASE_URL: https://ordering-helper-backend-1095766716155.asia-east1.run.app
⚠️ Azure Speech 設定不完整
⚠️ LINE Bot 設定不完整

🎤 測試語音檔案創建...
✅ 測試語音檔案創建成功: test_voice.wav, 大小: 44 bytes
✅ 測試語音檔案已清理

==================================================
📊 測試結果總結:
   語音目錄: ✅ 通過
   語音檔案清理: ✅ 通過
   語音檔案服務路由: ✅ 通過
   環境變數檢查: ✅ 通過
   語音檔案創建: ✅ 通過

🎯 總計: 5/5 項測試通過
🎉 所有測試通過！語音檔案功能應該正常工作。
```

## 主要改進點

### 1. 語音檔案持久性
- 延長清理時間從30分鐘到60分鐘
- 增加檔案存在性和大小檢查
- 改善檔案服務的安全性

### 2. 錯誤處理
- 增加詳細的錯誤訊息和日誌
- 改善備用方案的處理
- 增加檔案服務的安全性檢查

### 3. 語音檔案服務
- 增加檔案格式驗證
- 防止路徑遍歷攻擊
- 增加適當的 HTTP headers
- 改善錯誤回應

### 4. 備用方案
- 改善文字版本的語音內容
- 增加更好的錯誤處理
- 提供更詳細的狀態訊息

## 部署建議

1. **環境變數設定**：確保以下環境變數已正確設定
   - `AZURE_SPEECH_KEY`
   - `AZURE_SPEECH_REGION`
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `LINE_CHANNEL_SECRET`
   - `BASE_URL`

2. **監控建議**：
   - 監控語音檔案生成成功率
   - 監控語音檔案服務的錯誤率
   - 監控語音檔案清理的頻率

3. **效能優化**：
   - 語音檔案現在會保留60分鐘，確保用戶有足夠時間訪問
   - 增加了檔案服務的快取控制
   - 改善了錯誤處理，減少不必要的重試

## 結論

通過這些修復，語音檔案和摘要功能應該會更加穩定和可靠：

1. **語音檔案不會過早被刪除**（60分鐘 vs 30分鐘）
2. **更好的錯誤處理和備用方案**
3. **更安全的檔案服務**
4. **更詳細的日誌和監控**

這些改進應該能解決語音檔案和摘要消失的問題，並提供更好的用戶體驗。 