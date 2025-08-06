# 點餐小幫手後端系統

## 專案概述

這是一個專為 LINE Bot 點餐系統設計的後端 API，主要負責處理合作店家的菜單資料查詢和非合作店家的菜單圖片翻譯功能。

**注意：** LIFF 前端獨立部署在 Azure 靜態網頁，後端只提供 API 服務。

## 核心架構

### 後端職責（專注於核心功能）

後端系統專注於以下核心功能，避免重複 LINE Bot 已有的功能：

#### 1. **合作店家流程**
- 接收店家ID → 從資料庫拉取店家資訊和菜單
- 提供多語言翻譯支援
- 處理訂單建立和確認

#### 2. **非合作店家流程**
- 接收菜單圖片 → 使用 Gemini API 進行 OCR 和翻譯
- 生成動態菜單供使用者點餐
- 處理臨時訂單建立

### 分工明確

| 功能 | LINE Bot 負責 | 後端負責 |
|------|---------------|----------|
| GPS 定位 | ✅ 處理位置分享 | ❌ 不需要 |
| 店家選擇 | ✅ 顯示店家清單 | ❌ 不需要 |
| 店家資訊查詢 | ❌ 不需要 | ✅ 從資料庫拉取 |
| 菜單翻譯 | ❌ 不需要 | ✅ OCR + AI 翻譯 |
| 訂單處理 | ❌ 不需要 | ✅ 建立和確認訂單 |

## 完整流程

### 3. 選擇店家 → 進入 LIFF 點餐介面

#### 3.1 合作店家流程
1. **LINE Bot 處理**：使用者在 LINE Bot 點選店家
2. **自動建立記錄**：如果店家不存在，自動建立非合作店家記錄
3. **跳轉 LIFF**：跳轉至合作店家專屬 LIFF 頁面（Azure 靜態網頁）
4. **載入菜單**：從資料庫撈取已結構化和翻譯的菜單
5. **多語言顯示**：根據使用者語言偏好顯示菜單
6. **直接點餐**：使用者可直接選擇數量並確認訂單

#### 3.2 非合作店家流程
1. **LINE Bot 處理**：使用者在 LINE Bot 點選店家
2. **自動建立記錄**：自動建立非合作店家記錄
3. **跳轉 LIFF**：跳轉至非合作店家專屬 LIFF 頁面（Azure 靜態網頁）
4. **拍照上傳**：LIFF 提示使用者拍攝紙本菜單
5. **AI 處理**：後端呼叫 Gemini API 進行 OCR 辨識
6. **動態生成**：將菜單項目與價格轉成結構化資料
7. **翻譯顯示**：翻譯為使用者語言並動態生成可點選菜單介面
8. **臨時訂單**：建立基於 OCR 結果的臨時訂單

### 4. 點餐與確認

#### 4.1 購物車功能
- 使用者在 LIFF 介面選擇品項與數量
- 即時計算小計和總金額
- 支援數量調整和移除商品

#### 4.2 訂單確認
- 點擊「確認訂單」後顯示完整訂單明細
- 包含商品名稱、數量、單價、小計
- 顯示總金額和訂單時間
- 支援多語言訂單摘要

### 5. 生成中文語音檔

#### 5.1 語音生成流程
- 後端接收訂單後，將品項轉回原始中文菜名
- 呼叫 Azure TTS API 合成中文語音
- 支援 .wav 格式輸出
- 提供可調語速版本（0.5x - 2.0x）

#### 5.2 語音功能特色
- **多種語音**：支援不同中文語音（如 zh-TW-HsiaoChenNeural）
- **語速調整**：可調整語速範圍 0.5x - 2.0x
- **自動生成**：訂單建立時自動生成語音檔
- **即時下載**：提供語音檔下載 API

### 6. 回傳至 LINE Bot

#### 6.1 Bot 傳送內容
- **兩則訂單文字摘要**：
  - 使用者語言摘要（英文/日文/韓文）
  - 中文摘要（供現場點餐使用）
- **中文語音檔**：標準語速的點餐語音
- **語速控制按鈕**：
  - 慢速播放 (0.7x)
  - 正常播放 (1.0x)
  - 快速播放 (1.3x)
  - 重新播放

#### 6.2 語音控制功能
- **即時語速調整**：點擊按鈕即可生成不同語速的語音檔
- **多語言介面**：按鈕文字根據使用者語言顯示
- **錯誤處理**：語音生成失敗時提供友善的錯誤訊息

### 7. 現場點餐

#### 7.1 點餐流程
- 使用者於店家櫃檯播放中文語音
- 語音內容包含完整的點餐資訊
- 支援不同語速播放，適應不同環境需求
- 可重複播放，確保點餐準確性

#### 7.2 語音內容格式
```
您好，我要點餐。
牛肉麵 2份，
紅茶 1份，
總共350元，謝謝。
```

### 改進重點

#### ✅ **已改進的功能**

1. **完整的 LINE Bot 通知系統**
   ```python
   # 發送兩則文字摘要
   line_bot_api.push_message(user_id, TextSendMessage(text=chinese_summary))
   line_bot_api.push_message(user_id, TextSendMessage(text=translated_summary))
   
   # 發送語音檔
   line_bot_api.push_message(user_id, AudioSendMessage(...))
   
   # 發送語速控制按鈕
   send_voice_control_buttons(user_id, order_id, user_language)
   ```

2. **語速控制功能**
   - 支援 0.7x、1.0x、1.3x 三種語速
   - 即時生成和下載語音檔
   - 多語言按鈕介面

3. **臨時訂單通知**
   - 非合作店家也能收到完整的通知
   - 包含語音檔和語速控制
   - 支援原始中文菜名語音生成

4. **現場點餐支援**
   - 標準化的中文語音格式
   - 清晰的點餐內容結構
   - 適合現場播放的語音品質

5. **錯誤處理和用戶體驗**
   - 完整的錯誤訊息
   - 多語言支援
   - 友善的使用者介面

## API 端點

### 核心 API

#### 店家相關
- `GET /api/stores/{store_id}` - 取得店家資訊（支援多語言）
- `GET /api/stores/check-partner-status` - 檢查店家合作狀態

#### 菜單相關
- `GET /api/menu/{store_id}` - 取得合作店家菜單（支援多語言）
- `POST /api/menu/process-ocr` - 處理非合作店家菜單圖片

#### 訂單相關
- `POST /api/orders` - 建立訂單（合作店家）
- `POST /api/orders/temp` - 建立臨時訂單（非合作店家）
- `GET /api/orders/{order_id}/confirm` - 取得訂單確認資訊
- `GET /api/orders/{order_id}/voice` - 取得訂單語音檔

#### 語音相關
- `POST /api/voice/generate` - 生成自定義語音檔

#### 使用者相關
- `POST /api/users/register` - 使用者註冊

### LINE Bot 功能

#### 語音控制指令
- `voice_slow_{order_id}` - 慢速播放 (0.7x)
- `voice_normal_{order_id}` - 正常播放 (1.0x)
- `voice_fast_{order_id}` - 快速播放 (1.3x)
- `voice_replay_{order_id}` - 重新播放

#### 臨時訂單語音控制
- `temp_voice_slow_{processing_id}` - 臨時訂單慢速播放
- `temp_voice_normal_{processing_id}` - 臨時訂單正常播放
- `temp_voice_fast_{processing_id}` - 臨時訂單快速播放
- `temp_voice_replay_{processing_id}` - 臨時訂單重新播放

### 測試頁面
- `GET /test` - 後端 API 測試頁面

## 資料庫模型

### 核心模型
- `User` - 使用者資訊和語言偏好
- `Store` - 店家資訊（合作/非合作）
- `Menu/MenuItem` - 菜單項目
- `MenuTranslation` - 菜單翻譯
- `Order/OrderItem` - 訂單資料
- `GeminiProcessing` - AI 處理記錄

## 技術特色

### 1. 多語言支援
- 優先使用資料庫翻譯
- AI 翻譯作為備用方案
- 支援中文、英文、日文、韓文

### 2. 智慧菜單處理
- 使用 Gemini API 進行 OCR
- 自動結構化菜單資料
- 即時翻譯成使用者語言

### 3. 訂單確認系統
- 生成語音訂單確認
- 多語言訂單摘要
- 完整的訂單記錄

### 4. 完整的 API 支援
- RESTful API 設計
- 完整的錯誤處理
- 詳細的 API 文件

## 部署

### 環境需求
- Python 3.8+
- Flask
- SQLAlchemy
- LINE Bot SDK
- Google Gemini API

### 快速開始
```bash
# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
export LINE_CHANNEL_ACCESS_TOKEN="your_token"
export LINE_CHANNEL_SECRET="your_secret"
export GEMINI_API_KEY="your_gemini_key"

# 初始化資料庫
python tools/rebuild_database.py

# 啟動服務
python run.py
```

## 🔧 環境變數設定

### 必要環境變數
```bash
# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Azure Speech Service
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_azure_region

# LINE Bot
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# 資料庫
DATABASE_URL=your_database_url
```

### LINE Bot 設定說明
1. 在 LINE Developers Console 建立 Bot
2. 取得 Channel Access Token 和 Channel Secret
3. 設定 Webhook URL：`https://your-domain.com/api/line/webhook`
4. 啟用 Webhook 功能

## 開發原則

### 1. 職責分離
- LINE Bot 負責使用者互動和位置服務
- 後端專注於資料處理和 AI 功能
- LIFF 前端獨立部署在 Azure 靜態網頁

### 2. 簡化架構
- 移除不必要的 GPS 定位功能
- 專注於核心的菜單翻譯和訂單處理

### 3. 效能優化
- 優先使用資料庫翻譯減少 API 呼叫
- 快取常用的翻譯結果

### 4. 使用者體驗
- 完整的錯誤處理和重試機制
- 多語言支援
- 直觀的介面設計

## 貢獻

歡迎提交 Issue 和 Pull Request 來改善這個專案！

## 授權

MIT License
