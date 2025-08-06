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
import tempfile
import uuid
import time

# Voice files 存放在 Cloud Run 唯一可寫的 /tmp/voices
VOICE_DIR = "/tmp/voices"
os.makedirs(VOICE_DIR, exist_ok=True)

# Gemini API 設定（延遲初始化）
def get_gemini_client():
    """取得 Gemini 客戶端"""
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("警告: GEMINI_API_KEY 環境變數未設定")
            return None
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Gemini API 初始化失敗: {e}")
        return None

# Azure TTS 設定（延遲初始化）
def get_speech_config():
    """取得 Azure Speech 配置"""
    try:
        # 延遲導入 Azure Speech SDK
        from azure.cognitiveservices.speech import SpeechConfig
        
        speech_key = os.getenv('AZURE_SPEECH_KEY')
        speech_region = os.getenv('AZURE_SPEECH_REGION')
        
        # 檢查環境變數
        if not speech_key:
            print("警告: AZURE_SPEECH_KEY 環境變數未設定")
            return None
        
        if not speech_region:
            print("警告: AZURE_SPEECH_REGION 環境變數未設定")
            return None
        
        print(f"Azure Speech 配置: region={speech_region}")
        
        return SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )
    except ImportError as e:
        print(f"Azure Speech SDK 未安裝: {e}")
        return None
    except Exception as e:
        print(f"Azure Speech Service 配置失敗: {e}")
        return None

def cleanup_old_voice_files(max_age=1800):
    """刪除 30 分鐘以前的 WAV"""
    try:
        now = time.time()
        for fn in os.listdir(VOICE_DIR):
            full = os.path.join(VOICE_DIR, fn)
            if os.path.isfile(full) and now - os.path.getmtime(full) > max_age:
                try:
                    os.remove(full)
                    print(f"清理舊語音檔: {fn}")
                except Exception as e:
                    print(f"清理語音檔失敗 {fn}: {e}")
    except Exception as e:
        print(f"清理語音檔目錄失敗: {e}")

def process_menu_with_gemini(image_path, target_language='en'):
    """
    使用 Gemini 2.5 Flash API 處理菜單圖片
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
        
        # 圖片壓縮優化（減少處理時間）
        max_dimension = 1024  # 最大邊長
        if max(image.size) > max_dimension:
            # 等比例縮放
            ratio = max_dimension / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            print(f"圖片已壓縮至: {image.size}")
        
        # 檢查圖片格式並確定 MIME 類型
        import mimetypes
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'  # 預設為 JPEG
        
        print(f"圖片 MIME 類型: {mime_type}")
        print(f"圖片尺寸: {image.size}")
        
        # 建立 Gemini 提示詞（JSON Mode 優化版）
        prompt = f"""
你是一個菜單 OCR 專家。請分析這張菜單圖片並輸出 JSON 格式的結果。

## 任務：
1. 辨識菜單中的所有項目、價格和描述
2. 將菜名翻譯為 {target_language} 語言
3. 輸出合法的 JSON 物件

## 輸出格式：
{{
  "success": true,
  "menu_items": [
    {{
      "original_name": "原始菜名",
      "translated_name": "翻譯菜名", 
      "price": 數字,
      "description": "描述或null",
      "category": "分類"
    }}
  ],
  "store_info": {{
    "name": "店名",
    "address": "地址或null",
    "phone": "電話或null"
  }},
  "processing_notes": "備註"
}}

## 注意事項：
- 價格必須是整數
- 如果圖片模糊或無法辨識，將 success 設為 false
- 優先處理清晰可見的菜單項目
"""
        
        # 呼叫 Gemini 2.5 Flash API（添加超時控制）
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Gemini API 處理超時")
        
        # 設定 240 秒超時（與 Cloud Run 300秒保持安全邊距）
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(240)
        
        try:
            # 取得 Gemini 客戶端
            gemini_client = get_gemini_client()
            if not gemini_client:
                return {
                    'success': False,
                    'error': 'Gemini API 客戶端初始化失敗',
                    'processing_notes': '請檢查 GEMINI_API_KEY 環境變數'
                }
            
            # 使用 Gemini 2.5 Flash 模型 + JSON Mode
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_bytes
                                }
                            }
                        ]
                    }
                ],
                config={
                    "thinking_config": {
                        "thinking_budget": 128
                    }
                }
            )
            
            # 取消超時
            signal.alarm(0)
            
            # 解析回應
            if response and hasattr(response, 'text'):
                try:
                    # 嘗試解析 JSON
                    result_text = response.text.strip()
                    print(f"Gemini 回應: {result_text[:200]}...")
                    
                    # 如果回應包含 JSON，嘗試解析
                    if '{' in result_text and '}' in result_text:
                        # 提取 JSON 部分
                        start = result_text.find('{')
                        end = result_text.rfind('}') + 1
                        json_text = result_text[start:end]
                        
                        result = json.loads(json_text)
                        
                        # 驗證結果格式
                        if not isinstance(result, dict):
                            return {
                                'success': False,
                                'error': 'Gemini 回應格式錯誤',
                                'processing_notes': '回應不是有效的 JSON 物件'
                            }
                        
                        # 檢查必要欄位
                        if 'success' not in result:
                            result['success'] = True
                        
                        if 'menu_items' not in result:
                            result['menu_items'] = []
                        
                        if 'store_info' not in result:
                            result['store_info'] = {
                                'name': '未知店家',
                                'address': None,
                                'phone': None
                            }
                        
                        print(f"成功處理菜單，共 {len(result.get('menu_items', []))} 個項目")
                        return result
                    else:
                        # 如果沒有 JSON，嘗試結構化處理
                        return {
                            'success': False,
                            'error': '無法從圖片中辨識菜單',
                            'processing_notes': '圖片可能模糊或不是菜單'
                        }
                        
                except json.JSONDecodeError as e:
                    print(f"JSON 解析失敗: {e}")
                    return {
                        'success': False,
                        'error': 'JSON 解析失敗',
                        'processing_notes': f'Gemini 回應格式錯誤: {str(e)}'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Gemini API 回應為空',
                    'processing_notes': '請檢查 API 金鑰和網路連線'
                }
                
        except TimeoutError:
            print("Gemini API 處理超時")
            return {
                'success': False,
                'error': '處理超時',
                'processing_notes': '圖片處理時間過長，請嘗試上傳較小的圖片'
            }
        except Exception as e:
            print(f"Gemini API 處理失敗: {e}")
            return {
                'success': False,
                'error': f'Gemini API 處理失敗: {str(e)}',
                'processing_notes': '請稍後再試或聯繫技術支援'
            }
        finally:
            # 確保取消超時
            signal.alarm(0)
            
    except Exception as e:
        print(f"菜單處理失敗: {e}")
        return {
            'success': False,
            'error': f'菜單處理失敗: {str(e)}',
            'processing_notes': '請檢查圖片格式和大小'
        }

def generate_voice_order(order_id, speech_rate=1.0):
    """
    使用 Azure TTS 生成訂單語音
    """
    # 先 cleanup
    cleanup_old_voice_files()
    try:
        from ..models import Order, OrderItem, MenuItem
        
        # 取得訂單資訊
        order = Order.query.get(order_id)
        if not order:
            return None
        
        # 建立自然的中文訂單文字
        items_for_voice = []
        
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                # 為語音準備：自然的中文表達
                if item.quantity_small == 1:
                    items_for_voice.append(f"{menu_item.item_name}一份")
                else:
                    items_for_voice.append(f"{menu_item.item_name}{item.quantity_small}份")
        
        # 生成自然的中文語音
        if len(items_for_voice) == 1:
            order_text = f"老闆，我要{items_for_voice[0]}，謝謝。"
        else:
            voice_items = "、".join(items_for_voice[:-1]) + "和" + items_for_voice[-1]
            order_text = f"老闆，我要{voice_items}，謝謝。"
        
        # 取得語音配置
        speech_config = get_speech_config()
        if not speech_config:
            print("Azure Speech Service 配置失敗，使用備用方案")
            return generate_voice_order_fallback(order_id, speech_rate)
        
        try:
            # 延遲導入 Azure Speech SDK
            from azure.cognitiveservices.speech import SpeechSynthesizer, AudioConfig
            import uuid
            
            # 設定語音參數
            speech_config.speech_synthesis_voice_name = "zh-TW-HsiaoChenNeural"
            speech_config.speech_synthesis_speaking_rate = speech_rate
            
            # 直接存到 VOICE_DIR
            filename = f"{uuid.uuid4()}.wav"
            audio_path = os.path.join(VOICE_DIR, filename)
            audio_config = AudioConfig(filename=audio_path)
            synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
            
            result = synthesizer.speak_text_async(order_text).get()
            
            if result.reason == ResultReason.SynthesizingAudioCompleted:
                return audio_path
            else:
                print(f"語音生成失敗：{result.reason}")
                return generate_voice_order_fallback(order_id, speech_rate)
                
        except Exception as e:
            print(f"Azure TTS 處理失敗：{e}")
            return generate_voice_order_fallback(order_id, speech_rate)
            
    except Exception as e:
        print(f"語音生成失敗：{e}")
        return generate_voice_order_fallback(order_id, speech_rate)

def generate_voice_from_temp_order(temp_order, speech_rate=1.0):
    """
    為臨時訂單生成中文語音檔
    """
    # 每次呼叫前先清一次舊檔
    cleanup_old_voice_files()
    try:
        # 建立中文訂單文字
        order_text = f"您好，我要點餐。"
        
        for item in temp_order['items']:
            # 使用原始中文菜名
            original_name = item.get('original_name', '')
            quantity = item.get('quantity', 1)
            order_text += f" {original_name} {quantity}份，"
        
        order_text += f"總共{int(temp_order['total_amount'])}元，謝謝。"
        
        # 取得語音配置
        speech_config = get_speech_config()
        if not speech_config:
            print("Azure Speech Service 配置失敗，跳過語音生成")
            return None
        
        try:
            # 延遲導入 Azure Speech SDK
            from azure.cognitiveservices.speech import SpeechSynthesizer, AudioConfig
            
            # 設定語音參數、輸出到 /tmp/voices
            speech_config.speech_synthesis_voice_name = "zh-TW-HsiaoChenNeural"
            speech_config.speech_synthesis_speaking_rate = speech_rate
            filename = f"{uuid.uuid4()}.wav"
            audio_path = os.path.join(VOICE_DIR, filename)
            audio_config = AudioConfig(filename=audio_path)
            synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
            
            result = synthesizer.speak_text_async(order_text).get()
            
            if result.reason == ResultReason.SynthesizingAudioCompleted:
                return audio_path
            else:
                print(f"語音生成失敗：{result.reason}")
                return None
                
        except Exception as e:
            print(f"Azure TTS 處理失敗：{e}")
            return None
            
    except Exception as e:
        print(f"語音生成失敗：{e}")
        return None

def generate_voice_with_custom_rate(order_text, speech_rate=1.0, voice_name="zh-TW-HsiaoChenNeural"):
    """
    生成自定義語速的語音檔
    """
    cleanup_old_voice_files()
    try:
        # 取得語音配置
        speech_config = get_speech_config()
        if not speech_config:
            print("Azure Speech Service 配置失敗，跳過語音生成")
            return None
        
        try:
            # 延遲導入 Azure Speech SDK
            from azure.cognitiveservices.speech import SpeechSynthesizer, AudioConfig
            
            # 設定語音參數
            speech_config.speech_synthesis_voice_name = voice_name
            speech_config.speech_synthesis_speaking_rate = speech_rate
            filename = f"{uuid.uuid4()}.wav"
            audio_path = os.path.join(VOICE_DIR, filename)
            audio_config = AudioConfig(filename=audio_path)
            synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
            
            result = synthesizer.speak_text_async(order_text).get()
            
            if result.reason == ResultReason.SynthesizingAudioCompleted:
                return audio_path
            else:
                print(f"語音生成失敗：{result.reason}")
                return None
                
        except Exception as e:
            print(f"Azure TTS 處理失敗：{e}")
            return None
            
    except Exception as e:
        print(f"語音生成失敗：{e}")
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
    使用 Gemini 2.5 Flash API 翻譯文字
    """
    try:
        from google import genai
        
        # 設定 Gemini API
        genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        
        # 建立翻譯提示詞
        prompt = f"""
        請將以下中文文字翻譯為 {target_language} 語言：
        
        原文：{text}
        
        請只回傳翻譯結果，不要包含任何其他文字。
        """
        
        response = get_gemini_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config={
                "thinking_config": genai.types.ThinkingConfig(thinking_budget=128)
            }
        )
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
            'original_name': str(item.item_name or ''),
            'translated_name': str(translated_name or ''),
            'price_small': item.price_small,
            'price_large': item.price_large,
            'description': str(item.description or ''),
            'translated_description': str(translated_description or ''),
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
        'original_name': str(store.store_name or ''),
        'translated_name': str(translated_name or ''),
        'translated_reviews': str(translated_reviews or ''),
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
    
    # 1. 中文語音內容（改善格式，更自然）
    items_for_voice = []
    items_for_summary = []
    
    for item in order.items:
        menu_item = MenuItem.query.get(item.menu_item_id)
        if menu_item:
            # 為語音準備：自然的中文表達
            if item.quantity_small == 1:
                items_for_voice.append(f"{menu_item.item_name}一份")
            else:
                items_for_voice.append(f"{menu_item.item_name}{item.quantity_small}份")
            
            # 為摘要準備：清晰的格式
            items_for_summary.append(f"{menu_item.item_name} x{item.quantity_small}")
    
    # 生成自然的中文語音
    if len(items_for_voice) == 1:
        chinese_voice_text = f"老闆，我要{items_for_voice[0]}，謝謝。"
    else:
        voice_items = "、".join(items_for_voice[:-1]) + "和" + items_for_voice[-1]
        chinese_voice_text = f"老闆，我要{voice_items}，謝謝。"
    
    # 2. 中文點餐紀錄（改善格式）
    chinese_summary = f"訂單編號：{order.order_id}\n"
    chinese_summary += f"店家：{store.store_name}\n"
    chinese_summary += "訂購項目：\n"
    
    for item_summary in items_for_summary:
        chinese_summary += f"- {item_summary}\n"
    
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
    from ..webhook.routes import get_line_bot_api
    from linebot.models import (
        TextSendMessage, AudioSendMessage, FlexSendMessage,
        QuickReply, QuickReplyButton, MessageAction
    )
    
    order = Order.query.get(order_id)
    if not order:
        print(f"找不到訂單: {order_id}")
        return
    
    user = User.query.get(order.user_id)
    if not user:
        print(f"找不到使用者: {order.user_id}")
        return
    
    # 建立完整訂單確認內容
    confirmation = create_complete_order_confirmation(order_id, user.preferred_lang)
    if not confirmation:
        print(f"無法建立訂單確認內容: {order_id}")
        return
    
    try:
        print(f"開始發送訂單通知: {order_id} -> {user.line_user_id}")
        
        # 1. 生成中文語音檔（標準語速）
        voice_result = generate_voice_order(order_id, 1.0)
        
        # 2. 處理語音結果
        if voice_result and isinstance(voice_result, str) and os.path.exists(voice_result):
            # 成功生成語音檔
            print(f"語音檔生成成功: {voice_result}")
            try:
                with open(voice_result, 'rb') as audio_file:
                    line_bot_api = get_line_bot_api()
                    if line_bot_api:
                        line_bot_api.push_message(
                            user.line_user_id,
                            AudioSendMessage(
                                original_content_url=f"file://{voice_result}",
                                duration=30000  # 預設30秒
                            )
                        )
                        print("語音檔已發送到 LINE")
            except Exception as e:
                print(f"發送語音檔失敗: {e}")
        elif voice_result and isinstance(voice_result, dict):
            # 備用方案：發送文字版本
            print(f"使用備用語音方案: {voice_result.get('text', '')[:50]}...")
            line_bot_api = get_line_bot_api()
            if line_bot_api:
                line_bot_api.push_message(
                    user.line_user_id,
                    TextSendMessage(text=f"🎤 點餐語音（文字版）:\n{voice_result.get('text', '')}")
                )
                print("備用語音文字已發送到 LINE")
        else:
            print("語音生成失敗，跳過語音發送")
        
        # 3. 發送中文點餐紀錄
        line_bot_api = get_line_bot_api()
        if line_bot_api:
            line_bot_api.push_message(
                user.line_user_id,
                TextSendMessage(text=confirmation["chinese_summary"])
            )
            print("中文訂單摘要已發送到 LINE")
        
        # 4. 發送使用者語言的點餐紀錄
        if user.preferred_lang != 'zh':
            line_bot_api.push_message(
                user.line_user_id,
                TextSendMessage(text=confirmation["translated_summary"])
            )
            print(f"{user.preferred_lang} 語訂單摘要已發送到 LINE")
        
        # 5. 發送語速控制按鈕
        send_voice_control_buttons(user.line_user_id, order_id, user.preferred_lang)
        print("語速控制按鈕已發送到 LINE")
        
        # 6. 清理語音檔案
        if voice_result and isinstance(voice_result, str) and os.path.exists(voice_result):
            try:
                os.remove(voice_result)
                print(f"語音檔案已清理: {voice_result}")
            except Exception as e:
                print(f"清理語音檔案失敗: {e}")
        
        print(f"訂單通知發送完成: {order_id}")
            
    except Exception as e:
        print(f"發送訂單確認失敗：{e}")
        import traceback
        traceback.print_exc()

def send_voice_control_buttons(user_id, order_id, user_language):
    """
    發送語音控制按鈕
    """
    from ..webhook.routes import get_line_bot_api
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
    
    try:
        line_bot_api = get_line_bot_api()
        if line_bot_api:
            line_bot_api.push_message(
                user_id,
                TextSendMessage(
                    text=texts["title"],
                    quick_reply=QuickReply(
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
                )
            )
    except Exception as e:
        print(f"發送語音控制按鈕失敗：{e}")

def send_voice_with_rate(user_id, order_id, rate, user_language):
    """
    根據指定語速發送語音
    """
    from ..webhook.routes import get_line_bot_api
    from linebot.models import AudioSendMessage
    
    try:
        # 生成指定語速的語音檔
        voice_path = generate_voice_order(order_id, rate)
        
        if voice_path and os.path.exists(voice_path):
            # 構建語音檔 URL（使用環境變數或預設值）
            fname = os.path.basename(voice_path)
            base_url = os.getenv('BASE_URL', 'https://ordering-helper-backend-1095766716155.asia-east1.run.app')
            audio_url = f"{base_url}/api/voices/{fname}"
            
            line_bot_api = get_line_bot_api()
            if line_bot_api:
                line_bot_api.push_message(
                    user_id,
                    AudioSendMessage(
                        original_content_url=audio_url,
                        duration=30000
                    )
                )
            
    except Exception as e:
        print(f"發送語音失敗：{e}")

def send_temp_order_notification(temp_order, user_id, user_language):
    """
    發送臨時訂單通知
    """
    from ..webhook.routes import get_line_bot_api
    from linebot.models import TextSendMessage, AudioSendMessage
    
    try:
        # 生成語音檔
        voice_path = generate_voice_from_temp_order(temp_order)
        
        # 發送語音檔
        if voice_path and os.path.exists(voice_path):
            # 構建語音檔 URL（使用環境變數或預設值）
            fname = os.path.basename(voice_path)
            base_url = os.getenv('BASE_URL', 'https://ordering-helper-backend-1095766716155.asia-east1.run.app')
            audio_url = f"{base_url}/api/voices/{fname}"
            
            line_bot_api = get_line_bot_api()
            if line_bot_api:
                line_bot_api.push_message(
                    user_id,
                    AudioSendMessage(
                        original_content_url=audio_url,
                        duration=30000
                    )
                )
        
        # 發送訂單摘要
        summary = temp_order.get('summary', '訂單已建立')
        line_bot_api = get_line_bot_api()
        if line_bot_api:
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=summary)
            )
        
        # 發送語音控制按鈕
        send_temp_voice_control_buttons(user_id, temp_order, user_language)
            
    except Exception as e:
        print(f"發送臨時訂單通知失敗：{e}")

def send_temp_voice_control_buttons(user_id, temp_order, user_language):
    """
    發送臨時訂單的語音控制按鈕
    """
    from ..webhook.routes import get_line_bot_api
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
    
    try:
        line_bot_api = get_line_bot_api()
        if line_bot_api:
            line_bot_api.push_message(
                user_id,
                TextSendMessage(
                    text=texts["title"],
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(
                                    label=texts["slow"],
                                    text=f"temp_voice_slow_{temp_order['order_id']}"
                                )
                            ),
                            QuickReplyButton(
                                action=MessageAction(
                                    label=texts["normal"],
                                    text=f"temp_voice_normal_{temp_order['order_id']}"
                                )
                            ),
                            QuickReplyButton(
                                action=MessageAction(
                                    label=texts["fast"],
                                    text=f"temp_voice_fast_{temp_order['order_id']}"
                                )
                            ),
                            QuickReplyButton(
                                action=MessageAction(
                                    label=texts["replay"],
                                    text=f"temp_voice_replay_{temp_order['order_id']}"
                                )
                            )
                        ]
                    )
                )
            )
    except Exception as e:
        print(f"發送臨時訂單語音控制按鈕失敗：{e}")

def get_nearby_stores_with_translations(latitude, longitude, user_language='zh', radius_km=10):
    """
    取得附近店家並包含翻譯資訊
    """
    try:
        # 取得店家翻譯
        store_translations = get_store_translation_from_db(None, user_language)
        
        # 計算距離並篩選
        stores = Store.query.all()
        nearby_stores = []
        
        for store in stores:
            if store.gps_lat and store.gps_lng:
                distance = calculate_distance(
                    latitude, longitude, 
                    store.gps_lat, store.gps_lng
                )
                
                if distance <= radius_km:
                    # 取得翻譯資訊
                    translation = store_translations.get(store.store_id, {})
                    
                    store_data = {
                        'store_id': store.store_id,
                        'store_name': store.store_name,
                        'distance': round(distance, 2),
                        'partner_level': store.partner_level,
                        'description': translation.get('description_trans', ''),
                        'reviews': translation.get('reviews', ''),
                        'main_photo_url': store.main_photo_url,
                        'top_dishes': [
                            store.top_dish_1, store.top_dish_2, 
                            store.top_dish_3, store.top_dish_4, store.top_dish_5
                        ]
                    }
                    nearby_stores.append(store_data)
        
        # 按距離排序
        nearby_stores.sort(key=lambda x: x['distance'])
        return nearby_stores
        
    except Exception as e:
        print(f"取得附近店家失敗：{e}")
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


def generate_voice_order_fallback(order_id, speech_rate=1.0):
    """
    備用語音生成函數（當 Azure TTS 不可用時）
    """
    try:
        from ..models import Order, OrderItem, MenuItem
        
        # 取得訂單資訊
        order = Order.query.get(order_id)
        if not order:
            return None
        
        # 建立自然的中文訂單文字
        items_for_voice = []
        
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                # 為語音準備：自然的中文表達
                if item.quantity_small == 1:
                    items_for_voice.append(f"{menu_item.item_name}一份")
                else:
                    items_for_voice.append(f"{menu_item.item_name}{item.quantity_small}份")
        
        # 生成自然的中文語音
        if len(items_for_voice) == 1:
            order_text = f"老闆，我要{items_for_voice[0]}，謝謝。"
        else:
            voice_items = "、".join(items_for_voice[:-1]) + "和" + items_for_voice[-1]
            order_text = f"老闆，我要{voice_items}，謝謝。"
        
        # 返回文字而非音檔
        print(f"使用備用語音生成，文字內容: {order_text}")
        return {
            'success': True,
            'text': order_text,
            'message': '語音生成功能暫時不可用，請使用文字版本'
        }
        
    except Exception as e:
        print(f"備用語音生成失敗：{e}")
        return None

# =============================================================================
# 新增：非合作店家專用函數
# 功能：使用 Gemini API 生成訂單摘要和語音檔
# =============================================================================

def generate_order_summary_with_gemini(items, user_language='zh'):
    """
    使用 Gemini API 生成訂單摘要
    輸入：訂單項目列表和使用者語言
    輸出：中文摘要和使用者語言摘要
    """
    try:
        # 構建訂單項目文字（改善格式）
        items_text = ""
        total_amount = 0
        item_details = []
        
        for item in items:
            name = item['name']
            quantity = item['quantity']
            subtotal = item['subtotal']
            total_amount += subtotal
            
            # 記錄詳細資訊用於 Gemini API
            item_details.append({
                'name': name,
                'quantity': quantity,
                'price': item.get('price', 0),
                'subtotal': subtotal
            })
            
            items_text += f"{name} x{quantity}、"
        
        # 移除最後一個頓號
        if items_text.endswith('、'):
            items_text = items_text[:-1]
        
        # 構建更詳細的 Gemini 提示詞
        import json
        prompt = f"""
你是一個專業的點餐助手。請根據以下實際的點餐項目生成自然的中文語音和訂單摘要。

## 點餐項目詳情：
{json.dumps(item_details, ensure_ascii=False, indent=2)}

## 總金額：{int(total_amount)}元

請生成：

1. **中文語音內容**（給店家聽的，要自然流暢）：
   - 格式：老闆，我要[實際品項名稱]一份、[實際品項名稱]一杯，謝謝。
   - 要求：使用實際的品項名稱，語言要自然，像是客人親自點餐
   - 避免使用"品項1、品項2"這樣的佔位符
   - 範例：老闆，我要經典夏威夷奶醬義大利麵一份，謝謝。

2. **中文訂單摘要**（給使用者看的）：
   - 格式：[實際品項名稱] x [數量]、[實際品項名稱] x [數量]
   - 要求：清晰列出所有實際品項和數量
   - 避免使用"品項1、品項2"這樣的佔位符
   - 範例：經典夏威夷奶醬義大利麵 x 1

3. **使用者語言摘要**（{user_language}）：
   - 格式：Order: [實際品項名稱] x [qty], [實際品項名稱] x [qty]
   - 要求：使用使用者選擇的語言，翻譯實際品項名稱
   - 避免使用"Item 1、Item 2"這樣的佔位符

## 重要注意事項：
- 必須使用實際的品項名稱，不要使用"品項1、品項2"等佔位符
- 語音內容要自然流暢，適合現場點餐
- 摘要要清晰易讀，便於使用者確認

請以 JSON 格式回傳：
{{
    "chinese_voice": "老闆，我要[實際品項名稱]一份，謝謝。",
    "chinese_summary": "[實際品項名稱] x [數量]",
    "user_summary": "Order: [實際品項名稱] x [qty]"
}}
        """
        
        # 呼叫 Gemini API
        gemini_client = get_gemini_client()
        if not gemini_client:
            # 如果 Gemini API 不可用，使用改善的預設格式
            chinese_voice = f"老闆，我要{items_text}，謝謝。"
            chinese_summary = items_text.replace('、', '、').replace('x', ' x ')
            return {
                "chinese_voice": chinese_voice,
                "chinese_summary": chinese_summary,
                "user_summary": f"Order: {items_text}"
            }
        
        response = gemini_client.generate_content(prompt)
        
        # 嘗試解析 JSON 回應
        try:
            import json
            result = json.loads(response.text)
            
            # 確保回傳格式正確，並檢查是否包含實際品項名稱
            if 'chinese_voice' not in result:
                result['chinese_voice'] = f"老闆，我要{items_text}，謝謝。"
            elif '品項1' in result['chinese_voice'] or '項目1' in result['chinese_voice']:
                # 如果 Gemini 回傳了佔位符，使用實際品項名稱
                result['chinese_voice'] = f"老闆，我要{items_text}，謝謝。"
            
            if 'chinese_summary' not in result:
                result['chinese_summary'] = items_text.replace('、', '、').replace('x', ' x ')
            elif '品項1' in result['chinese_summary'] or '項目1' in result['chinese_summary']:
                # 如果 Gemini 回傳了佔位符，使用實際品項名稱
                result['chinese_summary'] = items_text.replace('、', '、').replace('x', ' x ')
            
            if 'user_summary' not in result:
                result['user_summary'] = f"Order: {items_text}"
            elif 'Item 1' in result['user_summary'] or '項目1' in result['user_summary']:
                # 如果 Gemini 回傳了佔位符，使用實際品項名稱
                result['user_summary'] = f"Order: {items_text}"
            
            return result
        except json.JSONDecodeError:
            # 如果 JSON 解析失敗，使用改善的預設格式
            chinese_voice = f"老闆，我要{items_text}，謝謝。"
            chinese_summary = items_text.replace('、', '、').replace('x', ' x ')
            return {
                "chinese_voice": chinese_voice,
                "chinese_summary": chinese_summary,
                "user_summary": f"Order: {items_text}"
            }
        
    except Exception as e:
        print(f"Gemini API 訂單摘要生成失敗: {e}")
        # 回傳改善的預設格式
        items_text = ""
        for item in items:
            name = item['name']
            quantity = item['quantity']
            items_text += f"{name} x{quantity}、"
        
        if items_text.endswith('、'):
            items_text = items_text[:-1]
        
        chinese_voice = f"老闆，我要{items_text}，謝謝。"
        chinese_summary = items_text.replace('、', '、').replace('x', ' x ')
        
        return {
            "chinese_voice": chinese_voice,
            "chinese_summary": chinese_summary,
            "user_summary": f"Order: {items_text}"
        }

def generate_chinese_voice_with_azure(order_summary, order_id, speech_rate=1.0):
    """
    使用 Azure Speech 生成中文語音檔
    輸入：訂單摘要、訂單ID、語速
    輸出：語音檔絕對路徑
    """
    cleanup_old_voice_files()
    try:
        from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig, ResultReason
        import os
        
        # 取得 Azure Speech 配置
        speech_config = get_speech_config()
        if not speech_config:
            print("Azure Speech 配置不可用")
            return None
        
        # 設定語音參數
        speech_config.speech_synthesis_voice_name = "zh-TW-HsiaoChenNeural"
        speech_config.speech_synthesis_speaking_rate = speech_rate  # 支援語速調整
        
        # 準備語音文字（優先使用 chinese_voice，如果沒有則使用 chinese_summary）
        chinese_text = order_summary.get('chinese_voice', order_summary.get('chinese_summary', '點餐摘要'))
        
        # 生成語音檔路徑（存到 /tmp/voices）
        filename = f"{uuid.uuid4()}.wav"
        voice_path = os.path.join(VOICE_DIR, filename)
        
        # 設定音訊輸出
        audio_config = AudioConfig(filename=voice_path)
        
        # 建立語音合成器
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        
        # 生成語音
        result = synthesizer.speak_text_async(chinese_text).get()
        
        if result.reason == ResultReason.SynthesizingAudioCompleted:
            print(f"語音檔生成成功: {voice_path}, 語速: {speech_rate}")
            return voice_path
        else:
            print(f"語音生成失敗: {result.reason}")
            return None
            
    except Exception as e:
        print(f"Azure Speech 語音生成失敗: {e}")
        return None

# =============================================================================
# LINE Bot 整合函數
# 功能：發送訂單摘要和語音檔給使用者
# =============================================================================

def send_order_to_line_bot(user_id, order_data):
    """
    發送訂單摘要和語音檔給 LINE Bot 使用者
    輸入：使用者ID和訂單資料
    """
    try:
        import os
        import requests
        
        # 取得 LINE Bot 設定
        line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        line_channel_secret = os.getenv('LINE_CHANNEL_SECRET')
        
        if not line_channel_access_token:
            print("警告: LINE_CHANNEL_ACCESS_TOKEN 環境變數未設定")
            return False
        
        # 準備訊息內容
        chinese_summary = order_data.get('chinese_summary', '點餐摘要')
        user_summary = order_data.get('user_summary', 'Order Summary')
        voice_url = order_data.get('voice_url')
        total_amount = order_data.get('total_amount', 0)
        
        # 構建文字訊息
        text_message = f"""
{user_summary}

中文摘要（給店家聽）：
{chinese_summary}

總金額：{int(total_amount)} 元
        """.strip()
        
        # 準備 LINE Bot API 請求
        line_api_url = "https://api.line.me/v2/bot/message/push"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {line_channel_access_token}'
        }
        
        # 構建訊息陣列
        messages = []
        
        # 1. 發送文字摘要
        messages.append({
            "type": "text",
            "text": text_message
        })
        
        # 2. 如果有語音檔，發送語音訊息
        if voice_url and os.path.exists(voice_url):
            # 構建語音檔 URL（使用環境變數或預設值）
            fname = os.path.basename(voice_url)
            base_url = os.getenv('BASE_URL', 'https://ordering-helper-backend-1095766716155.asia-east1.run.app')
            audio_url = f"{base_url}/api/voices/{fname}"
            
            messages.append({
                "type": "audio",
                "originalContentUrl": audio_url,
                "duration": 30000  # 預設30秒
            })
        
        # 3. 發送語音控制按鈕
        messages.append({
            "type": "template",
            "altText": "語音控制選項",
            "template": {
                "type": "buttons",
                "title": "語音控制",
                "text": "選擇語音播放選項",
                "actions": [
                    {
                        "type": "postback",
                        "label": "重新播放",
                        "data": f"replay_voice:{order_data.get('order_id', '')}"
                    },
                    {
                        "type": "postback", 
                        "label": "慢速播放",
                        "data": f"slow_voice:{order_data.get('order_id', '')}"
                    },
                    {
                        "type": "postback",
                        "label": "快速播放", 
                        "data": f"fast_voice:{order_data.get('order_id', '')}"
                    }
                ]
            }
        })
        
        # 發送訊息
        payload = {
            "to": user_id,
            "messages": messages
        }
        
        response = requests.post(line_api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"✅ 成功發送訂單到 LINE Bot，使用者: {user_id}")
            return True
        else:
            print(f"❌ LINE Bot 發送失敗: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ LINE Bot 整合失敗: {e}")
        return False

def upload_file_to_line(file_path, access_token):
    """
    上傳檔案到 LINE Bot
    輸入：檔案路徑和存取權杖
    輸出：檔案ID
    """
    try:
        import requests
        
        # 上傳檔案
        upload_url = "https://api.line.me/v2/bot/message/upload"
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        with open(file_path, 'rb') as file:
            files = {'file': file}
            response = requests.post(upload_url, headers=headers, files=files)
            
        if response.status_code == 200:
            result = response.json()
            return result.get('messageId')
        else:
            print(f"檔案上傳失敗: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"檔案上傳失敗: {e}")
        return None

def send_voice_with_rate(user_id, order_id, rate=1.0):
    """
    根據語速發送語音檔
    輸入：使用者ID、訂單ID、語速
    """
    try:
        import os
        import requests
        from ..webhook.routes import get_line_bot_api
        from linebot.models import AudioSendMessage
        
        # 取得 LINE Bot 設定
        line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        
        if not line_channel_access_token:
            print("警告: LINE_CHANNEL_ACCESS_TOKEN 環境變數未設定")
            return False
        
        # 生成指定語速的語音檔
        voice_path = generate_voice_order(order_id, rate)
        
        if voice_path and os.path.exists(voice_path):
            # 構建語音檔 URL
            fname = os.path.basename(voice_path)
            base_url = os.getenv('BASE_URL', 'https://ordering-helper-backend-1095766716155.asia-east1.run.app')
            audio_url = f"{base_url}/api/voices/{fname}"
            
            # 使用 LINE Bot API 發送語音
            line_bot_api = get_line_bot_api()
            if line_bot_api:
                line_bot_api.push_message(
                    user_id,
                    AudioSendMessage(
                        original_content_url=audio_url,
                        duration=30000
                    )
                )
                print(f"✅ 成功發送語速語音，使用者: {user_id}, 語速: {rate}")
                return True
            else:
                print("❌ LINE Bot API 不可用")
                return False
        else:
            print("❌ 語音檔生成失敗")
            return False
            
    except Exception as e:
        print(f"❌ 語速語音發送失敗: {e}")
        return False
