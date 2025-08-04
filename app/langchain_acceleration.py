#!/usr/bin/env python3
"""
LangChain 加速處理模組
使用 Gemini 2.5 Flash 進行高效處理
"""

import os
import json
import logging
from typing import Dict, List, Optional
from google import genai

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LangChainAcceleration:
    """LangChain 加速處理器"""
    
    def __init__(self):
        """初始化加速處理器"""
        try:
            # 初始化 Gemini 2.5 Flash
            genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
            self.client = genai.Client()
            logger.info("✅ LangChain 加速處理器初始化成功")
        except Exception as e:
            logger.error(f"❌ LangChain 加速處理器初始化失敗：{e}")
            self.client = None
    
    def process_text(self, text: str, task_type: str = "general") -> Dict:
        """處理文字任務"""
        if not self.client:
            return {"error": "處理器未初始化"}
        
        try:
            # 根據任務類型選擇不同的提示詞
            if task_type == "translation":
                prompt = f"請將以下文字翻譯為英文：{text}"
            elif task_type == "summary":
                prompt = f"請總結以下文字：{text}"
            else:
                prompt = f"請處理以下文字：{text}"
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
                config={
                    "thinking_config": genai.types.ThinkingConfig(thinking_budget=128)
                }
            )
            
            return {
                "success": True,
                "result": response.text.strip(),
                "task_type": task_type
            }
            
        except Exception as e:
            logger.error(f"文字處理失敗：{e}")
            return {
                "success": False,
                "error": str(e),
                "task_type": task_type
            }
    
    def process_image(self, image_path: str, task_type: str = "ocr") -> Dict:
        """處理圖片任務"""
        if not self.client:
            return {"error": "處理器未初始化"}
        
        try:
            from PIL import Image
            import io
            
            # 讀取圖片
            with open(image_path, 'rb') as img_file:
                image_bytes = img_file.read()
            
            image = Image.open(io.BytesIO(image_bytes))
            
            # 根據任務類型選擇不同的提示詞
            if task_type == "ocr":
                prompt = "請辨識這張圖片中的文字內容："
            elif task_type == "description":
                prompt = "請描述這張圖片的內容："
            else:
                prompt = "請分析這張圖片："
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    prompt,
                    image
                ],
                config={
                    "thinking_config": genai.types.ThinkingConfig(thinking_budget=256)
                }
            )
            
            return {
                "success": True,
                "result": response.text.strip(),
                "task_type": task_type
            }
            
        except Exception as e:
            logger.error(f"圖片處理失敗：{e}")
            return {
                "success": False,
                "error": str(e),
                "task_type": task_type
            }
    
    def batch_process(self, items: List[Dict]) -> List[Dict]:
        """批次處理多個項目"""
        results = []
        
        for item in items:
            if item.get("type") == "text":
                result = self.process_text(
                    item.get("content", ""),
                    item.get("task_type", "general")
                )
            elif item.get("type") == "image":
                result = self.process_image(
                    item.get("content", ""),
                    item.get("task_type", "ocr")
                )
            else:
                result = {"success": False, "error": "不支援的項目類型"}
            
            results.append(result)
        
        return results

def get_acceleration_processor() -> LangChainAcceleration:
    """取得加速處理器實例"""
    return LangChainAcceleration()

def test_acceleration():
    """測試加速功能"""
    print("🧪 測試 LangChain 加速功能...")
    
    processor = get_acceleration_processor()
    
    # 測試文字處理
    text_result = processor.process_text("你好，世界", "translation")
    print(f"文字處理結果：{text_result}")
    
    print("✅ LangChain 加速功能測試完成")

if __name__ == "__main__":
    test_acceleration() 