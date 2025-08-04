# =============================================================================
# 檔案名稱：app/langchain_enhancement.py
# 功能描述：LangChain 強化模組，提升 AI 答案準確度
# 主要功能：
# - 記憶體管理（Conversation Memory）
# - 檢索增強生成（RAG）
# - 鏈式處理（Chains）
# - 輸出解析和驗證
# - 錯誤處理和回退
# =============================================================================

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

# LangChain 相關導入
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import HumanMessage, SystemMessage, AIMessage
    from langchain.prompts import ChatPromptTemplate, PromptTemplate
    from langchain.output_parsers import PydanticOutputParser, ResponseSchema, StructuredOutputParser
    from langchain.chains import LLMChain, ConversationChain, RetrievalQA
    from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
    from langchain.embeddings import GooglePalmEmbeddings
    from langchain.vectorstores import FAISS
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.document_loaders import TextLoader
    from pydantic import BaseModel, Field
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️ LangChain 未安裝，請執行：pip install langchain langchain-google-genai faiss-cpu")

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LangChainConfig:
    """LangChain 配置類別"""
    model_name: str = "gemini-pro"
    temperature: float = 0.1
    max_tokens: int = 4000
    memory_type: str = "buffer"  # buffer, summary
    enable_rag: bool = True
    enable_validation: bool = True
    enable_fallback: bool = True

class EnhancedAIProcessor:
    """強化 AI 處理器"""
    
    def __init__(self, config: LangChainConfig = None):
        self.config = config or LangChainConfig()
        self.memory = None
        self.vector_store = None
        self.llm = None
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化 LangChain 組件"""
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain 未安裝，使用基礎模式")
            return
        
        try:
            # 初始化 LLM
            self.llm = ChatGoogleGenerativeAI(
                model=self.config.model_name,
                google_api_key=os.getenv('GEMINI_API_KEY'),
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            # 初始化記憶體
            if self.config.memory_type == "summary":
                self.memory = ConversationSummaryMemory(
                    llm=self.llm,
                    memory_key="chat_history",
                    return_messages=True
                )
            else:
                self.memory = ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True
                )
            
            # 初始化向量資料庫（如果啟用 RAG）
            if self.config.enable_rag:
                self._initialize_vector_store()
                
        except Exception as e:
            logger.error(f"初始化 LangChain 組件失敗：{e}")
    
    def _initialize_vector_store(self):
        """初始化向量資料庫"""
        try:
            # 這裡可以載入您的知識庫資料
            # 例如：菜單資料、店家資訊、常見問題等
            knowledge_base = self._load_knowledge_base()
            
            if knowledge_base:
                # 分割文本
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                texts = text_splitter.split_text(knowledge_base)
                
                # 建立向量資料庫
                embeddings = GooglePalmEmbeddings(
                    google_api_key=os.getenv('GEMINI_API_KEY')
                )
                self.vector_store = FAISS.from_texts(texts, embeddings)
                
        except Exception as e:
            logger.error(f"初始化向量資料庫失敗：{e}")
    
    def _load_knowledge_base(self) -> str:
        """載入知識庫資料"""
        # 這裡可以從資料庫或檔案載入知識庫
        # 例如：常見問題、店家資訊、菜單資料等
        knowledge_base = """
        餐飲推薦常見問題：
        1. 如何選擇適合的餐廳？
        2. 如何處理過敏需求？
        3. 如何推薦適合的菜色？
        4. 如何處理特殊飲食需求？
        
        推薦策略：
        1. 根據用戶偏好推薦
        2. 考慮店家評分和評論
        3. 考慮距離和便利性
        4. 考慮價格範圍
        5. 考慮營業時間
        """
        return knowledge_base
    
    def create_enhanced_prompt_chain(self, prompt_type: str) -> LLMChain:
        """創建強化提示詞鏈"""
        if not LANGCHAIN_AVAILABLE:
            return None
        
        # 根據不同類型建立不同的提示詞模板
        if prompt_type == "menu_ocr":
            template = self._get_menu_ocr_template()
        elif prompt_type == "recommendation":
            template = self._get_recommendation_template()
        elif prompt_type == "translation":
            template = self._get_translation_template()
        else:
            template = self._get_general_template()
        
        # 建立輸出解析器
        parser = self._create_output_parser(prompt_type)
        
        # 建立鏈
        chain = LLMChain(
            llm=self.llm,
            prompt=template,
            memory=self.memory,
            verbose=True
        )
        
        return chain, parser
    
    def _get_menu_ocr_template(self) -> ChatPromptTemplate:
        """菜單 OCR 提示詞模板"""
        return ChatPromptTemplate.from_messages([
            ("system", """你是一個專業的菜單辨識專家，具有以下能力：
1. 高精度 OCR 辨識
2. 智能分類和結構化
3. 多語言翻譯
4. 價格標準化
5. 信心度評估

請仔細分析菜單圖片，並提供最準確的結構化資料。"""),
            ("human", """請分析這張菜單圖片：

{image_data}

目標語言：{target_language}

{format_instructions}

請確保：
- 價格格式統一為數字
- 分類準確（主食、飲料、小菜、甜點等）
- 翻譯準確且符合當地文化
- 提供信心度評估""")
        ])
    
    def _get_recommendation_template(self) -> ChatPromptTemplate:
        """推薦系統提示詞模板"""
        return ChatPromptTemplate.from_messages([
            ("system", """你是一個專業的餐飲推薦專家，具有以下能力：
1. 深度分析用戶需求
2. 智能匹配店家特色
3. 考慮多種因素（評分、距離、價格等）
4. 提供個性化推薦
5. 解釋推薦理由"""),
            ("human", """用戶需求：{user_request}

可用店家：{available_stores}

歷史偏好：{user_history}

{format_instructions}

請提供：
- 最適合的店家推薦
- 詳細的推薦理由
- 用戶偏好分析
- 推薦信心度""")
        ])
    
    def _get_translation_template(self) -> ChatPromptTemplate:
        """翻譯提示詞模板"""
        return ChatPromptTemplate.from_messages([
            ("system", """你是一個專業的多語言翻譯專家，具有以下能力：
1. 準確理解語境
2. 保持文化適應性
3. 使用正確的專業術語
4. 保持語調一致性
5. 提供翻譯說明"""),
            ("human", """原文：{original_text}

目標語言：{target_language}

語境：{context}

{format_instructions}

請確保：
- 翻譯準確性
- 文化適應性
- 專業術語正確性
- 語調一致性""")
        ])
    
    def _get_general_template(self) -> ChatPromptTemplate:
        """通用提示詞模板"""
        return ChatPromptTemplate.from_messages([
            ("system", """你是一個專業的 AI 助手，具有以下能力：
1. 準確理解用戶需求
2. 提供有用的建議
3. 保持對話的連貫性
4. 處理複雜的查詢
5. 提供詳細的解釋"""),
            ("human", """用戶查詢：{user_query}

上下文：{context}

{format_instructions}

請提供：
- 準確的回答
- 詳細的解釋
- 相關的建議""")
        ])
    
    def _create_output_parser(self, prompt_type: str):
        """創建輸出解析器"""
        if prompt_type == "menu_ocr":
            return self._create_menu_ocr_parser()
        elif prompt_type == "recommendation":
            return self._create_recommendation_parser()
        elif prompt_type == "translation":
            return self._create_translation_parser()
        else:
            return self._create_general_parser()
    
    def _create_menu_ocr_parser(self):
        """創建菜單 OCR 輸出解析器"""
        response_schemas = [
            ResponseSchema(name="success", description="處理是否成功", type="boolean"),
            ResponseSchema(name="menu_items", description="菜單項目列表", type="list"),
            ResponseSchema(name="store_info", description="店家資訊", type="dict"),
            ResponseSchema(name="processing_notes", description="處理備註", type="string"),
            ResponseSchema(name="confidence_score", description="信心度", type="float")
        ]
        return StructuredOutputParser.from_response_schemas(response_schemas)
    
    def _create_recommendation_parser(self):
        """創建推薦系統輸出解析器"""
        response_schemas = [
            ResponseSchema(name="recommendations", description="推薦店家列表", type="list"),
            ResponseSchema(name="analysis", description="分析結果", type="dict"),
            ResponseSchema(name="confidence_score", description="推薦信心度", type="float")
        ]
        return StructuredOutputParser.from_response_schemas(response_schemas)
    
    def _create_translation_parser(self):
        """創建翻譯輸出解析器"""
        response_schemas = [
            ResponseSchema(name="translated_text", description="翻譯後文字", type="string"),
            ResponseSchema(name="confidence_score", description="翻譯信心度", type="float"),
            ResponseSchema(name="translation_notes", description="翻譯備註", type="string")
        ]
        return StructuredOutputParser.from_response_schemas(response_schemas)
    
    def _create_general_parser(self):
        """創建通用輸出解析器"""
        response_schemas = [
            ResponseSchema(name="answer", description="回答內容", type="string"),
            ResponseSchema(name="confidence_score", description="信心度", type="float"),
            ResponseSchema(name="suggestions", description="相關建議", type="list")
        ]
        return StructuredOutputParser.from_response_schemas(response_schemas)
    
    def process_with_enhancement(self, prompt_type: str, **kwargs) -> Dict:
        """使用 LangChain 強化處理"""
        try:
            if not LANGCHAIN_AVAILABLE:
                return self._fallback_processing(prompt_type, **kwargs)
            
            # 創建強化鏈
            chain, parser = self.create_enhanced_prompt_chain(prompt_type)
            
            if not chain:
                return self._fallback_processing(prompt_type, **kwargs)
            
            # 準備輸入資料
            input_data = self._prepare_input_data(prompt_type, **kwargs)
            input_data["format_instructions"] = parser.get_format_instructions()
            
            # 執行處理
            response = chain.run(input_data)
            
            # 解析結果
            result = parser.parse(response)
            
            # 驗證和增強結果
            if self.config.enable_validation:
                result = self._validate_and_enhance_result(result, prompt_type)
            
            return result
            
        except Exception as e:
            logger.error(f"LangChain 強化處理失敗：{e}")
            return self._fallback_processing(prompt_type, **kwargs)
    
    def _prepare_input_data(self, prompt_type: str, **kwargs) -> Dict:
        """準備輸入資料"""
        input_data = kwargs.copy()
        
        # 添加記憶體資料
        if self.memory:
            input_data["chat_history"] = self.memory.chat_memory.messages
        
        # 添加 RAG 資料
        if self.config.enable_rag and self.vector_store:
            query = kwargs.get("user_query", "")
            if query:
                docs = self.vector_store.similarity_search(query, k=3)
                input_data["relevant_context"] = "\n".join([doc.page_content for doc in docs])
        
        return input_data
    
    def _validate_and_enhance_result(self, result: Dict, prompt_type: str) -> Dict:
        """驗證和增強結果"""
        if prompt_type == "menu_ocr":
            return self._validate_menu_ocr_result(result)
        elif prompt_type == "recommendation":
            return self._validate_recommendation_result(result)
        elif prompt_type == "translation":
            return self._validate_translation_result(result)
        else:
            return self._validate_general_result(result)
    
    def _validate_menu_ocr_result(self, result: Dict) -> Dict:
        """驗證菜單 OCR 結果"""
        # 價格驗證
        if "menu_items" in result:
            for item in result["menu_items"]:
                if "price" in item:
                    if not isinstance(item["price"], (int, float)) or item["price"] < 0:
                        item["price"] = 0
        
        # 信心度驗證
        if "confidence_score" not in result:
            result["confidence_score"] = 0.5
        
        return result
    
    def _validate_recommendation_result(self, result: Dict) -> Dict:
        """驗證推薦結果"""
        # 確保有推薦項目
        if "recommendations" not in result:
            result["recommendations"] = []
        
        # 信心度驗證
        if "confidence_score" not in result:
            result["confidence_score"] = 0.5
        
        return result
    
    def _validate_translation_result(self, result: Dict) -> Dict:
        """驗證翻譯結果"""
        # 確保有翻譯結果
        if "translated_text" not in result:
            result["translated_text"] = ""
        
        # 信心度驗證
        if "confidence_score" not in result:
            result["confidence_score"] = 0.5
        
        return result
    
    def _validate_general_result(self, result: Dict) -> Dict:
        """驗證通用結果"""
        # 確保有回答
        if "answer" not in result:
            result["answer"] = ""
        
        # 信心度驗證
        if "confidence_score" not in result:
            result["confidence_score"] = 0.5
        
        return result
    
    def _fallback_processing(self, prompt_type: str, **kwargs) -> Dict:
        """回退處理"""
        logger.warning(f"使用回退處理：{prompt_type}")
        
        if prompt_type == "menu_ocr":
            return {
                "success": False,
                "menu_items": [],
                "store_info": {},
                "processing_notes": "LangChain 處理失敗，使用回退模式",
                "confidence_score": 0.0
            }
        elif prompt_type == "recommendation":
            return {
                "recommendations": [],
                "analysis": {"error": "處理失敗"},
                "confidence_score": 0.0
            }
        elif prompt_type == "translation":
            return {
                "translated_text": kwargs.get("original_text", ""),
                "confidence_score": 0.0,
                "translation_notes": "翻譯失敗，回傳原文"
            }
        else:
            return {
                "answer": "處理失敗，請稍後再試",
                "confidence_score": 0.0,
                "suggestions": []
            }
    
    def get_conversation_summary(self) -> str:
        """獲取對話摘要"""
        if self.memory and hasattr(self.memory, 'buffer'):
            return self.memory.buffer
        return ""
    
    def clear_memory(self):
        """清除記憶體"""
        if self.memory:
            self.memory.clear()

# 全域強化處理器實例
enhanced_processor = EnhancedAIProcessor()

def get_enhanced_processor() -> EnhancedAIProcessor:
    """獲取強化處理器實例"""
    return enhanced_processor 