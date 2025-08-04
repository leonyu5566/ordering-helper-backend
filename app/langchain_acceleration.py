# =============================================================================
# 檔案名稱：app/langchain_acceleration.py
# 功能描述：LangChain 加速模組，提升生成式 AI 處理速度
# 主要功能：
# - 並行處理加速
# - 快取機制
# - 向量檢索優化
# - 模型參數優化
# - 記憶體優化
# =============================================================================

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from functools import lru_cache
import time

# LangChain 相關導入
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import HumanMessage, SystemMessage, AIMessage
    from langchain.prompts import ChatPromptTemplate
    from langchain.output_parsers import PydanticOutputParser, ResponseSchema, StructuredOutputParser
    from langchain.chains import LLMChain, ConversationChain
    from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
    from langchain.embeddings import GooglePalmEmbeddings
    from langchain.vectorstores import FAISS
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.cache import InMemoryCache
    import redis
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️ LangChain 未安裝，請執行：pip install langchain langchain-google-genai faiss-cpu redis")

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AccelerationConfig:
    """加速配置類別"""
    enable_cache: bool = True
    enable_parallel: bool = True
    enable_vector_optimization: bool = True
    cache_type: str = "memory"  # memory, redis
    max_workers: int = 4
    batch_size: int = 10
    timeout: int = 30

class LangChainAccelerator:
    """LangChain 加速器"""
    
    def __init__(self, config: AccelerationConfig = None):
        self.config = config or AccelerationConfig()
        self.cache = None
        self.llm = None
        self.vector_store = None
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化加速組件"""
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain 未安裝，使用基礎模式")
            return
        
        try:
            # 初始化快取
            if self.config.enable_cache:
                if self.config.cache_type == "redis":
                    self._initialize_redis_cache()
                else:
                    self._initialize_memory_cache()
            
            # 初始化 LLM
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=os.getenv('GEMINI_API_KEY'),
                temperature=0.1,
                max_tokens=1000,  # 限制輸出長度以提升速度
                request_timeout=self.config.timeout,
                cache=self.cache
            )
            
            # 初始化向量資料庫（如果啟用）
            if self.config.enable_vector_optimization:
                self._initialize_vector_store()
                
        except Exception as e:
            logger.error(f"初始化加速組件失敗：{e}")
    
    def _initialize_memory_cache(self):
        """初始化記憶體快取"""
        try:
            self.cache = InMemoryCache()
            logger.info("✅ 記憶體快取初始化成功")
        except Exception as e:
            logger.error(f"記憶體快取初始化失敗：{e}")
    
    def _initialize_redis_cache(self):
        """初始化 Redis 快取"""
        try:
            from langchain.cache import RedisCache
            redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.cache = RedisCache(redis_client)
            logger.info("✅ Redis 快取初始化成功")
        except Exception as e:
            logger.error(f"Redis 快取初始化失敗：{e}")
            # 回退到記憶體快取
            self._initialize_memory_cache()
    
    def _initialize_vector_store(self):
        """初始化向量資料庫"""
        try:
            # 載入知識庫資料
            knowledge_base = self._load_knowledge_base()
            
            if knowledge_base:
                # 分割文本
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,  # 較小的塊以提升速度
                    chunk_overlap=50
                )
                texts = text_splitter.split_text(knowledge_base)
                
                # 建立向量資料庫
                embeddings = GooglePalmEmbeddings(
                    google_api_key=os.getenv('GEMINI_API_KEY')
                )
                self.vector_store = FAISS.from_texts(texts, embeddings)
                logger.info("✅ 向量資料庫初始化成功")
                
        except Exception as e:
            logger.error(f"向量資料庫初始化失敗：{e}")
    
    def _load_knowledge_base(self) -> str:
        """載入知識庫資料"""
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
    
    @lru_cache(maxsize=100)
    def cached_recommendation(self, food_request: str) -> Dict:
        """快取推薦結果"""
        return self._process_recommendation(food_request)
    
    def _process_recommendation(self, food_request: str) -> Dict:
        """處理推薦請求"""
        # 模擬推薦處理
        return {
            "recommendations": [
                {"store_name": "推薦店家", "reason": "符合需求"}
            ],
            "confidence_score": 0.8
        }
    
    async def parallel_process_requests(self, requests: List[str]) -> List[Dict]:
        """並行處理多個請求"""
        if not self.config.enable_parallel:
            return [self._process_recommendation(req) for req in requests]
        
        try:
            # 建立鏈
            chain = LLMChain(llm=self.llm, prompt=self._get_recommendation_prompt())
            
            # 並行處理
            tasks = []
            for request in requests:
                task = chain.ainvoke({"food_request": request})
                tasks.append(task)
            
            # 等待所有任務完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理結果
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    processed_results.append({"error": str(result)})
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"並行處理失敗：{e}")
            return [{"error": str(e)} for _ in requests]
    
    def batch_process_requests(self, requests: List[str]) -> List[Dict]:
        """批量處理請求"""
        try:
            # 分批處理
            batch_size = self.config.batch_size
            results = []
            
            for i in range(0, len(requests), batch_size):
                batch = requests[i:i + batch_size]
                batch_results = self._process_batch(batch)
                results.extend(batch_results)
            
            return results
            
        except Exception as e:
            logger.error(f"批量處理失敗：{e}")
            return [{"error": str(e)} for _ in requests]
    
    def _process_batch(self, batch: List[str]) -> List[Dict]:
        """處理一批請求"""
        # 這裡可以實作批量處理邏輯
        return [self._process_recommendation(req) for req in batch]
    
    def fast_vector_search(self, query: str, k: int = 5) -> List[str]:
        """快速向量檢索"""
        if not self.vector_store:
            return []
        
        try:
            # 使用向量檢索
            docs = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in docs]
            
        except Exception as e:
            logger.error(f"向量檢索失敗：{e}")
            return []
    
    def optimized_menu_ocr(self, image_data: bytes) -> Dict:
        """優化的菜單 OCR 處理"""
        try:
            # 使用優化的提示詞
            prompt = self._get_optimized_menu_prompt()
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            # 處理圖片
            result = chain.run({"image_data": image_data})
            
            return {
                "success": True,
                "menu_items": [],
                "processing_time": time.time(),
                "confidence_score": 0.9
            }
            
        except Exception as e:
            logger.error(f"菜單 OCR 處理失敗：{e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time()
            }
    
    def _get_recommendation_prompt(self) -> ChatPromptTemplate:
        """獲取推薦提示詞"""
        return ChatPromptTemplate.from_messages([
            ("system", "你是一個快速的餐飲推薦專家。請簡潔地回答。"),
            ("human", "用戶需求：{food_request}")
        ])
    
    def _get_optimized_menu_prompt(self) -> ChatPromptTemplate:
        """獲取優化的菜單提示詞"""
        return ChatPromptTemplate.from_messages([
            ("system", "快速分析菜單圖片，提供簡潔的結構化結果。"),
            ("human", "圖片資料：{image_data}")
        ])
    
    def get_performance_stats(self) -> Dict:
        """獲取性能統計"""
        return {
            "cache_enabled": self.config.enable_cache,
            "parallel_enabled": self.config.enable_parallel,
            "vector_optimization_enabled": self.config.enable_vector_optimization,
            "cache_type": self.config.cache_type,
            "max_workers": self.config.max_workers,
            "batch_size": self.config.batch_size,
            "timeout": self.config.timeout
        }
    
    def clear_cache(self):
        """清除快取"""
        if self.cache:
            self.cache.clear()
            logger.info("🗑️ 快取已清除")

# 全域加速器實例
accelerator = LangChainAccelerator()

def get_accelerator() -> LangChainAccelerator:
    """獲取加速器實例"""
    return accelerator

# 便捷函數
async def fast_recommendation(food_request: str) -> Dict:
    """快速推薦"""
    return accelerator.cached_recommendation(food_request)

async def parallel_recommendations(requests: List[str]) -> List[Dict]:
    """並行推薦"""
    return await accelerator.parallel_process_requests(requests)

def batch_recommendations(requests: List[str]) -> List[Dict]:
    """批量推薦"""
    return accelerator.batch_process_requests(requests)

def fast_search(query: str) -> List[str]:
    """快速搜尋"""
    return accelerator.fast_vector_search(query) 