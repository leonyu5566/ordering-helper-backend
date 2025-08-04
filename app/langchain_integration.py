# =============================================================================
# 檔案名稱：app/langchain_integration.py
# 功能描述：LangChain 整合模組，將所有 Gemini API 使用整合到 LangChain 架構
# 主要功能：
# - 整合菜單 OCR 處理
# - 整合文字翻譯功能
# - 整合餐飲推薦功能
# - 提供統一的 LangChain 介面
# =============================================================================

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# 導入 LangChain 強化模組
try:
    from app.langchain_enhancement import get_enhanced_processor, LangChainConfig
    from app.ai_enhancement import get_ai_enhancement_manager
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️ LangChain 強化模組未載入")

# 導入新版 Gemini API 功能（作為回退）
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini API 未載入")

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LangChainIntegration:
    """LangChain 整合器"""
    
    def __init__(self):
        self.enhanced_processor = None
        self.ai_manager = None
        self.use_langchain = True
        
        # 初始化 LangChain 組件
        if LANGCHAIN_AVAILABLE:
            try:
                self.enhanced_processor = get_enhanced_processor()
                self.ai_manager = get_ai_enhancement_manager()
                logger.info("✅ LangChain 整合器初始化成功")
            except Exception as e:
                logger.error(f"❌ LangChain 整合器初始化失敗：{e}")
                self.use_langchain = False
        else:
            self.use_langchain = False
            logger.warning("⚠️ LangChain 不可用，使用基礎模式")
    
    def process_menu_ocr_langchain(self, image_path: str, target_language: str = 'en') -> Dict:
        """使用 LangChain 處理菜單 OCR"""
        try:
            if self.use_langchain and self.ai_manager:
                # 使用 LangChain 強化處理
                logger.info("🔧 使用 LangChain 處理菜單 OCR")
                return self.ai_manager.process_menu_ocr(image_path, target_language)
            else:
                # 回退到原始 Gemini API
                logger.info("🔄 使用原始 Gemini API 處理菜單 OCR")
                return self._fallback_menu_ocr(image_path, target_language)
                
        except Exception as e:
            logger.error(f"❌ 菜單 OCR 處理失敗：{e}")
            return self._fallback_menu_ocr(image_path, target_language)
    
    def translate_text_langchain(self, text: str, target_language: str = 'en', context: str = None) -> Dict:
        """使用 LangChain 翻譯文字"""
        try:
            if self.use_langchain and self.ai_manager:
                # 使用 LangChain 強化處理
                logger.info("🔧 使用 LangChain 翻譯文字")
                return self.ai_manager.process_translation(text, target_language, context)
            else:
                # 回退到原始 Gemini API
                logger.info("🔄 使用原始 Gemini API 翻譯文字")
                return self._fallback_translate_text(text, target_language)
                
        except Exception as e:
            logger.error(f"❌ 文字翻譯失敗：{e}")
            return self._fallback_translate_text(text, target_language)
    
    def get_recommendations_langchain(self, food_request: str, user_language: str = 'zh', 
                                    user_history: List = None) -> Dict:
        """使用 LangChain 獲取餐飲推薦"""
        try:
            if self.use_langchain and self.ai_manager:
                # 使用 LangChain 強化處理
                logger.info("🔧 使用 LangChain 獲取餐飲推薦")
                return self.ai_manager.process_recommendation(food_request, user_language, user_history)
            else:
                # 回退到原始 Gemini API
                logger.info("🔄 使用原始 Gemini API 獲取餐飲推薦")
                return self._fallback_get_recommendations(food_request, user_language)
                
        except Exception as e:
            logger.error(f"❌ 餐飲推薦失敗：{e}")
            return self._fallback_get_recommendations(food_request, user_language)
    
    def _fallback_menu_ocr(self, image_path: str, target_language: str = 'en') -> Dict:
        """回退到原始 Gemini API 菜單 OCR"""
        if not GEMINI_AVAILABLE:
            return {
                "success": False,
                "menu_items": [],
                "store_info": {},
                "processing_notes": "Gemini API 不可用"
            }
        
        try:
            # 設定 Gemini API
            from google import genai
            genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
            
            # 讀取圖片並轉換為 PIL.Image 格式
            from PIL import Image
            import io
            
            with open(image_path, 'rb') as img_file:
                image_bytes = img_file.read()
            
            # 將 bytes 轉換為 PIL.Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # 檢查圖片格式並確定 MIME 類型
            import mimetypes
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type or not mime_type.startswith('image/'):
                mime_type = 'image/jpeg'  # 預設為 JPEG
            
            logger.info(f"圖片 MIME 類型: {mime_type}")
            logger.info(f"圖片大小: {len(image_bytes)} bytes")
            logger.info(f"圖片尺寸: {image.size}")
            
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
            
            # 調用 Gemini 2.5 Flash API
            response = genai.Client().models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    prompt,
                    image
                ],
                config=genai.types.GenerateContentConfig(
                    thinking_config=genai.types.ThinkingConfig(thinking_budget=256)
                )
            )
            
            # 解析回應
            result = json.loads(response.text)
            
            # 驗證回應格式
            if not isinstance(result, dict):
                raise ValueError("回應不是有效的 JSON 物件")
            
            if 'success' not in result:
                result['success'] = True
            
            if 'menu_items' not in result:
                result['menu_items'] = []
            
            if 'store_info' not in result:
                result['store_info'] = {}
            
            # 驗證菜單項目格式
            for item in result['menu_items']:
                if 'original_name' not in item:
                    item['original_name'] = ''
                if 'translated_name' not in item:
                    item['translated_name'] = item.get('original_name', '')
                if 'price' not in item:
                    item['price'] = 0
                if 'description' not in item:
                    item['description'] = ''
                if 'category' not in item:
                    item['category'] = '其他'
            
            return result
            
        except Exception as e:
            logger.error(f"回退菜單 OCR 處理失敗：{e}")
            return {
                "success": False,
                "menu_items": [],
                "store_info": {},
                "processing_notes": f"處理失敗：{str(e)}"
            }
    
    def _fallback_translate_text(self, text: str, target_language: str = 'en') -> Dict:
        """回退到原始 Gemini API 翻譯"""
        if not GEMINI_AVAILABLE:
            return {
                "translated_text": text,
                "confidence_score": 0.0,
                "translation_notes": "Gemini API 不可用"
            }
        
        try:
            # 設定 Gemini API
            from google import genai
            genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
            
            # 建立翻譯提示詞
            prompt = f"""
            請將以下中文文字翻譯為 {target_language} 語言：
            
            原文：{text}
            
            請只回傳翻譯結果，不要包含任何其他文字。
            """
            
            response = genai.Client().models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
                config=genai.types.GenerateContentConfig(
                    thinking_config=genai.types.ThinkingConfig(thinking_budget=128)
                )
            )
            
            return {
                "translated_text": response.text.strip(),
                "confidence_score": 0.9,
                "translation_notes": "Gemini 2.5 Flash 翻譯"
            }
            
        except Exception as e:
            logger.error(f"回退翻譯失敗：{e}")
            return {
                "translated_text": text,
                "confidence_score": 0.0,
                "translation_notes": f"翻譯失敗：{str(e)}"
            }
    
    def _fallback_get_recommendations(self, food_request: str, user_language: str = 'zh') -> Dict:
        """回退到原始 Gemini API 推薦"""
        if not GEMINI_AVAILABLE:
            return {
                "recommendations": [],
                "analysis": {"error": "Gemini API 不可用"},
                "confidence_score": 0.0
            }
        
        try:
            # 設定 Gemini API
            from google import genai
            genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
            
            # 獲取店家資料
            from app.models import Store
            stores = Store.query.all()
            store_data = []
            
            for store in stores:
                store_info = {
                    'store_id': store.store_id,
                    'store_name': store.store_name,
                    'partner_level': store.partner_level,
                    'review_summary': store.review_summary or '',
                    'top_dishes': [
                        store.top_dish_1, store.top_dish_2, store.top_dish_3,
                        store.top_dish_4, store.top_dish_5
                    ],
                    'main_photo_url': store.main_photo_url
                }
                store_info['top_dishes'] = [dish for dish in store_info['top_dishes'] if dish]
                store_data.append(store_info)
            
            # 建立推薦提示詞
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
            
            # 調用 Gemini API
            response = genai.Client().models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
                config=genai.types.GenerateContentConfig(
                    thinking_config=genai.types.ThinkingConfig(thinking_budget=128)
                )
            )
            
            # 解析回應
            result = json.loads(response.text)
            
            if 'recommendations' in result and result['recommendations']:
                # 按照合作等級排序
                recommendations = sorted(
                    result['recommendations'], 
                    key=lambda x: x.get('partner_level', 0), 
                    reverse=True
                )
                return {
                    "recommendations": recommendations[:5],
                    "analysis": result.get('analysis', {}),
                    "confidence_score": 0.8
                }
            else:
                return {
                    "recommendations": [],
                    "analysis": {"error": "無推薦結果"},
                    "confidence_score": 0.0
                }
                
        except Exception as e:
            logger.error(f"回退推薦失敗：{e}")
            return {
                "recommendations": [],
                "analysis": {"error": f"推薦失敗：{str(e)}"},
                "confidence_score": 0.0
            }
    
    def get_integration_stats(self) -> Dict:
        """獲取整合統計資訊"""
        return {
            "langchain_available": LANGCHAIN_AVAILABLE,
            "gemini_available": GEMINI_AVAILABLE,
            "use_langchain": self.use_langchain,
            "enhanced_processor_available": self.enhanced_processor is not None,
            "ai_manager_available": self.ai_manager is not None,
            "timestamp": datetime.now().isoformat()
        }

# 全域整合器實例
integration = LangChainIntegration()

def get_integration() -> LangChainIntegration:
    """獲取整合器實例"""
    return integration

# 便捷函數
def integrated_menu_ocr(image_path: str, target_language: str = 'en') -> Dict:
    """整合菜單 OCR 處理"""
    return integration.process_menu_ocr_langchain(image_path, target_language)

def integrated_translate_text(text: str, target_language: str = 'en', context: str = None) -> Dict:
    """整合文字翻譯"""
    return integration.translate_text_langchain(text, target_language, context)

def integrated_get_recommendations(food_request: str, user_language: str = 'zh', 
                                 user_history: List = None) -> Dict:
    """整合餐飲推薦"""
    return integration.get_recommendations_langchain(food_request, user_language, user_history) 