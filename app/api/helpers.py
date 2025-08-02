# =============================================================================
# 檔案名稱：app/api/helpers.py
# 功能描述：提供 API 路由的輔助函數，包含 AI 功能和檔案處理
# 主要職責：
# - Gemini API 整合（OCR 和翻譯）
# - Azure TTS 語音生成
# - 檔案上傳處理
# - 訂單摘要生成
# 支援功能：
# - 菜單圖片 OCR 辨識
# - 多語言翻譯
# - 中文語音生成
# - 檔案安全管理
# =============================================================================

import os
import json
import requests
import google.generativeai as genai
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig
import tempfile
import uuid

# Gemini API 設定
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro-vision')

# Azure TTS 設定
speech_config = SpeechConfig(
    subscription=os.getenv('AZURE_SPEECH_KEY'),
    region=os.getenv('AZURE_SPEECH_REGION')
)

def process_menu_with_gemini(image_path, target_language='en'):
    """
    使用 Gemini API 處理菜單圖片
    1. OCR 辨識菜單文字
    2. 結構化為菜單項目
    3. 翻譯為目標語言
    """
    try:
        # 讀取圖片
        with open(image_path, 'rb') as img_file:
            image_data = img_file.read()
        
        # 建立 Gemini 提示詞
        prompt = f"""
        請分析這張菜單圖片，並執行以下任務：
        
        1. 使用 OCR 辨識所有菜單項目和價格
        2. 將辨識結果結構化為 JSON 格式
        3. 將所有菜名翻譯為 {target_language} 語言
        
        請回傳以下格式的 JSON：
        {{
            "menu_items": [
                {{
                    "original_name": "中文菜名",
                    "translated_name": "翻譯後菜名",
                    "price": 價格,
                    "description": "描述（如果有）"
                }}
            ],
            "store_info": {{
                "name": "店家名稱",
                "address": "地址"
            }}
        }}
        
        請確保 JSON 格式正確，可以直接解析。
        """
        
        # 呼叫 Gemini API
        response = model.generate_content([prompt, image_data])
        
        # 解析回應
        result = json.loads(response.text)
        return result
        
    except Exception as e:
        print(f"Gemini API 處理失敗：{e}")
        return None

def generate_voice_order(order_id, speech_rate=1.0):
    """
    使用 Azure TTS 生成訂單語音
    """
    try:
        from ..models import Order, OrderItem, MenuItem
        
        # 取得訂單資訊
        order = Order.query.get(order_id)
        if not order:
            return None
        
        # 建立中文訂單文字
        order_text = f"您好，我要點餐。"
        
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                order_text += f" {menu_item.item_name} {item.quantity_small}份，"
        
        order_text += f"總共{order.total_amount}元，謝謝。"
        
        # 設定語音參數
        speech_config.speech_synthesis_voice_name = "zh-TW-HsiaoChenNeural"
        speech_config.speech_synthesis_speaking_rate = speech_rate
        
        # 生成語音檔案
        audio_config = AudioConfig(filename=f"temp_audio_{uuid.uuid4()}.wav")
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        
        result = synthesizer.speak_text_async(order_text).get()
        
        if result.reason == "SynthesizingAudioCompleted":
            # 取得生成的音檔路徑
            audio_path = audio_config.filename
            return audio_path
        else:
            print(f"語音生成失敗：{result.reason}")
            return None
            
    except Exception as e:
        print(f"Azure TTS 處理失敗：{e}")
        return None

def create_order_summary(order_id, user_language='zh'):
    """
    建立訂單摘要（雙語）
    """
    from ..models import Order, OrderItem, MenuItem, Store
    
    order = Order.query.get(order_id)
    if not order:
        return None
    
    store = Store.query.get(order.store_id)
    
    # 中文摘要
    chinese_summary = f"訂單編號：{order.order_id}\n"
    chinese_summary += f"店家：{store.store_name}\n"
    chinese_summary += "訂購項目：\n"
    
    for item in order.items:
        menu_item = MenuItem.query.get(item.menu_item_id)
        if menu_item:
            chinese_summary += f"- {menu_item.item_name} x{item.quantity_small}\n"
    
    chinese_summary += f"總金額：${order.total_amount}"
    
    # 翻譯摘要（簡化版）
    if user_language != 'zh':
        # 這裡可以呼叫 Gemini API 進行翻譯
        translated_summary = f"Order #{order.order_id}\n"
        translated_summary += f"Store: {store.store_name}\n"
        translated_summary += "Items:\n"
        
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                translated_summary += f"- {menu_item.item_name} x{item.quantity_small}\n"
        
        translated_summary += f"Total: ${order.total_amount}"
    else:
        translated_summary = chinese_summary
    
    return {
        "chinese": chinese_summary,
        "translated": translated_summary
    }

def save_uploaded_file(file, folder='uploads'):
    """
    儲存上傳的檔案
    """
    import os
    from werkzeug.utils import secure_filename
    
    # 確保目錄存在
    os.makedirs(folder, exist_ok=True)
    
    # 生成安全的檔名
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    filepath = os.path.join(folder, unique_filename)
    
    # 儲存檔案
    file.save(filepath)
    
    return filepath
