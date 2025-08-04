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

# Azure TTS 設定（延遲初始化）
def get_speech_config():
    """取得 Azure Speech 配置"""
    try:
        speech_key = os.getenv('AZURE_SPEECH_KEY')
        speech_region = os.getenv('AZURE_SPEECH_REGION')
        
        if not speech_key or not speech_region:
            print("警告: Azure Speech Service 環境變數未設定")
            return None
        
        return SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )
    except Exception as e:
        print(f"Azure Speech Service 配置失敗: {e}")
        return None

def process_menu_with_gemini(image_path, target_language='en'):
    """
    使用 Gemini API 處理菜單圖片
    1. OCR 辨識菜單文字
    2. 結構化為菜單項目
    3. 翻譯為目標語言
    """
    try:
        # 檢查檔案大小
        file_size = os.path.getsize(image_path)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            return {
                'success': False,
                'error': f'檔案太大 ({file_size / 1024 / 1024:.1f}MB)，請上傳較小的圖片'
            }
        
        print(f"處理圖片: {image_path}, 大小: {file_size / 1024:.1f}KB")
        
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
        
        print(f"圖片 MIME 類型: {mime_type}")
        print(f"圖片大小: {len(image_bytes)} bytes")
        print(f"圖片尺寸: {image.size}")
        
        # 建立 Gemini 提示詞
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
- 請在 30 秒內完成處理
"""
        
        # 呼叫 Gemini API（添加超時控制）
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Gemini API 處理超時")
        
        # 設定 60 秒超時
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)
        
        try:
            # 使用 PIL.Image 格式調用 Gemini API
            response = model.generate_content([prompt, image])
            signal.alarm(0)  # 取消超時
            
            # 解析回應
        except TimeoutError:
            signal.alarm(0)  # 取消超時
            return {
                'success': False,
                'error': 'OCR 處理超時，請稍後再試或上傳較小的圖片',
                'menu_items': [],
                'store_info': {},
                'processing_notes': '處理超時'
            }
        except Exception as e:
            signal.alarm(0)  # 取消超時
            print(f"Gemini API 錯誤: {e}")
            return {
                'success': False,
                'error': f'OCR 處理失敗: {str(e)}',
                'menu_items': [],
                'store_info': {},
                'processing_notes': f'處理失敗: {str(e)}'
            }
        
        try:
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
            
        except json.JSONDecodeError as e:
            print(f"JSON 解析失敗：{e}")
            print(f"回應內容：{response.text}")
            return {
                "success": False,
                "menu_items": [],
                "store_info": {},
                "processing_notes": f"JSON 解析失敗：{str(e)}"
            }
        
    except Exception as e:
        print(f"Gemini API 處理失敗：{e}")
        return {
            "success": False,
            "menu_items": [],
            "store_info": {},
            "processing_notes": f"處理失敗：{str(e)}"
        }

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
        
        # 取得語音配置
        speech_config = get_speech_config()
        if not speech_config:
            print("Azure Speech Service 配置失敗，跳過語音生成")
            return None
        
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

def generate_voice_from_temp_order(temp_order, speech_rate=1.0):
    """
    為臨時訂單生成中文語音檔
    """
    try:
        # 建立中文訂單文字
        order_text = f"您好，我要點餐。"
        
        for item in temp_order['items']:
            # 使用原始中文菜名
            original_name = item.get('original_name', '')
            quantity = item.get('quantity', 1)
            order_text += f" {original_name} {quantity}份，"
        
        order_text += f"總共{temp_order['total_amount']}元，謝謝。"
        
        # 取得語音配置
        speech_config = get_speech_config()
        if not speech_config:
            print("Azure Speech Service 配置失敗，跳過語音生成")
            return None
        
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

def generate_voice_with_custom_rate(order_text, speech_rate=1.0, voice_name="zh-TW-HsiaoChenNeural"):
    """
    生成自定義語速的語音檔
    """
    try:
        # 取得語音配置
        speech_config = get_speech_config()
        if not speech_config:
            print("Azure Speech Service 配置失敗，跳過語音生成")
            return None
        
        # 設定語音參數
        speech_config.speech_synthesis_voice_name = voice_name
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
    chinese_summary += f"店家：{store.store_name if store else '未知店家'}\n"
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
        translated_summary += f"Store: {store.store_name if store else 'Unknown Store'}\n"
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
    儲存上傳的檔案並進行圖片壓縮
    """
    import os
    from werkzeug.utils import secure_filename
    from PIL import Image
    import io
    
    # 確保目錄存在
    os.makedirs(folder, exist_ok=True)
    
    # 生成安全的檔名
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    filepath = os.path.join(folder, unique_filename)
    
    try:
        # 讀取圖片並壓縮
        image = Image.open(file)
        
        # 檢查圖片大小，如果太大則壓縮
        max_size = (2048, 2048)  # 最大尺寸
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            print(f"圖片尺寸過大 {image.size}，進行壓縮...")
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 轉換為 RGB 模式（如果是 RGBA）
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # 儲存壓縮後的圖片
        image.save(filepath, 'JPEG', quality=85, optimize=True)
        print(f"圖片已壓縮並儲存: {filepath}")
        
    except Exception as e:
        print(f"圖片壓縮失敗，使用原始檔案: {e}")
        # 如果壓縮失敗，使用原始檔案
        file.save(filepath)
    
    return filepath

def translate_text(text, target_language='en'):
    """
    使用 Gemini API 翻譯文字
    """
    try:
        import google.generativeai as genai
        
        # 設定 Gemini API
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-pro')
        
        # 建立翻譯提示詞
        prompt = f"""
        請將以下中文文字翻譯為 {target_language} 語言：
        
        原文：{text}
        
        請只回傳翻譯結果，不要包含任何其他文字。
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"翻譯失敗：{e}")
        return text  # 如果翻譯失敗，回傳原文

def translate_menu_items(menu_items, target_language='en'):
    """
    翻譯菜單項目
    """
    translated_items = []
    
    for item in menu_items:
        translated_item = {
            'menu_item_id': item.menu_item_id,
            'original_name': item.item_name,
            'translated_name': translate_text(item.item_name, target_language),
            'price_small': item.price_small,
            'price_large': item.price_large,
            'description': item.description,
            'translated_description': translate_text(item.description, target_language) if item.description else None
        }
        translated_items.append(translated_item)
    
    return translated_items

def get_menu_translation_from_db(menu_item_id, target_language):
    """
    從資料庫取得菜單翻譯
    """
    try:
        from ..models import MenuTranslation
        
        translation = MenuTranslation.query.filter_by(
            menu_item_id=menu_item_id,
            lang_code=target_language
        ).first()
        
        return translation
    except Exception as e:
        print(f"取得資料庫翻譯失敗：{e}")
        return None

def get_store_translation_from_db(store_id, target_language):
    """
    從資料庫取得店家翻譯
    """
    try:
        from ..models import StoreTranslation
        
        translation = StoreTranslation.query.filter_by(
            store_id=store_id,
            lang_code=target_language
        ).first()
        
        return translation
    except Exception as e:
        print(f"取得店家翻譯失敗：{e}")
        return None

def translate_text_with_fallback(text, target_language='en'):
    """
    翻譯文字（優先使用資料庫翻譯，如果沒有才使用AI翻譯）
    """
    # 如果是中文，直接回傳
    if target_language == 'zh':
        return text
    
    # 嘗試使用AI翻譯
    try:
        return translate_text(text, target_language)
    except Exception as e:
        print(f"AI翻譯失敗：{e}")
        return text  # 如果翻譯失敗，回傳原文

def translate_menu_items_with_db_fallback(menu_items, target_language='en'):
    """
    翻譯菜單項目（優先使用資料庫翻譯）
    """
    translated_items = []
    
    for item in menu_items:
        # 先嘗試從資料庫取得翻譯
        db_translation = get_menu_translation_from_db(item.menu_item_id, target_language)
        
        if db_translation and db_translation.item_name_trans:
            # 使用資料庫翻譯
            translated_name = db_translation.item_name_trans
            translated_description = db_translation.description
        else:
            # 使用AI翻譯
            translated_name = translate_text_with_fallback(item.item_name, target_language)
            translated_description = translate_text_with_fallback(item.description, target_language) if item.description else None
        
        translated_item = {
            'menu_item_id': item.menu_item_id,
            'original_name': item.item_name,
            'translated_name': translated_name,
            'price_small': item.price_small,
            'price_large': item.price_large,
            'description': item.description,
            'translated_description': translated_description,
            'translation_source': 'database' if db_translation and db_translation.item_name_trans else 'ai'
        }
        translated_items.append(translated_item)
    
    return translated_items

def translate_store_info_with_db_fallback(store, target_language='en'):
    """
    翻譯店家資訊（優先使用資料庫翻譯）
    """
    # 先嘗試從資料庫取得翻譯
    db_translation = get_store_translation_from_db(store.store_id, target_language)
    
    if db_translation:
        # 使用資料庫翻譯
        translated_name = db_translation.description_trans or store.store_name
        translated_reviews = db_translation.reviews
    else:
        # 使用AI翻譯
        translated_name = translate_text_with_fallback(store.store_name, target_language)
        translated_reviews = translate_text_with_fallback(store.review_summary, target_language) if store.review_summary else None
    
    return {
        'store_id': store.store_id,
        'original_name': store.store_name,
        'translated_name': translated_name,
        'translated_reviews': translated_reviews,
        'translation_source': 'database' if db_translation else 'ai'
    }

def create_complete_order_confirmation(order_id, user_language='zh'):
    """
    建立完整的訂單確認內容（包含語音、中文紀錄、使用者語言紀錄）
    """
    from ..models import Order, OrderItem, MenuItem, Store, User
    
    order = Order.query.get(order_id)
    if not order:
        return None
    
    store = Store.query.get(order.store_id)
    user = User.query.get(order.user_id)
    
    # 1. 中文語音內容
    chinese_voice_text = f"您好，我要點餐。"
    for item in order.items:
        menu_item = MenuItem.query.get(item.menu_item_id)
        if menu_item:
            chinese_voice_text += f" {menu_item.item_name} {item.quantity_small}份，"
    chinese_voice_text += f"總共{order.total_amount}元，謝謝。"
    
    # 2. 中文點餐紀錄
    chinese_summary = f"訂單編號：{order.order_id}\n"
    chinese_summary += f"店家：{store.store_name}\n"
    chinese_summary += "訂購項目：\n"
    
    for item in order.items:
        menu_item = MenuItem.query.get(item.menu_item_id)
        if menu_item:
            chinese_summary += f"- {menu_item.item_name} x{item.quantity_small} (${item.subtotal})\n"
    
    chinese_summary += f"總金額：${order.total_amount}"
    
    # 3. 使用者語言的點餐紀錄（優先使用資料庫翻譯）
    if user_language != 'zh':
        # 翻譯店家名稱
        store_translation = translate_store_info_with_db_fallback(store, user_language)
        translated_store_name = store_translation['translated_name']
        
        translated_summary = f"Order #{order.order_id}\n"
        translated_summary += f"Store: {translated_store_name}\n"
        translated_summary += "Items:\n"
        
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                # 優先使用資料庫翻譯
                db_translation = get_menu_translation_from_db(menu_item.menu_item_id, user_language)
                if db_translation and db_translation.item_name_trans:
                    translated_name = db_translation.item_name_trans
                else:
                    translated_name = translate_text_with_fallback(menu_item.item_name, user_language)
                
                translated_summary += f"- {translated_name} x{item.quantity_small} (${item.subtotal})\n"
        
        translated_summary += f"Total: ${order.total_amount}"
    else:
        translated_summary = chinese_summary
    
    return {
        "chinese_voice_text": chinese_voice_text,
        "chinese_summary": chinese_summary,
        "translated_summary": translated_summary,
        "user_language": user_language
    }

def send_complete_order_notification(order_id):
    """
    發送完整的訂單確認通知到 LINE
    包含：兩則訂單文字摘要、中文語音檔、語速控制按鈕
    """
    from ..models import Order, User
    from ..webhook.routes import line_bot_api
    from linebot.models import (
        TextSendMessage, AudioSendMessage, FlexSendMessage,
        QuickReply, QuickReplyButton, MessageAction
    )
    
    order = Order.query.get(order_id)
    if not order:
        return
    
    user = User.query.get(order.user_id)
    if not user:
        return
    
    # 建立完整訂單確認內容
    confirmation = create_complete_order_confirmation(order_id, user.preferred_lang)
    if not confirmation:
        return
    
    try:
        # 1. 生成中文語音檔（標準語速）
        voice_path = generate_voice_order(order_id, 1.0)
        
        # 2. 發送中文語音檔
        if voice_path and os.path.exists(voice_path):
            with open(voice_path, 'rb') as audio_file:
                line_bot_api.push_message(
                    user.line_user_id,
                    AudioSendMessage(
                        original_content_url=f"file://{voice_path}",
                        duration=30000  # 預設30秒
                    )
                )
        
        # 3. 發送中文點餐紀錄
        line_bot_api.push_message(
            user.line_user_id,
            TextSendMessage(text=confirmation["chinese_summary"])
        )
        
        # 4. 發送使用者語言的點餐紀錄
        if user.preferred_lang != 'zh':
            line_bot_api.push_message(
                user.line_user_id,
                TextSendMessage(text=confirmation["translated_summary"])
            )
        
        # 5. 發送語速控制按鈕
        send_voice_control_buttons(user.line_user_id, order_id, user.preferred_lang)
        
        # 6. 清理語音檔案
        if voice_path and os.path.exists(voice_path):
            os.remove(voice_path)
            
    except Exception as e:
        print(f"發送訂單確認失敗：{e}")

def send_voice_control_buttons(user_id, order_id, user_language):
    """
    發送語音控制按鈕
    """
    from ..webhook.routes import line_bot_api
    from linebot.models import (
        TextSendMessage, QuickReply, QuickReplyButton, MessageAction
    )
    
    # 根據使用者語言建立按鈕文字
    button_texts = {
        "zh": {
            "title": "🎤 語音控制",
            "slow": "慢速播放 (0.7x)",
            "normal": "正常播放 (1.0x)",
            "fast": "快速播放 (1.3x)",
            "replay": "重新播放"
        },
        "en": {
            "title": "🎤 Voice Control",
            "slow": "Slow Play (0.7x)",
            "normal": "Normal Play (1.0x)",
            "fast": "Fast Play (1.3x)",
            "replay": "Replay"
        },
        "ja": {
            "title": "🎤 音声制御",
            "slow": "スロー再生 (0.7x)",
            "normal": "通常再生 (1.0x)",
            "fast": "高速再生 (1.3x)",
            "replay": "再再生"
        },
        "ko": {
            "title": "🎤 음성 제어",
            "slow": "느린 재생 (0.7x)",
            "normal": "일반 재생 (1.0x)",
            "fast": "빠른 재생 (1.3x)",
            "replay": "다시 재생"
        }
    }
    
    texts = button_texts.get(user_language, button_texts["zh"])
    
    # 建立快速回覆按鈕
    quick_reply = QuickReply(
        items=[
            QuickReplyButton(
                action=MessageAction(
                    label=texts["slow"],
                    text=f"voice_slow_{order_id}"
                )
            ),
            QuickReplyButton(
                action=MessageAction(
                    label=texts["normal"],
                    text=f"voice_normal_{order_id}"
                )
            ),
            QuickReplyButton(
                action=MessageAction(
                    label=texts["fast"],
                    text=f"voice_fast_{order_id}"
                )
            ),
            QuickReplyButton(
                action=MessageAction(
                    label=texts["replay"],
                    text=f"voice_replay_{order_id}"
                )
            )
        ]
    )
    
    # 發送語音控制訊息
    line_bot_api.push_message(
        user_id,
        TextSendMessage(
            text=texts["title"],
            quick_reply=quick_reply
        )
    )

def send_voice_with_rate(user_id, order_id, rate, user_language):
    """
    發送指定語速的語音檔
    """
    from ..webhook.routes import line_bot_api
    from linebot.models import AudioSendMessage, TextSendMessage
    
    try:
        # 生成指定語速的語音檔
        voice_path = generate_voice_order(order_id, rate)
        
        if voice_path and os.path.exists(voice_path):
            with open(voice_path, 'rb') as audio_file:
                line_bot_api.push_message(
                    user_id,
                    AudioSendMessage(
                        original_content_url=f"file://{voice_path}",
                        duration=30000
                    )
                )
            
            # 發送語速確認訊息
            rate_texts = {
                "zh": f"已生成 {rate}x 語速的語音檔",
                "en": f"Generated voice file with {rate}x speed",
                "ja": f"{rate}x の速度で音声ファイルを生成しました",
                "ko": f"{rate}x 속도로 음성 파일을 생성했습니다"
            }
            
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=rate_texts.get(user_language, rate_texts["zh"]))
            )
            
            # 清理語音檔案
            os.remove(voice_path)
        else:
            # 發送錯誤訊息
            error_texts = {
                "zh": "語音檔生成失敗，請稍後再試",
                "en": "Failed to generate voice file, please try again later",
                "ja": "音声ファイルの生成に失敗しました。後でもう一度お試しください",
                "ko": "음성 파일 생성에 실패했습니다. 나중에 다시 시도해 주세요"
            }
            
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=error_texts.get(user_language, error_texts["zh"]))
            )
            
    except Exception as e:
        print(f"發送語音檔失敗：{e}")

def send_temp_order_notification(temp_order, user_id, user_language):
    """
    發送臨時訂單確認通知到 LINE
    """
    from ..webhook.routes import line_bot_api
    from linebot.models import (
        TextSendMessage, AudioSendMessage, QuickReply, QuickReplyButton, MessageAction
    )
    
    try:
        # 1. 生成中文語音檔
        voice_path = generate_voice_from_temp_order(temp_order, 1.0)
        
        # 2. 建立中文點餐紀錄
        chinese_summary = f"臨時訂單\n"
        chinese_summary += "訂購項目：\n"
        
        for item in temp_order['items']:
            chinese_summary += f"- {item['original_name']} x{item['quantity']} (${item['subtotal']})\n"
        
        chinese_summary += f"總金額：${temp_order['total_amount']}"
        
        # 3. 建立使用者語言摘要
        if user_language != 'zh':
            translated_summary = f"Temporary Order\n"
            translated_summary += "Items:\n"
            
            for item in temp_order['items']:
                translated_name = item.get('translated_name', item['original_name'])
                translated_summary += f"- {translated_name} x{item['quantity']} (${item['subtotal']})\n"
            
            translated_summary += f"Total: ${temp_order['total_amount']}"
        else:
            translated_summary = chinese_summary
        
        # 4. 發送中文語音檔
        if voice_path and os.path.exists(voice_path):
            with open(voice_path, 'rb') as audio_file:
                line_bot_api.push_message(
                    user_id,
                    AudioSendMessage(
                        original_content_url=f"file://{voice_path}",
                        duration=30000
                    )
                )
        
        # 5. 發送中文點餐紀錄
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=chinese_summary)
        )
        
        # 6. 發送使用者語言的點餐紀錄
        if user_language != 'zh':
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=translated_summary)
            )
        
        # 7. 發送語音控制按鈕
        send_temp_voice_control_buttons(user_id, temp_order, user_language)
        
        # 8. 清理語音檔案
        if voice_path and os.path.exists(voice_path):
            os.remove(voice_path)
            
    except Exception as e:
        print(f"發送臨時訂單確認失敗：{e}")

def send_temp_voice_control_buttons(user_id, temp_order, user_language):
    """
    發送臨時訂單語音控制按鈕
    """
    from ..webhook.routes import line_bot_api
    from linebot.models import (
        TextSendMessage, QuickReply, QuickReplyButton, MessageAction
    )
    
    # 根據使用者語言建立按鈕文字
    button_texts = {
        "zh": {
            "title": "🎤 語音控制",
            "slow": "慢速播放 (0.7x)",
            "normal": "正常播放 (1.0x)",
            "fast": "快速播放 (1.3x)",
            "replay": "重新播放"
        },
        "en": {
            "title": "🎤 Voice Control",
            "slow": "Slow Play (0.7x)",
            "normal": "Normal Play (1.0x)",
            "fast": "Fast Play (1.3x)",
            "replay": "Replay"
        },
        "ja": {
            "title": "🎤 音声制御",
            "slow": "スロー再生 (0.7x)",
            "normal": "通常再生 (1.0x)",
            "fast": "高速再生 (1.3x)",
            "replay": "再再生"
        },
        "ko": {
            "title": "🎤 음성 제어",
            "slow": "느린 재생 (0.7x)",
            "normal": "일반 재생 (1.0x)",
            "fast": "빠른 재생 (1.3x)",
            "replay": "다시 재생"
        }
    }
    
    texts = button_texts.get(user_language, button_texts["zh"])
    
    # 建立快速回覆按鈕
    quick_reply = QuickReply(
        items=[
            QuickReplyButton(
                action=MessageAction(
                    label=texts["slow"],
                    text=f"temp_voice_slow_{temp_order['processing_id']}"
                )
            ),
            QuickReplyButton(
                action=MessageAction(
                    label=texts["normal"],
                    text=f"temp_voice_normal_{temp_order['processing_id']}"
                )
            ),
            QuickReplyButton(
                action=MessageAction(
                    label=texts["fast"],
                    text=f"temp_voice_fast_{temp_order['processing_id']}"
                )
            ),
            QuickReplyButton(
                action=MessageAction(
                    label=texts["replay"],
                    text=f"temp_voice_replay_{temp_order['processing_id']}"
                )
            )
        ]
    )
    
    # 發送語音控制訊息
    line_bot_api.push_message(
        user_id,
        TextSendMessage(
            text=texts["title"],
            quick_reply=quick_reply
        )
    )

def get_nearby_stores_with_translations(latitude, longitude, user_language='zh', radius_km=10):
    """
    根據 GPS 座標取得鄰近店家（包含翻譯）
    """
    try:
        from ..models import Store, StoreTranslation
        
        # 取得所有店家
        stores = Store.query.all()
        nearby_stores = []
        
        for store in stores:
            # 檢查店家是否有 GPS 座標
            store_lat = store.gps_lat or store.latitude
            store_lng = store.gps_lng or store.longitude
            
            if store_lat and store_lng:
                # 計算距離（使用 Haversine 公式）
                distance = calculate_distance(
                    latitude, longitude, 
                    store_lat, store_lng
                )
                
                # 檢查是否在指定範圍內
                if distance <= radius_km:
                    # 取得店家翻譯
                    store_translation = get_store_translation_from_db(store.store_id, user_language)
                    
                    # 建立店家資料
                    store_data = {
                        'store_id': store.store_id,
                        'store_name': store.store_name,
                        'partner_level': store.partner_level,
                        'distance': round(distance, 2),
                        'main_photo_url': store.main_photo_url,
                        'gps_lat': store_lat,
                        'gps_lng': store_lng,
                        'place_id': store.place_id
                    }
                    
                    # 加入翻譯資訊
                    if store_translation:
                        store_data['description'] = store_translation.description_trans or store.review_summary or ''
                        store_data['reviews'] = store_translation.reviews or ''
                    else:
                        # 使用 AI 翻譯
                        if user_language != 'zh':
                            store_data['description'] = translate_text_with_fallback(
                                store.review_summary or '', user_language
                            )
                            store_data['reviews'] = ''
                        else:
                            store_data['description'] = store.review_summary or ''
                            store_data['reviews'] = ''
                    
                    nearby_stores.append(store_data)
        
        # 按距離排序
        nearby_stores.sort(key=lambda x: x['distance'])
        
        return nearby_stores
        
    except Exception as e:
        print(f"取得鄰近店家失敗：{e}")
        return []

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    使用 Haversine 公式計算兩點間距離（公里）
    """
    import math
    
    # 將度數轉換為弧度
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine 公式
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # 地球半徑（公里）
    r = 6371
    
    return c * r

def get_partner_level_label(partner_level, language='zh'):
    """
    取得合作等級標籤
    """
    labels = {
        'zh': {0: '非合作', 1: '合作', 2: 'VIP'},
        'en': {0: 'Non-partner', 1: 'Partner', 2: 'VIP'},
        'ja': {0: '非提携', 1: '提携', 2: 'VIP'},
        'ko': {0: '비제휴', 1: '제휴', 2: 'VIP'}
    }
    
    return labels.get(language, labels['zh']).get(partner_level, '非合作')
