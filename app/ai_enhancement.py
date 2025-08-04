# =============================================================================
# 檔案名稱：app/ai_enhancement.py
# 功能描述：AI 強化整合模組，整合 LangChain 功能到現有 AI 系統
# 主要功能：
# - 整合現有的 AI 功能與 LangChain
# - 提供統一的 AI 處理介面
# - 支援多種 AI 任務類型
# - 提供回退機制
# =============================================================================

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# 導入現有模組
from app.prompts import prompt_engineer
from app.api.helpers import get_gemini_model, process_menu_with_gemini, translate_text
from app.webhook.routes import get_ai_recommendations

# 導入 LangChain 強化模組
try:
    from app.langchain_enhancement import get_enhanced_processor, LangChainConfig
    LANGCHAIN_ENHANCEMENT_AVAILABLE = True
except ImportError:
    LANGCHAIN_ENHANCEMENT_AVAILABLE = False
    print("⚠️ LangChain 強化模組未載入")

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIEnhancementManager:
    """AI 強化管理器"""
    
    def __init__(self):
        self.enhanced_processor = None
        self.use_langchain = True
        
        # 初始化 LangChain 強化處理器
        if LANGCHAIN_ENHANCEMENT_AVAILABLE:
            try:
                config = LangChainConfig(
                    model_name="gemini-2.5-flash",
                    temperature=0.1,
                    memory_type="buffer",
                    enable_rag=True,
                    enable_validation=True,
                    enable_fallback=True
                )
                self.enhanced_processor = get_enhanced_processor()
                logger.info("✅ LangChain 強化處理器初始化成功")
            except Exception as e:
                logger.error(f"❌ LangChain 強化處理器初始化失敗：{e}")
                self.use_langchain = False
        else:
            self.use_langchain = False
            logger.warning("⚠️ LangChain 強化功能不可用，使用基礎模式")
    
    def process_menu_ocr(self, image_path: str, target_language: str = 'en') -> Dict:
        """處理菜單 OCR（強化版）"""
        try:
            if self.use_langchain and self.enhanced_processor:
                # 使用 LangChain 強化處理
                logger.info("🔧 使用 LangChain 強化處理菜單 OCR")
                
                # 讀取圖片
                with open(image_path, 'rb') as img_file:
                    image_data = img_file.read()
                
                result = self.enhanced_processor.process_with_enhancement(
                    prompt_type="menu_ocr",
                    image_data=image_data,
                    target_language=target_language
                )
                
                # 驗證結果
                if result.get("success", False):
                    logger.info(f"✅ LangChain 菜單 OCR 處理成功，信心度：{result.get('confidence_score', 0.0)}")
                    return result
                else:
                    logger.warning("⚠️ LangChain 處理失敗，使用基礎模式")
            
            # 回退到基礎處理
            logger.info("🔄 使用基礎菜單 OCR 處理")
            return process_menu_with_gemini(image_path, target_language)
            
        except Exception as e:
            logger.error(f"❌ 菜單 OCR 處理失敗：{e}")
            return {
                "success": False,
                "menu_items": [],
                "store_info": {},
                "processing_notes": f"處理失敗：{str(e)}",
                "confidence_score": 0.0
            }
    
    def process_recommendation(self, food_request: str, user_language: str = 'zh', 
                             user_history: List = None) -> Dict:
        """處理餐飲推薦（強化版）"""
        try:
            if self.use_langchain and self.enhanced_processor:
                # 使用 LangChain 強化處理
                logger.info("🔧 使用 LangChain 強化處理餐飲推薦")
                
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
                
                result = self.enhanced_processor.process_with_enhancement(
                    prompt_type="recommendation",
                    user_request=food_request,
                    available_stores=json.dumps(store_data, ensure_ascii=False, indent=2),
                    user_history=user_history or []
                )
                
                # 驗證結果
                if result.get("recommendations"):
                    logger.info(f"✅ LangChain 推薦處理成功，信心度：{result.get('confidence_score', 0.0)}")
                    return result
                else:
                    logger.warning("⚠️ LangChain 處理失敗，使用基礎模式")
            
            # 回退到基礎處理
            logger.info("🔄 使用基礎餐飲推薦處理")
            return get_ai_recommendations(food_request, user_language)
            
        except Exception as e:
            logger.error(f"❌ 餐飲推薦處理失敗：{e}")
            return {
                "recommendations": [],
                "analysis": {"error": f"處理失敗：{str(e)}"},
                "confidence_score": 0.0
            }
    
    def process_translation(self, text: str, target_language: str = 'en', 
                          context: str = None) -> Dict:
        """處理翻譯（強化版）"""
        try:
            if self.use_langchain and self.enhanced_processor:
                # 使用 LangChain 強化處理
                logger.info("🔧 使用 LangChain 強化處理翻譯")
                
                result = self.enhanced_processor.process_with_enhancement(
                    prompt_type="translation",
                    original_text=text,
                    target_language=target_language,
                    context=context or ""
                )
                
                # 驗證結果
                if result.get("translated_text"):
                    logger.info(f"✅ LangChain 翻譯處理成功，信心度：{result.get('confidence_score', 0.0)}")
                    return result
                else:
                    logger.warning("⚠️ LangChain 處理失敗，使用基礎模式")
            
            # 回退到基礎處理
            logger.info("🔄 使用基礎翻譯處理")
            translated_text = translate_text(text, target_language)
            return {
                "translated_text": translated_text,
                "confidence_score": 0.8,
                "translation_notes": "基礎翻譯處理"
            }
            
        except Exception as e:
            logger.error(f"❌ 翻譯處理失敗：{e}")
            return {
                "translated_text": text,
                "confidence_score": 0.0,
                "translation_notes": f"翻譯失敗：{str(e)}"
            }
    
    def process_general_query(self, user_query: str, context: str = None) -> Dict:
        """處理一般查詢（強化版）"""
        try:
            if self.use_langchain and self.enhanced_processor:
                # 使用 LangChain 強化處理
                logger.info("🔧 使用 LangChain 強化處理一般查詢")
                
                result = self.enhanced_processor.process_with_enhancement(
                    prompt_type="general",
                    user_query=user_query,
                    context=context or ""
                )
                
                # 驗證結果
                if result.get("answer"):
                    logger.info(f"✅ LangChain 查詢處理成功，信心度：{result.get('confidence_score', 0.0)}")
                    return result
                else:
                    logger.warning("⚠️ LangChain 處理失敗，使用基礎模式")
            
            # 回退到基礎處理
            logger.info("🔄 使用基礎查詢處理")
            model = get_gemini_model()
            prompt = f"""
用戶查詢：{user_query}

上下文：{context or ""}

請提供準確、有用的回答。
"""
            response = model.generate_content(prompt)
            return {
                "answer": response.text,
                "confidence_score": 0.7,
                "suggestions": []
            }
            
        except Exception as e:
            logger.error(f"❌ 查詢處理失敗：{e}")
            return {
                "answer": "抱歉，我無法處理您的查詢。請稍後再試。",
                "confidence_score": 0.0,
                "suggestions": []
            }
    
    def get_conversation_context(self) -> str:
        """獲取對話上下文"""
        if self.enhanced_processor:
            return self.enhanced_processor.get_conversation_summary()
        return ""
    
    def clear_conversation_memory(self):
        """清除對話記憶"""
        if self.enhanced_processor:
            self.enhanced_processor.clear_memory()
            logger.info("🗑️ 對話記憶已清除")
    
    def get_processing_stats(self) -> Dict:
        """獲取處理統計資訊"""
        stats = {
            "langchain_enabled": self.use_langchain,
            "enhanced_processor_available": self.enhanced_processor is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.enhanced_processor:
            stats["memory_type"] = self.enhanced_processor.config.memory_type
            stats["rag_enabled"] = self.enhanced_processor.config.enable_rag
            stats["validation_enabled"] = self.enhanced_processor.config.enable_validation
        
        return stats

# 全域 AI 強化管理器實例
ai_enhancement_manager = AIEnhancementManager()

def get_ai_enhancement_manager() -> AIEnhancementManager:
    """獲取 AI 強化管理器實例"""
    return ai_enhancement_manager

# 便捷函數
def enhanced_menu_ocr(image_path: str, target_language: str = 'en') -> Dict:
    """強化菜單 OCR 處理"""
    return ai_enhancement_manager.process_menu_ocr(image_path, target_language)

def enhanced_recommendation(food_request: str, user_language: str = 'zh', 
                          user_history: List = None) -> Dict:
    """強化餐飲推薦處理"""
    return ai_enhancement_manager.process_recommendation(food_request, user_language, user_history)

def enhanced_translation(text: str, target_language: str = 'en', context: str = None) -> Dict:
    """強化翻譯處理"""
    return ai_enhancement_manager.process_translation(text, target_language, context)

def enhanced_query(user_query: str, context: str = None) -> Dict:
    """強化查詢處理"""
    return ai_enhancement_manager.process_general_query(user_query, context) 