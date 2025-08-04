#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 LangChain 強化菜單 OCR 處理
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel, Field
from typing import List, Optional
import json
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv('notebook.env')

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
    
    # 初始化 LangChain
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        google_api_key=os.getenv('GEMINI_API_KEY'),
        temperature=0.1,
        max_tokens=4000
    )
    
    # 建立結構化輸出解析器
    parser = PydanticOutputParser(pydantic_object=MenuProcessingResult)
    
    # 建立提示詞模板
    prompt_template = ChatPromptTemplate.from_messages([
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
    
    # 建立記憶體（用於多輪對話）
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    # 建立 LangChain
    chain = LLMChain(
        llm=llm,
        prompt=prompt_template,
        memory=memory,
        verbose=True
    )
    
    return chain, parser

def process_menu_with_langchain(image_path, target_language='en'):
    """使用 LangChain 處理菜單"""
    
    try:
        # 讀取圖片
        with open(image_path, 'rb') as img_file:
            image_data = img_file.read()
        
        # 創建處理器
        chain, parser = create_enhanced_menu_processor()
        
        # 執行處理
        response = chain.run({
            "image_data": image_data,
            "target_language": target_language,
            "format_instructions": parser.get_format_instructions()
        })
        
        # 解析結果
        result = parser.parse(response)
        
        # 添加額外的驗證和後處理
        result = validate_and_enhance_result(result)
        
        return result.dict()
        
    except Exception as e:
        print(f"LangChain 處理失敗：{e}")
        return {
            "success": False,
            "menu_items": [],
            "store_info": {},
            "processing_notes": f"LangChain 處理失敗：{str(e)}",
            "confidence_score": 0.0
        }

def validate_and_enhance_result(result):
    """驗證和增強結果"""
    
    # 價格驗證
    for item in result.menu_items:
        if item.price < 0:
            item.price = 0
        if item.price > 10000:  # 異常高價
            item.price = 0
    
    # 分類標準化
    category_mapping = {
        "主食": ["飯", "麵", "粥", "餃子", "包子"],
        "飲料": ["茶", "咖啡", "果汁", "汽水", "奶茶"],
        "小菜": ["小菜", "涼菜", "開胃菜"],
        "甜點": ["蛋糕", "冰淇淋", "布丁", "甜點"]
    }
    
    for item in result.menu_items:
        # 智能分類
        for category, keywords in category_mapping.items():
            if any(keyword in item.original_name for keyword in keywords):
                item.category = category
                break
    
    # 信心度調整
    if len(result.menu_items) == 0:
        result.confidence_score = 0.0
    elif result.confidence_score < 0.5:
        result.confidence_score = 0.5  # 最低信心度
    
    return result

def create_menu_qa_chain():
    """創建菜單問答鏈"""
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        google_api_key=os.getenv('GEMINI_API_KEY'),
        temperature=0.3
    )
    
    # 建立問答提示詞
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一個專業的餐飲顧問，基於菜單資訊回答顧客問題。
請提供準確、實用的建議。"""),
        ("human", """菜單資訊：
{menu_data}

顧客問題：{question}

請提供詳細的回答：""")
    ])
    
    return LLMChain(llm=llm, prompt=qa_prompt)

def answer_menu_question(menu_data, question):
    """回答菜單相關問題"""
    
    try:
        chain = create_menu_qa_chain()
        response = chain.run({
            "menu_data": json.dumps(menu_data, ensure_ascii=False, indent=2),
            "question": question
        })
        return response
    except Exception as e:
        return f"無法回答問題：{str(e)}"

# 測試函數
def test_langchain_enhancement():
    """測試 LangChain 強化功能"""
    
    print("🔧 測試 LangChain 強化功能...")
    
    # 模擬菜單資料
    sample_menu = {
        "menu_items": [
            {"original_name": "牛肉麵", "translated_name": "Beef Noodle Soup", "price": 120, "category": "主食"},
            {"original_name": "紅茶", "translated_name": "Black Tea", "price": 30, "category": "飲料"}
        ],
        "store_info": {"name": "小螺波 慶城店", "address": "台北市信義區"}
    }
    
    # 測試問答功能
    question = "這家店有什麼推薦的飲料？"
    answer = answer_menu_question(sample_menu, question)
    
    print(f"📝 問題：{question}")
    print(f"🤖 回答：{answer}")
    
    return True

if __name__ == "__main__":
    test_langchain_enhancement() 