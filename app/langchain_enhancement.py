#!/usr/bin/env python3
"""
LangChain 增強處理模組
使用 Gemini 2.5 Flash 進行高級處理
"""

import os
import json
import logging
from typing import Dict, List, Optional
from google import genai

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LangChainEnhancement:
    """LangChain 增強處理器"""
    
    def __init__(self):
        """初始化增強處理器"""
        try:
            # 初始化 Gemini 2.5 Flash
            genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
            self.client = genai.Client()
            logger.info("✅ LangChain 增強處理器初始化成功")
        except Exception as e:
            logger.error(f"❌ LangChain 增強處理器初始化失敗：{e}")
            self.client = None
    
    def enhanced_text_processing(self, text: str, enhancement_type: str = "general") -> Dict:
        """增強文字處理"""
        if not self.client:
            return {"error": "處理器未初始化"}
        
        try:
            # 根據增強類型選擇不同的提示詞
            if enhancement_type == "sentiment":
                prompt = f"請分析以下文字的情感傾向：{text}"
            elif enhancement_type == "summary":
                prompt = f"請為以下文字提供詳細摘要：{text}"
            elif enhancement_type == "translation":
                prompt = f"請將以下文字翻譯為英文：{text}"
            elif enhancement_type == "correction":
                prompt = f"請修正以下文字中的錯誤：{text}"
            else:
                prompt = f"請對以下文字進行一般處理：{text}"
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
                config=genai.types.GenerateContentConfig(
                    thinking_config=genai.types.ThinkingConfig(thinking_budget=256)
                )
            )
            
            return {
                "success": True,
                "result": response.text.strip(),
                "enhancement_type": enhancement_type
            }
            
        except Exception as e:
            logger.error(f"增強文字處理失敗：{e}")
            return {
                "success": False,
                "error": str(e),
                "enhancement_type": enhancement_type
            }
    
    def enhanced_image_analysis(self, image_path: str, analysis_type: str = "general") -> Dict:
        """增強圖片分析"""
        if not self.client:
            return {"error": "處理器未初始化"}
        
        try:
            from PIL import Image
            import io
            
            # 讀取圖片
            with open(image_path, 'rb') as img_file:
                image_bytes = img_file.read()
            
            image = Image.open(io.BytesIO(image_bytes))
            
            # 根據分析類型選擇不同的提示詞
            if analysis_type == "detailed":
                prompt = "請對這張圖片進行詳細分析，包括內容、風格、色彩等："
            elif analysis_type == "ocr":
                prompt = "請準確辨識這張圖片中的所有文字內容："
            elif analysis_type == "objects":
                prompt = "請識別這張圖片中的主要物件："
            else:
                prompt = "請分析這張圖片的內容："
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    prompt,
                    image
                ],
                config=genai.types.GenerateContentConfig(
                    thinking_config=genai.types.ThinkingConfig(thinking_budget=512)
                )
            )
            
            return {
                "success": True,
                "result": response.text.strip(),
                "analysis_type": analysis_type
            }
            
        except Exception as e:
            logger.error(f"增強圖片分析失敗：{e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_type": analysis_type
            }
    
    def multi_modal_processing(self, text: str, image_path: str) -> Dict:
        """多模態處理（文字+圖片）"""
        if not self.client:
            return {"error": "處理器未初始化"}
        
        try:
            from PIL import Image
            import io
            
            # 讀取圖片
            with open(image_path, 'rb') as img_file:
                image_bytes = img_file.read()
            
            image = Image.open(io.BytesIO(image_bytes))
            
            prompt = f"""
請結合以下文字和圖片進行分析：

文字內容：{text}

請提供綜合分析結果。
"""
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    prompt,
                    image
                ],
                config=genai.types.GenerateContentConfig(
                    thinking_config=genai.types.ThinkingConfig(thinking_budget=512)
                )
            )
            
            return {
                "success": True,
                "result": response.text.strip(),
                "processing_type": "multimodal"
            }
            
        except Exception as e:
            logger.error(f"多模態處理失敗：{e}")
            return {
                "success": False,
                "error": str(e),
                "processing_type": "multimodal"
            }

def get_enhancement_processor() -> LangChainEnhancement:
    """取得增強處理器實例"""
    return LangChainEnhancement()

def test_enhancement():
    """測試增強功能"""
    print("🧪 測試 LangChain 增強功能...")
    
    processor = get_enhancement_processor()
    
    # 測試文字處理
    text_result = processor.enhanced_text_processing("這是一個測試文字", "summary")
    print(f"文字處理結果：{text_result}")
    
    print("✅ LangChain 增強功能測試完成")

if __name__ == "__main__":
    test_enhancement() 