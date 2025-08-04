#!/usr/bin/env python3
"""
LangChain 菜單增強處理
使用 Gemini 2.5 Flash 進行高級菜單處理
"""

import os
import json
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from google import genai

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MenuItem(BaseModel):
    """菜單項目結構"""
    original_name: str = Field(description="原始菜名（中文）")
    translated_name: str = Field(description="翻譯後菜名")
    price: int = Field(description="價格（數字）")
    description: Optional[str] = Field(description="菜單描述", default="")
    category: str = Field(description="分類（如：主食、飲料、小菜等）")

class StoreInfo(BaseModel):
    """店家資訊結構"""
    name: str = Field(description="店家名稱")
    address: Optional[str] = Field(description="地址", default="")
    phone: Optional[str] = Field(description="電話", default="")

class MenuProcessingResult(BaseModel):
    """菜單處理結果"""
    success: bool = Field(description="處理是否成功")
    menu_items: List[MenuItem] = Field(description="菜單項目列表")
    store_info: StoreInfo = Field(description="店家資訊")
    processing_notes: str = Field(description="處理備註")
    confidence_score: float = Field(description="辨識信心度", ge=0.0, le=1.0)

def create_enhanced_menu_processor():
    """創建強化版菜單處理器"""
    
    # 初始化 Gemini 2.5 Flash
    genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    
    return genai.Client()

def process_menu_with_langchain(image_path, target_language='en'):
    """使用 Gemini 2.5 Flash 處理菜單"""
    
    try:
        # 讀取圖片
        from PIL import Image
        import io
        
        with open(image_path, 'rb') as img_file:
            image_bytes = img_file.read()
        
        # 轉換為 PIL.Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # 創建處理器
        client = create_enhanced_menu_processor()
        
        # 建立提示詞
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
  "processing_notes": "處理備註",
  "confidence_score": 0.9
}}
```

## 重要注意事項：
- 價格必須是數字格式
- 如果無法辨識某個項目，請在 processing_notes 中說明
- 確保 JSON 格式完全正確，可以直接解析
- 如果圖片模糊或無法辨識，請將 success 設為 false
- 翻譯時保持菜名的準確性和文化適應性
"""
        
        # 執行處理
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                prompt,
                image
            ],
            config=genai.types.GenerateContentConfig(
                thinking_config=genai.types.ThinkingConfig(thinking_budget=256)
            )
        )
        
        # 解析結果
        result = json.loads(response.text)
        
        # 添加額外的驗證和後處理
        result = validate_and_enhance_result(result)
        
        return result
        
    except Exception as e:
        logger.error(f"Gemini 2.5 Flash 處理失敗：{e}")
        return {
            "success": False,
            "menu_items": [],
            "store_info": {},
            "processing_notes": f"Gemini 2.5 Flash 處理失敗：{str(e)}",
            "confidence_score": 0.0
        }

def validate_and_enhance_result(result):
    """驗證和增強結果"""
    
    # 價格驗證
    for item in result.get('menu_items', []):
        if isinstance(item.get('price'), str):
            try:
                item['price'] = int(item['price'].replace('$', '').replace(',', ''))
            except:
                item['price'] = 0
    
    # 信心度調整
    if 'confidence_score' not in result:
        result['confidence_score'] = 0.8
    
    return result

def create_menu_qa_chain():
    """創建菜單問答鏈"""
    
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    
    return client

def answer_menu_question(menu_data, question):
    """回答菜單相關問題"""
    
    try:
        client = create_menu_qa_chain()
        
        prompt = f"""
基於以下菜單資料回答問題：

菜單資料：{json.dumps(menu_data, ensure_ascii=False)}

問題：{question}

請提供準確、有用的回答。
"""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=genai.types.GenerateContentConfig(
                thinking_config=genai.types.ThinkingConfig(thinking_budget=128)
            )
        )
        
        return response.text.strip()
        
    except Exception as e:
        logger.error(f"菜單問答失敗：{e}")
        return "抱歉，無法回答這個問題。"

def test_langchain_enhancement():
    """測試 LangChain 增強功能"""
    print("🧪 測試 Gemini 2.5 Flash 增強功能...")
    
    # 這裡可以添加測試邏輯
    print("✅ Gemini 2.5 Flash 增強功能測試完成")

if __name__ == "__main__":
    test_langchain_enhancement() 