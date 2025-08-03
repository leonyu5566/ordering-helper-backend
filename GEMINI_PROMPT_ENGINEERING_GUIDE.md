# Gemini API 提示詞工程說明書

## 📋 目錄
1. [概述](#概述)
2. [菜單 OCR 處理](#菜單-ocr-處理)
3. [餐飲推薦系統](#餐飲推薦系統)
4. [文字翻譯](#文字翻譯)
5. [最佳實踐](#最佳實踐)
6. [錯誤處理](#錯誤處理)

---

## 🎯 概述

本專案使用 Google Gemini API 實現以下功能：
- **菜單圖片 OCR 辨識與翻譯**
- **智能餐飲推薦**
- **多語言文字翻譯**

### 使用的 Gemini 模型
- `gemini-pro-vision`: 用於圖片分析（菜單 OCR）
- `gemini-pro`: 用於文字處理（翻譯、推薦）

---

## 🍽️ 菜單 OCR 處理

### 功能描述
將菜單圖片轉換為結構化的菜單資料，包含 OCR 辨識、翻譯和分類。

### 提示詞模板

```python
prompt = f"""
你是一個專業的菜單辨識專家。請仔細分析這張菜單圖片，並執行以下任務：

## 任務要求：
1. **OCR 辨識**：準確辨識所有菜單項目、價格和描述
2. **結構化處理**：將辨識結果整理成結構化資料
3. **語言翻譯**：將菜名翻譯為 {target_language} 語言
4. **價格標準化**：統一價格格式（數字）

## 輸出格式要求：
請嚴格按照以下 JSON 格式輸出，不要包含任何其他文字：

```json
{{
  "success": true,
  "menu_items": [
    {{
      "original_name": "原始菜名（中文）",
      "translated_name": "翻譯後菜名",
      "price": 數字價格,
      "description": "菜單描述（如果有）",
      "category": "分類（如：主食、飲料、小菜等）"
    }}
  ],
  "store_info": {{
    "name": "店家名稱",
    "address": "地址（如果有）",
    "phone": "電話（如果有）"
  }},
  "processing_notes": "處理備註"
}}
```

## 重要注意事項：
- 價格必須是數字格式
- 如果無法辨識某個項目，請在 processing_notes 中說明
- 確保 JSON 格式完全正確，可以直接解析
- 如果圖片模糊或無法辨識，請將 success 設為 false
- 翻譯時保持菜名的準確性和文化適應性
"""
```

### 關鍵設計原則
1. **明確的角色定義**：將 AI 定位為"專業的菜單辨識專家"
2. **結構化輸出**：要求嚴格的 JSON 格式
3. **錯誤處理**：包含 success 欄位和處理備註
4. **多語言支援**：動態設定目標語言

---

## 🤖 餐飲推薦系統

### 功能描述
根據使用者需求，從店家列表中推薦最適合的餐飲選擇。

### 提示詞模板

```python
prompt = f"""
你是一個專業的餐飲推薦專家。請根據使用者的餐飲需求，從以下店家列表中推薦最適合的店家。

## 使用者需求：
{food_request}

## 可用店家列表：
{json.dumps(store_data, ensure_ascii=False, indent=2)}

## 推薦規則：
1. **優先順序**：VIP店家 (partner_level=2) > 合作店家 (partner_level=1) > 非合作店家 (partner_level=0)
2. **需求匹配**：根據使用者需求選擇最適合的店家
3. **菜色特色**：考慮店家的熱門菜色和評論摘要
4. **推薦數量**：最多推薦5家店家

## 輸出格式要求：
請嚴格按照以下 JSON 格式輸出，不要包含任何其他文字：

```json
{{
  "recommendations": [
    {{
      "store_id": 店家ID,
      "store_name": "店家名稱",
      "partner_level": 合作等級,
      "reason": "推薦理由",
      "matched_keywords": ["匹配的關鍵字"],
      "estimated_rating": "預估評分 (1-5星)"
    }}
  ],
  "analysis": {{
    "user_preference": "分析出的使用者偏好",
    "recommendation_strategy": "推薦策略說明"
  }}
}}
```

## 重要注意事項：
- 確保推薦理由符合使用者需求
- 考慮店家的合作等級和特色
- 提供有價值的推薦理由
- 確保 JSON 格式完全正確
"""
```

### 關鍵設計原則
1. **多維度分析**：結合合作等級、需求匹配、菜色特色
2. **結構化推薦**：包含推薦理由和關鍵字匹配
3. **使用者偏好分析**：提供個性化推薦策略
4. **評分系統**：包含預估評分機制

---

## 🌐 文字翻譯

### 功能描述
將中文文字翻譯為目標語言，支援多語言本地化。

### 提示詞模板

```python
prompt = f"""
請將以下中文文字翻譯為 {target_language} 語言：

原文：{text}

請只回傳翻譯結果，不要包含任何其他文字。
"""
```

### 關鍵設計原則
1. **簡潔明確**：直接要求翻譯結果
2. **格式控制**：避免額外的解釋文字
3. **錯誤回退**：翻譯失敗時回傳原文

---

## 🎯 最佳實踐

### 1. 角色定義
```python
# 明確定義 AI 角色
"你是一個專業的菜單辨識專家"
"你是一個專業的餐飲推薦專家"
```

### 2. 結構化輸出
```python
# 要求嚴格的 JSON 格式
"請嚴格按照以下 JSON 格式輸出，不要包含任何其他文字"
```

### 3. 錯誤處理
```python
# 包含錯誤處理機制
"如果圖片模糊或無法辨識，請將 success 設為 false"
"如果無法辨識某個項目，請在 processing_notes 中說明"
```

### 4. 多語言支援
```python
# 動態語言設定
f"將菜名翻譯為 {target_language} 語言"
f"翻譯為 {target_language} 語言"
```

### 5. 資料驗證
```python
# 驗證回應格式
if 'success' not in result:
    result['success'] = True
if 'menu_items' not in result:
    result['menu_items'] = []
```

---

## ⚠️ 錯誤處理

### 1. JSON 解析錯誤
```python
try:
    result = json.loads(response.text)
except json.JSONDecodeError as e:
    return {
        "success": False,
        "menu_items": [],
        "processing_notes": f"JSON 解析失敗：{str(e)}"
    }
```

### 2. API 調用失敗
```python
try:
    response = model.generate_content([prompt, image_data])
except Exception as e:
    print(f"Gemini API 處理失敗：{e}")
    return {
        "success": False,
        "menu_items": [],
        "store_info": {},
        "processing_notes": f"API 調用失敗：{str(e)}"
    }
```

### 3. 翻譯回退機制
```python
try:
    return translate_text(text, target_language)
except Exception as e:
    print(f"翻譯失敗：{e}")
    return text  # 回傳原文
```

---

## 📊 提示詞優化建議

### 1. 增加上下文
- 提供更多背景資訊
- 包含相關的業務規則

### 2. 改進輸出格式
- 使用更詳細的 JSON Schema
- 增加驗證規則

### 3. 錯誤處理增強
- 提供更詳細的錯誤訊息
- 實現重試機制

### 4. 多語言優化
- 根據目標語言調整提示詞
- 考慮文化差異

---

## 🔧 技術實現

### 環境變數設定
```bash
GEMINI_API_KEY="your_gemini_api_key"
```

### 模型初始化
```python
import google.generativeai as genai
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro-vision')  # 圖片處理
model = genai.GenerativeModel('gemini-pro')         # 文字處理
```

### API 調用
```python
# 圖片處理
response = model.generate_content([prompt, image_data])

# 文字處理
response = model.generate_content(prompt)
```

---

## 📝 總結

本專案的 Gemini API 提示詞工程遵循以下原則：

1. **明確的角色定義**：讓 AI 理解其專業領域
2. **結構化輸出**：確保回應格式的一致性
3. **錯誤處理**：提供完善的錯誤回退機制
4. **多語言支援**：實現國際化功能
5. **業務邏輯整合**：將 AI 能力與業務需求結合

這些提示詞經過精心設計，確保能夠穩定、準確地處理各種餐飲相關的 AI 任務。 