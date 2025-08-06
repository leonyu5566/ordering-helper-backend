# Gemini API 訂單摘要和語音生成指南

## 🎯 功能概述

本系統使用 Gemini API 來生成訂單摘要和語音檔，確保使用實際的品項名稱而不是"品項1、品項2"這樣的佔位符。

## 🔄 工作流程

### 1. 訂單處理流程

```
使用者點餐 → 實際品項名稱收集 → Gemini API 處理 → 生成語音檔 → 發送給使用者
```

### 2. 實際品項名稱處理

系統會優先使用以下順序的品項名稱：

1. **`name`** - 主要品項名稱
2. **`translated_name`** - 翻譯後的品項名稱
3. **`original_name`** - 原始品項名稱
4. **`item_name`** - 菜單項目名稱
5. **預設值** - "項目 X"（僅作為最後備用）

### 3. Gemini API 整合

#### 輸入格式
```python
items = [
    {
        'name': '經典夏威夷奶醬義大利麵',
        'quantity': 1,
        'price': 115,
        'subtotal': 115
    },
    {
        'name': '美國脆薯',
        'quantity': 2,
        'price': 55,
        'subtotal': 110
    }
]
```

#### 輸出格式
```python
{
    "chinese_voice": "老闆，我要經典夏威夷奶醬義大利麵一份、美國脆薯兩份，謝謝。",
    "chinese_summary": "經典夏威夷奶醬義大利麵 x 1、美國脆薯 x 2",
    "user_summary": "Order: Classic Hawaiian Cream Pasta x 1, American Fries x 2"
}
```

## 🚀 API 使用方式

### 1. 簡化訂單 API

**端點：** `POST /api/orders/simple`

**請求格式：**
```json
{
    "user_language": "zh",
    "line_user_id": "U1234567890abcdef",
    "items": [
        {
            "name": "經典夏威夷奶醬義大利麵",
            "quantity": 1,
            "price": 115
        },
        {
            "name": "美國脆薯",
            "quantity": 2,
            "price": 55
        }
    ]
}
```

**回應格式：**
```json
{
    "success": true,
    "order_id": "simple_20241201_143022",
    "total_amount": 225,
    "voice_url": "/static/voice/order_simple_20241201_143022_rate_1.0.wav",
    "chinese_summary": "經典夏威夷奶醬義大利麵 x 1、美國脆薯 x 2",
    "user_summary": "Order: Classic Hawaiian Cream Pasta x 1, American Fries x 2",
    "order_details": [
        {
            "name": "經典夏威夷奶醬義大利麵",
            "quantity": 1,
            "price": 115,
            "subtotal": 115
        },
        {
            "name": "美國脆薯",
            "quantity": 2,
            "price": 55,
            "subtotal": 110
        }
    ],
    "line_bot_sent": true
}
```

### 2. 臨時訂單 API

**端點：** `POST /api/orders/temp`

**請求格式：**
```json
{
    "line_user_id": "U1234567890abcdef",
    "language": "zh",
    "items": [
        {
            "item_name": "經典夏威夷奶醬義大利麵",
            "quantity": 1,
            "price": 115
        }
    ]
}
```

## 🎤 語音生成功能

### 1. Azure Speech 整合

系統使用 Azure Speech Service 生成中文語音檔：

- **語音模型：** `zh-TW-HsiaoChenNeural`
- **語速支援：** 0.5x - 2.0x
- **輸出格式：** WAV
- **檔案位置：** `/static/voice/`

### 2. 語音控制功能

支援多種語速的語音播放：

- **慢速播放：** 0.7x
- **正常播放：** 1.0x
- **快速播放：** 1.3x
- **重新播放：** 1.0x

### 3. LINE Bot 整合

自動發送語音檔和文字摘要到 LINE Bot：

```python
# 發送語音檔
line_bot_api.push_message(
    user_id,
    AudioSendMessage(
        original_content_url=f"file://{voice_path}",
        duration=30000
    )
)

# 發送文字摘要
line_bot_api.push_message(
    user_id,
    TextSendMessage(text=chinese_summary)
)
```

## 🔧 技術實現

### 1. Gemini API 提示詞工程

```python
prompt = f"""
你是一個專業的點餐助手。請根據以下實際的點餐項目生成自然的中文語音和訂單摘要。

## 點餐項目詳情：
{json.dumps(item_details, ensure_ascii=False, indent=2)}

## 總金額：{total_amount}元

請生成：

1. **中文語音內容**（給店家聽的，要自然流暢）：
   - 格式：老闆，我要[實際品項名稱]一份、[實際品項名稱]一杯，謝謝。
   - 要求：使用實際的品項名稱，語言要自然，像是客人親自點餐
   - 避免使用"品項1、品項2"這樣的佔位符

2. **中文訂單摘要**（給使用者看的）：
   - 格式：[實際品項名稱] x [數量]、[實際品項名稱] x [數量]
   - 要求：清晰列出所有實際品項和數量
   - 避免使用"品項1、品項2"這樣的佔位符

3. **使用者語言摘要**（{user_language}）：
   - 格式：Order: [實際品項名稱] x [qty], [實際品項名稱] x [qty]
   - 要求：使用使用者選擇的語言，翻譯實際品項名稱
   - 避免使用"Item 1、Item 2"這樣的佔位符

## 重要注意事項：
- 必須使用實際的品項名稱，不要使用"品項1、品項2"等佔位符
- 語音內容要自然流暢，適合現場點餐
- 摘要要清晰易讀，便於使用者確認
"""
```

### 2. 佔位符檢測和修正

```python
# 檢查是否包含佔位符
if '品項1' in result['chinese_voice'] or '項目1' in result['chinese_voice']:
    # 如果 Gemini 回傳了佔位符，使用實際品項名稱
    result['chinese_voice'] = f"老闆，我要{items_text}，謝謝。"
```

### 3. 多語言支援

支援以下語言：

- **中文 (zh)：** 預設語言
- **英文 (en)：** 英文翻譯
- **日文 (ja)：** 日文翻譯
- **韓文 (ko)：** 韓文翻譯

## 🧪 測試功能

### 1. 運行測試

```bash
python test_gemini_order_summary.py
```

### 2. 測試內容

- ✅ 實際品項名稱傳遞
- ✅ 佔位符檢測
- ✅ 多語言支援
- ✅ 語音檔生成
- ✅ LINE Bot 整合

### 3. 測試結果

```
🧪 測試 Gemini API 訂單摘要生成功能
==================================================
📋 測試品項：
  1. 經典夏威夷奶醬義大利麵 x1 ($115)
  2. 美國脆薯 x2 ($55)
  3. 可樂 x1 ($30)

💰 總金額：$255
==================================================
🇹🇼 測試中文摘要生成...
✅ 中文摘要生成結果：
語音內容：老闆，我要經典夏威夷奶醬義大利麵一份、美國脆薯兩份、可樂一杯，謝謝。
中文摘要：經典夏威夷奶醬義大利麵 x 1、美國脆薯 x 2、可樂 x 1
使用者摘要：Order: Classic Hawaiian Cream Pasta x 1, American Fries x 2, Cola x 1
✅ 通過：沒有檢測到佔位符，使用實際品項名稱
✅ 通過：檢測到實際品項名稱
```

## 🔍 錯誤處理

### 1. Gemini API 不可用

如果 Gemini API 不可用，系統會使用預設格式：

```python
chinese_voice = f"老闆，我要{items_text}，謝謝。"
chinese_summary = items_text.replace('、', '、').replace('x', ' x ')
user_summary = f"Order: {items_text}"
```

### 2. 語音生成失敗

如果 Azure Speech 不可用，系統會：

1. 發送文字版本的語音內容
2. 提供友善的錯誤訊息
3. 繼續提供其他功能

### 3. JSON 解析失敗

如果 Gemini API 回傳的 JSON 格式不正確，系統會：

1. 使用預設格式
2. 記錄錯誤日誌
3. 確保功能正常運作

## 📋 環境變數設定

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
```

## 🎯 最佳實踐

### 1. 品項名稱處理

- ✅ 使用實際的品項名稱
- ✅ 避免使用佔位符
- ✅ 提供多語言支援
- ✅ 確保語音內容自然

### 2. 錯誤處理

- ✅ 提供備用方案
- ✅ 友善的錯誤訊息
- ✅ 完整的日誌記錄
- ✅ 功能降級處理

### 3. 使用者體驗

- ✅ 清晰的訂單摘要
- ✅ 自然的語音內容
- ✅ 多語言支援
- ✅ 語速控制功能

## 🚀 部署檢查清單

- [ ] 設定 Gemini API Key
- [ ] 設定 Azure Speech Key
- [ ] 設定 LINE Bot Token
- [ ] 測試品項名稱處理
- [ ] 測試語音生成功能
- [ ] 測試多語言支援
- [ ] 測試錯誤處理
- [ ] 測試 LINE Bot 整合

## 📞 支援

如果您遇到任何問題，請檢查：

1. **環境變數設定**
2. **API 金鑰有效性**
3. **網路連線狀態**
4. **錯誤日誌記錄**

系統會自動處理大部分錯誤情況，並提供友善的錯誤訊息。 