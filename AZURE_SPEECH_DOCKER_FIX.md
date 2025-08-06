# Azure Speech SDK Docker 環境修復

## 🔍 問題診斷

根據Cloud Run日誌分析，主要問題是：

### ❌ 問題1：OpenSSL版本不匹配
- **錯誤訊息**：`Failed to initialize platform (azure-c-shared). Error: 2176`
- **原因**：Azure Speech SDK需要OpenSSL 1.1，但Ubuntu 22.04使用OpenSSL 3
- **影響**：導致TTS功能完全無法使用

### ❌ 問題2：缺少系統庫依賴
- **缺少庫**：`libssl1.1`、`libasound2`、`libpthread-stubs0-dev`
- **影響**：Azure Speech SDK無法正確初始化

### ❌ 問題3：Worker超時
- **錯誤**：`WORKER TIMEOUT (pid:2)` 和 `SIGKILL`
- **原因**：初始化失敗導致請求掛起
- **影響**：整個請求被中斷

## ✅ 修復方案

### 1. 更換基礎映像為Ubuntu 20.04

```dockerfile
# 修復前
FROM python:3.11-slim

# 修復後
FROM ubuntu:20.04
```

**原因**：Ubuntu 20.04預設使用OpenSSL 1.1.1，與Azure Speech SDK相容

### 2. 安裝必要的系統庫

```dockerfile
RUN apt-get update && \
    apt-get install -y \
        python3.11 \
        python3.11-pip \
        python3.11-dev \
        libssl1.1 \
        libasound2 \
        libpthread-stubs0-dev \
        ca-certificates \
        curl \
        gunicorn \
    && rm -rf /var/lib/apt/lists/*
```

**包含的庫**：
- `libssl1.1`：OpenSSL 1.1版本
- `libasound2`：音訊輸出支援
- `libpthread-stubs0-dev`：POSIX線程支援
- `ca-certificates`：SSL證書
- `curl`：HTTP請求支援

### 3. 設定Python 3.11為預設版本

```dockerfile
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3.11 1
```

### 4. 建立語音檔案目錄

```dockerfile
RUN mkdir -p /tmp/voices && chmod 755 /tmp/voices
```

### 5. 設定環境變數

```dockerfile
ENV PYTHONPATH=/app
```

## 🧪 測試腳本

### 1. Azure Speech SDK測試
- **檔案**：`test_azure_speech_docker.py`
- **功能**：測試SDK初始化、OpenSSL版本、系統庫依賴

### 2. 部署腳本
- **檔案**：`deploy_with_voice_fix.py`
- **功能**：自動部署到Cloud Run並設定環境變數

## 🚀 部署步驟

### 1. 本地測試
```bash
# 載入環境變數
source <(cat notebook.env | sed 's/^/export /')

# 測試Azure Speech SDK
python3 test_azure_speech_docker.py
```

### 2. 構建Docker映像
```bash
# 構建映像
docker build -t ordering-helper-backend .

# 測試容器
docker run --rm -it ordering-helper-backend python3 test_azure_speech_docker.py
```

### 3. 部署到Cloud Run
```bash
# 使用部署腳本
python3 deploy_with_voice_fix.py

# 或手動部署
gcloud run deploy ordering-helper-backend \
    --source . \
    --region asia-east1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300
```

## 📋 環境變數檢查

確保Cloud Run環境中設定了以下變數：

```bash
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=australiaeast
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_CHANNEL_SECRET=your_line_secret
GEMINI_API_KEY=your_gemini_key
BASE_URL=https://ordering-helper-backend-ordering-helper-backend-1095766716155.asia-east1.run.app
```

## 🔍 部署後驗證

### 1. 檢查應用程式日誌
```bash
gcloud logs read --service=ordering-helper-backend --limit=50
```

### 2. 測試語音生成
```bash
curl -X POST https://your-service-url/api/voice/generate \
  -H "Content-Type: application/json" \
  -d '{"text":"測試語音","rate":1.0}'
```

### 3. 檢查靜態路由
```bash
curl -I https://your-service-url/api/voices/test.wav
```

## 🎯 預期結果

修復後應該看到：

1. **Azure Speech SDK初始化成功**
   ```
   ✅ Azure Speech SDK 導入成功
   ✅ SpeechConfig 初始化成功
   ✅ SpeechSynthesizer 初始化成功
   ```

2. **語音檔生成成功**
   ```
   [TTS] Will save to /tmp/voices/xxx.wav
   [TTS] Success, file exists? True
   ```

3. **靜態路由正常**
   ```
   HTTP/1.1 200 OK
   Content-Type: audio/wav
   ```

4. **LINE Bot語音回傳成功**
   ```
   [Webhook] Reply with voice URL: https://...
   ✅ 成功發送語速語音
   ```

## 📞 故障排除

### 如果仍有問題：

1. **檢查OpenSSL版本**
   ```bash
   docker run --rm ordering-helper-backend openssl version
   ```

2. **檢查系統庫**
   ```bash
   docker run --rm ordering-helper-backend ldd /usr/lib/x86_64-linux-gnu/libssl.so.1.1
   ```

3. **檢查Azure Speech SDK版本**
   ```bash
   docker run --rm ordering-helper-backend pip3 show azure-cognitiveservices-speech
   ```

4. **查看詳細錯誤日誌**
   ```bash
   gcloud logs read --service=ordering-helper-backend --filter="severity>=ERROR" --limit=20
   ``` 