# =============================================================================
# 檔案名稱：app/api/helpers.py
# 功能描述：API 輔助函數集合，提供各種業務邏輯處理功能
# 主要職責：
# - 提供 API 路由所需的輔助函數
# - 處理複雜的業務邏輯
# - 整合外部服務（如 Gemini API、Azure Speech 等）
# - 提供資料庫操作的便利函數
# =============================================================================

import os
import uuid
import json
import requests
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import re
import datetime
# from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig, ResultReason
import tempfile
from copy import deepcopy

# =============================================================================
# 新增：中文檢測和防呆轉換器函數
# =============================================================================

# =============================================================================
# Google Cloud Translation API 整合
# 功能：提供批次翻譯服務，支援任意語言
# =============================================================================

def translate_text_batch(texts: List[str], target_language: str, source_language: str = None) -> List[str]:
    """
    使用 Google Cloud Translation API 批次翻譯文字
    
    Args:
        texts: 要翻譯的文字列表
        target_language: 目標語言碼 (如 'fr', 'de', 'th')
        source_language: 來源語言碼 (如 'en', 'zh')，可為 None 自動偵測
    
    Returns:
        翻譯後的文字列表
    """
    try:
        from google.cloud import translate_v3 as translate
        
        # 檢查環境變數
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise Exception("GOOGLE_CLOUD_PROJECT 環境變數未設定")
        
        location = "global"  # 或使用 "us-central1"
        
        # 建立翻譯客戶端
        client = translate.TranslationServiceClient()
        parent = f"projects/{project_id}/locations/{location}"
        
        # 準備翻譯請求
        request_data = {
            "parent": parent,
            "contents": texts,
            "mime_type": "text/plain",
            "target_language_code": target_language,
        }
        
        # 如果指定了來源語言，加入請求
        if source_language:
            request_data["source_language_code"] = source_language
        
        # 執行翻譯
        response = client.translate_text(request=request_data)
        
        # 提取翻譯結果
        translated_texts = [translation.translated_text for translation in response.translations]
        
        return translated_texts
        
    except ImportError:
        # 如果沒有安裝 google-cloud-translate，使用 fallback
        logging.warning("Google Cloud Translation API 未安裝，使用 fallback 翻譯")
        return translate_text_batch_fallback(texts, target_language, source_language)
        
    except Exception as e:
        logging.error(f"Google Cloud Translation API 錯誤: {str(e)}")
        # 使用 fallback 翻譯
        return translate_text_batch_fallback(texts, target_language, source_language)

def translate_text_batch_fallback(texts: List[str], target_language: str, source_language: str = None) -> List[str]:
    """
    Fallback 翻譯函數（當 Google Cloud Translation API 不可用時）
    目前簡單回傳原文，未來可整合其他翻譯服務
    """
    logging.warning(f"使用 fallback 翻譯，目標語言: {target_language}")
    
    # 如果是英文，提供簡單的中文到英文翻譯
    if target_language == 'en':
        # 簡單的中文菜名翻譯對應
        chinese_to_english = {
            '招牌金湯酸菜': 'Signature Golden Soup Pickled Cabbage',
            '白濃雞湯': 'White Thick Chicken Soup',
            '14嚴選 霜降牛': '14 Selected Marbled Beef',
            '雞肉捲': 'Chicken Roll',
            '14嚴選 嫩肩羊': '14 Selected Lamb Shoulder',
            '鱸魚': 'Sea Bass',
            '魚餃': 'Fish Dumplings',
            '養生番茄': 'Healthy Tomato',
            '白蝦': 'White Shrimp',
            '中草蝦': 'Medium Grass Shrimp'
        }
        
        translated_texts = []
        for text in texts:
            # 檢查是否有對應的翻譯
            if text in chinese_to_english:
                translated_texts.append(chinese_to_english[text])
            else:
                # 如果沒有對應翻譯，回傳原文加上標記
                translated_texts.append(f"{text} (English)")
        
        return translated_texts
    
    # 其他語言的簡單對應（可擴展）
    language_names = {
        'fr': 'French', 'de': 'German', 'es': 'Spanish', 'it': 'Italian',
        'pt': 'Portuguese', 'ru': 'Russian', 'ar': 'Arabic', 'hi': 'Hindi',
        'th': 'Thai', 'vi': 'Vietnamese', 'ko': 'Korean', 'ja': 'Japanese'
    }
    
    # 回傳原文加上語言標記（避免翻譯失敗）
    return [f"{text} ({language_names.get(target_language, target_language)})" for text in texts]

def contains_cjk(text: str) -> bool:
    """
    檢測文字是否包含中日韓文字（CJK）
    用於判斷是否為中文菜名
    """
    if not text or not isinstance(text, str):
        return False
    
    # 中日韓統一表意文字範圍
    cjk_ranges = [
        (0x4E00, 0x9FFF),   # 基本中日韓統一表意文字
        (0x3400, 0x4DBF),   # 中日韓統一表意文字擴展A
        (0x20000, 0x2A6DF), # 中日韓統一表意文字擴展B
        (0x2A700, 0x2B73F), # 中日韓統一表意文字擴展C
        (0x2B740, 0x2B81F), # 中日韓統一表意文字擴展D
        (0x2B820, 0x2CEAF), # 中日韓統一表意文字擴展E
        (0xF900, 0xFAFF),   # 中日韓相容表意文字
        (0x2F800, 0x2FA1F), # 中日韓相容表意文字補充
    ]
    
    for char in text:
        char_code = ord(char)
        for start, end in cjk_ranges:
            if start <= char_code <= end:
                return True
    
    return False

def safe_build_localised_name(raw_name: str, zh_name: str | None = None) -> Dict[str, str]:
    """
    安全建立本地化菜名
    若已經抓到 OCR 中文 (zh_name)，就放到 original；
    沒有中文才 fallback 到 raw_name。
    
    Args:
        raw_name: 原始菜名（可能是英文或中文）
        zh_name: OCR 或 Gemini 取得的中文菜名
    
    Returns:
        Dict with 'original' and 'translated' keys
    """
    if zh_name and contains_cjk(zh_name):
        # 有中文菜名，使用中文作為 original
        return {
            'original': zh_name,
            'translated': raw_name
        }
    elif contains_cjk(raw_name):
        # raw_name 本身就是中文
        # 如果 zh_name 存在且不是中文，使用它作為翻譯
        translated_name = zh_name if zh_name and not contains_cjk(zh_name) else raw_name
        return {
            'original': raw_name,
            'translated': translated_name
        }
    else:
        # 沒有中文，先把 raw_name 當 original，再視語言翻譯
        # 如果 zh_name 存在但不是中文，可能是有用的翻譯
        translated_name = zh_name if zh_name and not contains_cjk(zh_name) else raw_name
        return {
            'original': raw_name,
            'translated': translated_name
        }

# =============================================================================
# Pydantic 模型定義
# 功能：定義 API 請求和回應的資料結構
# 用途：確保資料類型的正確性和一致性
# =============================================================================

class LocalisedName(BaseModel):
    """雙語菜名模型"""
    original: str  # 原始中文菜名（OCR辨識結果）
    translated: str  # 翻譯菜名（使用者語言）

class OrderItemRequest(BaseModel):
    """訂單項目請求模型"""
    name: LocalisedName  # 雙語菜名
    quantity: int  # 數量
    price: float  # 價格
    menu_item_id: Optional[int] = None  # 可選的菜單項目 ID（OCR 菜單可能為 None）

class OrderRequest(BaseModel):
    """訂單請求模型"""
    lang: str  # 使用者語言代碼（如 'zh-TW', 'en', 'ja'）
    items: List[OrderItemRequest]  # 訂單項目列表
    line_user_id: Optional[str] = None  # LINE 使用者 ID

# =============================================================================
# 環境變數和配置區塊
# 功能：載入和管理環境變數，設定 API 金鑰和服務配置
# 用途：確保敏感資訊的安全性，提供靈活的配置管理
# =============================================================================

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

# gTTS 設定（替換 Azure Speech）
def get_speech_config():
    """取得語音配置（已改為使用 gTTS）"""
    # 返回一個簡單的配置對象，但實際上我們使用 gTTS
    class MockSpeechConfig:
        def __init__(self):
            self.speech_synthesis_voice_name = "zh-TW-HsiaoChenNeural"
            self.speech_synthesis_speaking_rate = 1.0
    
    print("使用 gTTS 語音生成服務")
    return MockSpeechConfig()

def cleanup_old_voice_files(max_age=3600):
    """刪除 60 分鐘以前的 MP3（延長清理時間）"""
    try:
        import time
        now = time.time()
        cleaned_count = 0
        
        # 確保目錄存在
        os.makedirs(VOICE_DIR, exist_ok=True)
        
        for fn in os.listdir(VOICE_DIR):
            if not fn.endswith('.mp3'):
                continue
                
            full = os.path.join(VOICE_DIR, fn)
            if os.path.isfile(full) and now - os.path.getmtime(full) > max_age:
                try:
                    os.remove(full)
                    cleaned_count += 1
                    print(f"清理舊語音檔: {fn}")
                except Exception as e:
                    print(f"清理語音檔失敗 {fn}: {e}")
        
        if cleaned_count > 0:
            print(f"總共清理了 {cleaned_count} 個舊語音檔案")
            
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
你是一個餐廳菜單解析器。請分析這張菜單圖片並輸出**唯一**的 JSON，符合下列 schema：

## 輸出格式：
{{
  "success": true,
  "menu_items": [
    {{
      "original_name": "原始中文菜名",
      "translated_name": "翻譯為{target_language}的菜名", 
      "price": 數字,
      "description": "描述或null",
      "category": "分類或null"
    }}
  ],
  "store_info": {{
    "name": "店名或null",
    "address": "地址或null",
    "phone": "電話或null"
  }},
  "processing_notes": "備註或null"
}}

## 重要規則：
1. **original_name 必須是圖片中的原始中文菜名**，不要翻譯
2. **translated_name 必須是翻譯為 {target_language} 的菜名**
3. 如果圖片中的菜名已經是 {target_language}，則 original_name 和 translated_name 可以相同
4. 圖片中沒有的店家資訊請回 `null`，不要猜測
5. 一律不要使用 ``` 或任何程式碼區塊語法
6. 價格輸出數字，無法辨識時用 0
7. **只輸出 JSON**，不要其他文字
8. 若圖片模糊或無法辨識，將 success 設為 false
9. 優先處理清晰可見的菜單項目
10. **確保每個菜品都有原始中文名稱和翻譯名稱**
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
            
                    # 使用正確的 Gemini 模型名稱
            response = gemini_client.models.generate_content(
                model="models/gemini-2.5-flash-lite",
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
                        "thinking_budget": 512
                    }
                }
            )
            
            # 取消超時
            signal.alarm(0)
            
            # 解析回應
            if response and hasattr(response, 'text'):
                try:
                    # 使用新的 JSON 解析函數
                    result_text = response.text.strip()
                    print(f"Gemini 回應長度: {len(result_text)} 字符")
                    print(f"Gemini 回應前200字符: {result_text[:200]}...")
                    
                    # 使用強健的 JSON 解析函數
                    result = parse_gemini_json_response(result_text)
                    print("JSON 解析成功")
                    
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
                    
                    # 主要成功條件：以 menu_items 為準，而不是店家資訊
                    if not result.get('menu_items') or len(result['menu_items']) == 0:
                        result['success'] = False
                        result['error'] = '無法從圖片中辨識菜單項目'
                        result['processing_notes'] = '圖片可能模糊或不是菜單'
                        return result
                    
                    if 'store_info' not in result:
                        result['store_info'] = {
                            'name': None,
                            'address': None,
                            'phone': None
                        }
                    
                    # 保底填值：確保店家資訊欄位不會是 None，而是明確的 null 值
                    if result.get('store_info'):
                        store_info = result['store_info']
                        if store_info.get('name') is None:
                            store_info['name'] = None
                            store_info['note'] = 'store_name_not_found_in_image'
                        if store_info.get('address') is None:
                            store_info['address'] = None
                        if store_info.get('phone') is None:
                            store_info['phone'] = None
                    
                    print(f"成功處理菜單，共 {len(result.get('menu_items', []))} 個項目")
                    return result
                        
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

def parse_gemini_json_response(response_text):
    """
    解析 Gemini API 的 JSON 回應，包含多種修復策略
    """
    import re
    import ast
    
    try:
        # 清理回應文本
        result_text = response_text.strip()
        
        # 如果回應包含 JSON，嘗試解析
        if '{' in result_text and '}' in result_text:
            # 提取 JSON 部分
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            json_text = result_text[start:end]
            
            # 策略1: 直接解析
            try:
                return json.loads(json_text)
            except json.JSONDecodeError as e:
                print(f"直接解析失敗: {e}")
                
                # 策略2: 修復常見問題
                try:
                    # 移除尾隨逗號
                    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
                    # 修復引號問題
                    json_text = re.sub(r'([^\\])"([^"]*?)([^\\])"', r'\1"\2\3"', json_text)
                    # 移除可能的控制字符
                    json_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_text)
                    # 修復多餘的逗號
                    json_text = re.sub(r',\s*}', '}', json_text)
                    json_text = re.sub(r',\s*]', ']', json_text)
                    
                    return json.loads(json_text)
                except json.JSONDecodeError as e2:
                    print(f"修復後解析失敗: {e2}")
                    
                    # 策略3: 嘗試提取 menu_items 部分
                    try:
                        # 尋找 menu_items 陣列
                        menu_items_match = re.search(r'"menu_items"\s*:\s*\[(.*?)\]', json_text, re.DOTALL)
                        if menu_items_match:
                            menu_items_content = menu_items_match.group(1)
                            # 嘗試解析每個菜單項目
                            items = []
                            # 簡單的正則表達式來提取項目
                            item_matches = re.findall(r'\{[^}]*\}', menu_items_content)
                            for item_match in item_matches:
                                try:
                                    # 清理項目文本
                                    clean_item = re.sub(r',\s*}', '}', item_match)
                                    clean_item = re.sub(r',\s*]', ']', clean_item)
                                    item_data = json.loads(clean_item)
                                    items.append(item_data)
                                except:
                                    continue
                            
                            if items:
                                return {
                                    'success': True,
                                    'menu_items': items,
                                    'store_info': {'name': 'Unknown Store'},
                                    'processing_notes': 'JSON 解析修復成功'
                                }
                    except Exception as e3:
                        print(f"提取 menu_items 失敗: {e3}")
                    
                    # 策略4: 使用 ast.literal_eval
                    try:
                        return ast.literal_eval(json_text)
                    except:
                        print("ast.literal_eval 也失敗")
                        
                        # 策略5: 嘗試提取部分有效的 JSON
                        try:
                            # 尋找最長的連續 JSON 結構
                            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                            matches = re.findall(json_pattern, json_text)
                            if matches:
                                longest_match = max(matches, key=len)
                                return json.loads(longest_match)
                        except:
                            pass
                        
                        # 如果所有策略都失敗，拋出原始錯誤
                        raise e
        
        # 如果沒有找到 JSON 結構
        raise ValueError("回應中沒有找到有效的 JSON 結構")
        
    except Exception as e:
        print(f"JSON 解析完全失敗: {e}")
        raise e

def normalize_order_text_for_tts(text):
    """
    文本預處理：將訂單文本中的 x1 格式轉換為自然的中文量詞表達
    基於 Azure TTS 的最佳實踐，使用文本預處理而非 SSML 提示詞
    """
    import re
    
    def number_to_chinese(num):
        """將阿拉伯數字轉換為中文數字"""
        chinese_numbers = {
            1: '一', 2: '二', 3: '三', 4: '四', 5: '五',
            6: '六', 7: '七', 8: '八', 9: '九', 10: '十'
        }
        return chinese_numbers.get(num, str(num))
    
    def repl(match):
        item_name = match.group(1).strip()
        quantity = int(match.group(2))
        
        # 飲料類關鍵字（使用「杯」）
        drink_keywords = ['茶', '咖啡', '飲料', '果汁', '奶茶', '汽水', '可樂', '啤酒', '酒', '檸檬', '柳橙', '蘋果']
        
        # 餐點類關鍵字（使用「份」）
        food_keywords = ['麵', '飯', '鍋', '義大利', '牛排', '雞排', '豬排', '魚排', '蝦', '肉', '菜', '湯', '沙拉']
        
        # 判斷是飲料還是餐點
        if any(keyword in item_name for keyword in drink_keywords):
            if quantity == 1:
                return f"{item_name}一杯"
            else:
                chinese_quantity = number_to_chinese(quantity)
                return f"{item_name}{chinese_quantity}杯"
        else:
            if quantity == 1:
                return f"{item_name}一份"
            else:
                chinese_quantity = number_to_chinese(quantity)
                return f"{item_name}{chinese_quantity}份"
    
    # 匹配模式：菜名 + x + 數量（更精確的匹配）
    # 支援 x1, X1, *1, ×1 等多種格式
    # 確保 x 前後有適當的間隔，避免誤匹配
    # 使用更精確的匹配，確保菜名包含中文字符
    pattern = r'([\u4e00-\u9fff]+(?:\s*[\u4e00-\u9fff]+)*)\s*[xX*×]\s*(\d+)\b'
    normalized_text = re.sub(pattern, repl, text)
    
    return normalized_text

def test_text_normalization():
    """
    測試文本預處理功能
    """
    test_cases = [
        "經典奶油夏威夷義大利麵 x1、綠茶 x1",
        "牛肉麵 X1、可樂 *1",
        "雞排飯 ×2、奶茶 x1",
        "義大利麵 x1、柳橙汁 x2",
        "牛排 x1、啤酒 x3"
    ]
    
    print("=== 文本預處理測試 ===")
    for test_case in test_cases:
        normalized = normalize_order_text_for_tts(test_case)
        print(f"原始: {test_case}")
        print(f"預處理後: {normalized}")
        print("---")
    
    return True

def generate_voice_order(order_id, speech_rate=1.0):
    """
    使用 gTTS 生成訂單語音
    """
    print(f"🔧 開始生成語音檔...")
    print(f"📋 輸入參數: order_id={order_id}, speech_rate={speech_rate}")
    
    # 先 cleanup（延長清理時間）
    cleanup_old_voice_files(3600)  # 60分鐘
    
    try:
        from ..models import Order, OrderItem, MenuItem
        
        # 取得訂單資訊
        order = Order.query.get(order_id)
        if not order:
            print(f"❌ 找不到訂單: {order_id}")
            return None
        
        print(f"✅ 找到訂單: order_id={order.order_id}")
        
        # 使用 create_complete_order_confirmation 生成正確的中文語音文字
        print(f"🔧 調用 create_complete_order_confirmation 生成語音文字...")
        confirmation = create_complete_order_confirmation(order_id, 'zh')  # 強制使用中文
        if not confirmation:
            print(f"❌ 無法生成訂單確認內容")
            return None
        
        order_text = confirmation.get('chinese_voice_text', '')
        print(f"🎤 使用中文語音文字: '{order_text}'")
        
        if not order_text:
            print(f"❌ 語音文字為空，使用備用方案")
            return generate_voice_order_fallback(order_id, speech_rate)
        
        # 應用文本預處理（確保沒有遺漏的 x1 格式）
        order_text = normalize_order_text_for_tts(order_text)
        print(f"[TTS] 預處理後的訂單文本: {order_text}")
        
        try:
            # 使用 gTTS 生成語音
            from gtts import gTTS
            
            # 確保目錄存在
            os.makedirs(VOICE_DIR, exist_ok=True)
            
            # 生成檔案路徑
            filename = f"{uuid.uuid4()}.mp3"
            audio_path = os.path.join(VOICE_DIR, filename)
            print(f"[TTS] Will save to {audio_path}")
            
            # 使用 gTTS 生成語音（中文）
            tts = gTTS(text=order_text, lang='zh-tw', slow=False)
            tts.save(audio_path)
            
            # 檢查檔案是否真的生成
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                print(f"[TTS] Success, file exists and size: {os.path.getsize(audio_path)} bytes")
                return audio_path
            else:
                print(f"[TTS] 檔案生成失敗或為空: {audio_path}")
                return generate_voice_order_fallback(order_id, speech_rate)
                
        except Exception as e:
            print(f"gTTS 處理失敗：{e}")
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
            
            # 改進：根據菜名類型選擇合適的量詞
            if any(keyword in original_name for keyword in ['茶', '咖啡', '飲料', '果汁', '奶茶', '汽水', '可樂', '啤酒', '酒']):
                # 飲料類用「杯」
                if quantity == 1:
                    order_text += f" {original_name}一杯，"
                else:
                    order_text += f" {original_name}{quantity}杯，"
            else:
                # 餐點類用「份」
                if quantity == 1:
                    order_text += f" {original_name}一份，"
                else:
                    order_text += f" {original_name}{quantity}份，"
        
        order_text += f"總共{int(temp_order['total_amount'])}元，謝謝。"
        
        # 應用文本預處理（確保沒有遺漏的 x1 格式）
        order_text = normalize_order_text_for_tts(order_text)
        print(f"[TTS] 預處理後的臨時訂單文本: {order_text}")
        
        # 取得語音配置
        speech_config = get_speech_config()
        if not speech_config:
            print("Azure Speech Service 配置失敗，跳過語音生成")
            return None
        
        try:
            # 使用 gTTS 生成語音
            from gtts import gTTS
            
            # 確保目錄存在
            os.makedirs(VOICE_DIR, exist_ok=True)
            
            # 生成檔案路徑
            filename = f"{uuid.uuid4()}.mp3"
            audio_path = os.path.join(VOICE_DIR, filename)
            print(f"[TTS] Will save to {audio_path}")
            
            # 使用 gTTS 生成語音（中文）
            tts = gTTS(text=order_text, lang='zh-tw', slow=False)
            tts.save(audio_path)
            
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                print(f"[TTS] Success, file exists? {os.path.exists(audio_path)}")
                return audio_path
            else:
                print(f"語音生成失敗：檔案不存在或為空")
                return None
                
        except Exception as e:
            print(f"gTTS 處理失敗：{e}")
            return None
            
    except Exception as e:
        print(f"語音生成失敗：{e}")
        return None

def generate_voice_with_custom_rate(order_text, speech_rate=1.0, voice_name="zh-TW-HsiaoChenNeural"):
    """
    使用 gTTS 生成自定義語速的語音檔
    """
    cleanup_old_voice_files()
    try:
        # 應用文本預處理（確保沒有遺漏的 x1 格式）
        order_text = normalize_order_text_for_tts(order_text)
        print(f"[TTS] 自定義語音預處理後的文本: {order_text}")
        
        try:
            # 使用 gTTS 生成語音
            from gtts import gTTS
            
            # 確保目錄存在
            os.makedirs(VOICE_DIR, exist_ok=True)
            
            # 生成檔案路徑
            filename = f"{uuid.uuid4()}.mp3"
            audio_path = os.path.join(VOICE_DIR, filename)
            print(f"[TTS] Will save to {audio_path}")
            
            # 使用 gTTS 生成語音（中文）
            # 注意：gTTS 不支援語速調整，但我們可以通過 slow 參數來控制
            slow = speech_rate < 0.8  # 如果語速小於 0.8，使用慢速
            tts = gTTS(text=order_text, lang='zh-tw', slow=slow)
            tts.save(audio_path)
            
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                print(f"[TTS] Success, file exists? {os.path.exists(audio_path)}")
                return audio_path
            else:
                print(f"語音生成失敗：檔案不存在或為空")
                return None
                
        except Exception as e:
            print(f"gTTS 處理失敗：{e}")
            return None
            
    except Exception as e:
        print(f"語音生成失敗：{e}")
        return None

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
    print(f"🎯 translate_text 開始: text='{text}', target_language='{target_language}'")
    
    try:
        from google import genai
        
        # 設定 Gemini API
        print(f"🎯 設定 Gemini API...")
        genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        
        # 建立翻譯提示詞
        prompt = f"""
        請將以下文字翻譯為 {target_language} 語言：
        
        原文：{text}
        
        請只回傳翻譯結果，不要包含任何其他文字。
        """
        print(f"🎯 翻譯提示詞: {prompt}")
        
        print(f"🎯 調用 Gemini API...")
        response = get_gemini_client().models.generate_content(
            model="models/gemini-2.5-flash-lite",
            contents=[prompt],
            config={
                "thinking_config": genai.types.ThinkingConfig(thinking_budget=512)
            }
        )
        
        result = response.text.strip()
        print(f"🎯 Gemini API 返回結果: '{result}'")
        return result
        
    except Exception as e:
        print(f"❌ 翻譯失敗：{e}")
        print(f"🎯 回傳原文: '{text}'")
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
            'price_large': item.price_big,  # 修正：使用 price_big 而不是 price_large
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
        
        print(f"🔍 查詢菜品翻譯: menu_item_id={menu_item_id}, target_language={target_language}")
        
        translation = MenuTranslation.query.filter_by(
            menu_item_id=menu_item_id,
            lang_code=target_language
        ).first()
        
        if translation:
            print(f"✅ 找到資料庫翻譯: description='{translation.description}'")
        else:
            print(f"❌ 資料庫中沒有找到翻譯")
            
            # 檢查是否有其他語言的翻譯
            all_translations = MenuTranslation.query.filter_by(menu_item_id=menu_item_id).all()
            if all_translations:
                print(f"📋 該菜品有其他語言翻譯: {[(t.lang_code, t.description) for t in all_translations]}")
            else:
                print(f"📋 該菜品完全沒有翻譯資料")
        
        return translation
    except Exception as e:
        print(f"❌ 取得資料庫翻譯失敗：{e}")
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
    print(f"🔧 translate_text_with_fallback 開始: text='{text}', target_language='{target_language}'")
    
    # 嘗試使用AI翻譯
    try:
        print(f"🔧 調用 translate_text 函數...")
        result = translate_text(text, target_language)
        print(f"🔧 translate_text 返回結果: '{result}'")
        return result
    except Exception as e:
        print(f"❌ AI翻譯失敗：{e}")
        print(f"🔧 回傳原文: '{text}'")
        return text  # 如果翻譯失敗，回傳原文

def translate_menu_items_with_db_fallback(menu_items, target_language):
    """翻譯菜單項目，優先使用資料庫翻譯，失敗時使用 AI 翻譯"""
    from ..models import MenuTranslation
    
    translated_items = []
    
    # 語言碼正規化：支援 BCP47 格式
    def normalize_language_code(lang_code):
        """將語言碼正規化為 Google Cloud Translation API 支援的格式"""
        if not lang_code:
            return 'en'
        
        # 支援的語言直接返回
        supported_langs = ['zh', 'en', 'ja', 'ko']
        if lang_code in supported_langs:
            return lang_code
        
        # 處理 BCP47 格式 (如 'fr-FR', 'de-DE')
        if '-' in lang_code:
            return lang_code.split('-')[0]
        
        return lang_code
    
    normalized_lang = normalize_language_code(target_language)
    
    for item in menu_items:
        # 嘗試從資料庫獲取翻譯
        db_translation = None
        try:
            # 先嘗試完整語言碼
            db_translation = MenuTranslation.query.filter_by(
                menu_item_id=item.menu_item_id,
                lang_code=target_language
            ).first()
            
            # 如果沒有找到，嘗試主要語言碼
            if not db_translation and '-' in target_language:
                main_lang = target_language.split('-')[0]
                db_translation = MenuTranslation.query.filter_by(
                    menu_item_id=item.menu_item_id,
                    lang_code=main_lang
                ).first()
                
        except Exception as e:
            print(f"資料庫翻譯查詢失敗: {e}")
        
        # 如果資料庫有翻譯，使用資料庫翻譯
        if db_translation and db_translation.description:
            translated_name = db_translation.description
            translation_source = 'database'
        else:
            # 使用 AI 翻譯
            try:
                # 使用正規化後的語言碼進行翻譯
                translated_name = translate_text_with_fallback(item.item_name, normalized_lang)
                translation_source = 'ai'
            except Exception as e:
                print(f"AI 翻譯失敗: {e}")
                translated_name = item.item_name
                translation_source = 'original'
        
        # 建立雙語格式的菜名
        translated_item = {
            'menu_item_id': item.menu_item_id,
            'original_name': item.item_name,
            'translated_name': translated_name,
            'price_small': item.price_small,
            'price_big': item.price_big,
            'translation_source': translation_source,
            # 新增雙語格式支援
            'name': {
                'original': item.item_name,
                'translated': translated_name
            },
            'show_image': False  # 控制是否顯示圖片框框
        }
        translated_items.append(translated_item)
    
    return translated_items

def translate_store_info_with_db_fallback(store, target_language):
    """翻譯店家資訊，優先使用資料庫翻譯，失敗時使用 AI 翻譯"""
    from ..models import StoreTranslation
    
    print(f"🔍 查詢店家翻譯: store_id={store.store_id}, store_name='{store.store_name}', target_language={target_language}")
    
    # 嘗試從資料庫獲取翻譯
    db_translation = None
    try:
        db_translation = StoreTranslation.query.filter_by(
            store_id=store.store_id,
            language_code=target_language
        ).first()
        
        if db_translation:
            print(f"✅ 找到店家資料庫翻譯: description='{db_translation.description}'")
        else:
            print(f"❌ 資料庫中沒有找到店家翻譯")
            
            # 檢查是否有其他語言的翻譯
            all_translations = StoreTranslation.query.filter_by(store_id=store.store_id).all()
            if all_translations:
                print(f"📋 該店家有其他語言翻譯: {[(t.language_code, t.description) for t in all_translations]}")
            else:
                print(f"📋 該店家完全沒有翻譯資料")
                
    except Exception as e:
        print(f"❌ 店家翻譯查詢失敗: {e}")
    
    # 如果資料庫有翻譯，使用資料庫翻譯
    if db_translation and db_translation.description:
        translated_name = db_translation.description
        translation_source = 'database'
        print(f"✅ 使用資料庫翻譯: '{translated_name}'")
    else:
        # 使用 AI 翻譯
        try:
            print(f"🔧 嘗試AI翻譯店家名稱: '{store.store_name}'")
            translated_name = translate_text_with_fallback(store.store_name, target_language)
            translation_source = 'ai'
            print(f"✅ AI翻譯結果: '{translated_name}'")
        except Exception as e:
            print(f"❌ AI 翻譯失敗: {e}")
            translated_name = store.store_name
            translation_source = 'original'
            print(f"⚠️ 使用原始名稱: '{translated_name}'")
    
    return {
        'store_id': store.store_id,
        'original_name': store.store_name,
        'translated_name': translated_name,
        'translated_reviews': translate_text_with_fallback(store.review_summary, target_language) if store.review_summary else None,
        'translation_source': translation_source
    }

def create_complete_order_confirmation(order_id, user_language='zh', store_name=None):
    """
    建立完整的訂單確認內容（使用新的 DTO 模型，支援雙語摘要）
    
    Args:
        order_id: 訂單ID
        user_language: 使用者語言
        store_name: 前端傳遞的店家名稱（優先使用）
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    
    from ..models import Order, OrderItem, MenuItem, Store, User, db
    from .dto_models import build_order_item_dto, OrderSummaryDTO
    
    print(f"🔧 開始生成訂單確認...")
    print(f"📋 輸入參數: order_id={order_id}, user_language={user_language}, store_name={store_name}")
    
    order = Order.query.get(order_id)
    if not order:
        print(f"❌ 找不到訂單: {order_id}")
        return None
    
    print(f"✅ 找到訂單: order_id={order.order_id}, user_id={order.user_id}, store_id={order.store_id}")
    
    store = Store.query.get(order.store_id)
    if not store:
        print(f"❌ 找不到店家: store_id={order.store_id}")
        return None
    
    print(f"✅ 找到店家: store_id={store.store_id}, store_name='{store.store_name}'")
    
    # 分離中文店名和顯示店名
    # 中文摘要：使用原始中文店名
    chinese_store_name = store.store_name
    
    # 顯示店名：優先使用前端傳遞的店名，否則使用資料庫店名
    if store_name:
        print(f"✅ 使用前端傳遞的店家名稱: '{store_name}'")
        display_store_name = store_name
    else:
        # 檢查店名是否為自動生成格式（店家_ChIJ-xxxxx 或其他預設格式）
        is_auto_generated = (
            (store.store_name and store.store_name.startswith('店家_ChIJ')) or
            (store.store_name and store.store_name in ['非合作店家', 'OCR店家', 'Unknown Store']) or
            (store.store_name and store.store_name.startswith('店家_'))
        )
        
        if is_auto_generated:
            print(f"⚠️ 檢測到自動生成的店名: '{store.store_name}'")
            
            # 嘗試從 OCR 菜單中獲取正確的店名
            print(f"🔍 嘗試從 OCR 菜單中獲取正確的店名...")
            from sqlalchemy import text
            try:
                # 查詢該店家的 OCR 菜單，優先選擇看起來像真實店名的名稱
                result = db.session.execute(text("""
                    SELECT store_name, COUNT(*) as count 
                    FROM ocr_menus 
                    WHERE store_id = :store_id 
                      AND store_name IS NOT NULL 
                      AND store_name != ''
                      AND store_name NOT LIKE '店家_ChIJ%'
                      AND store_name NOT LIKE '%非合作店家%'
                      AND store_name NOT LIKE '%OCR店家%'
                    GROUP BY store_name 
                    ORDER BY count DESC, store_name ASC
                    LIMIT 1
                """), {"store_id": store.store_id})
                
                ocr_store_name = result.fetchone()
                if ocr_store_name and ocr_store_name[0]:
                    print(f"✅ 從 OCR 菜單中找到真實店名: '{ocr_store_name[0]}'")
                    display_store_name = ocr_store_name[0]
                else:
                    # 如果沒有找到真實店名，再查詢所有店名
                    print(f"⚠️ 沒有找到真實店名，查詢所有店名...")
                    result = db.session.execute(text("""
                        SELECT store_name, COUNT(*) as count 
                        FROM ocr_menus 
                        WHERE store_id = :store_id AND store_name IS NOT NULL AND store_name != ''
                        GROUP BY store_name 
                        ORDER BY count DESC, store_name ASC
                        LIMIT 1
                    """), {"store_id": store.store_id})
                    
                    ocr_store_name = result.fetchone()
                    if ocr_store_name and ocr_store_name[0]:
                        print(f"✅ 從 OCR 菜單中找到店名: '{ocr_store_name[0]}'")
                        display_store_name = ocr_store_name[0]
                    else:
                        print(f"⚠️ 沒有找到 OCR 菜單中的店名，使用資料庫名稱: '{store.store_name}'")
                        display_store_name = store.store_name
            except Exception as e:
                print(f"❌ 查詢 OCR 菜單店名時發生錯誤: {e}")
                display_store_name = store.store_name
        else:
            print(f"✅ 使用資料庫名稱: '{store.store_name}'")
            display_store_name = store.store_name
    
    print(f"📋 中文店名: '{chinese_store_name}'")
    print(f"📋 顯示店名: '{display_store_name}'")
    
    user = User.query.get(order.user_id)
    if not user:
        print(f"❌ 找不到使用者: user_id={order.user_id}")
        return None
    
    print(f"✅ 找到使用者: user_id={user.user_id}, preferred_lang={user.preferred_lang}")
    
    # 建立訂單項目 DTO 列表
    order_items_dto = []
    
    print(f"🔍 訂單項目數量: {len(order.items)}")
    print(f"🔍 訂單項目列表: {[item.menu_item_id for item in order.items]}")
    print(f"🔍 訂單項目類型: {type(order.items)}")
    print(f"🔍 訂單項目是否為空: {not order.items}")
    
    if not order.items:
        print(f"⚠️ 警告：訂單沒有項目！")
        return None
    
    for item in order.items:
        print(f"🔍 處理訂單項目: menu_item_id={item.menu_item_id}, quantity={item.quantity_small}")
        
        menu_item = MenuItem.query.get(item.menu_item_id)
        if menu_item:
            print(f"✅ 找到菜單項目: item_name='{menu_item.item_name}'")
            
            # 檢查是否有翻譯資料
            from sqlalchemy import text
            try:
                result = db.session.execute(text("""
                    SELECT description 
                    FROM menu_translations 
                    WHERE menu_item_id = :menu_item_id AND lang_code = :language_code
                """), {
                    "menu_item_id": menu_item.menu_item_id,
                    "language_code": user_language
                })
                
                translation = result.fetchone()
                if translation and translation[0]:
                    chinese_name = translation[0]  # 使用翻譯的中文名稱
                    translated_name = menu_item.item_name  # 使用原始英文名稱
                    print(f"✅ 找到翻譯: '{translated_name}' -> '{chinese_name}'")
                else:
                    # 如果沒有翻譯資料，需要判斷原始名稱是否為中文
                    # contains_cjk 函數已在同檔案中定義
                    print(f"🔍 檢查菜名語言: '{menu_item.item_name}'")
                    is_cjk = contains_cjk(menu_item.item_name)
                    print(f"🔍 是否包含中日韓字元: {is_cjk}")
                    
                    if is_cjk:
                        # 原始名稱是中文
                        chinese_name = menu_item.item_name
                        translated_name = menu_item.item_name
                        print(f"✅ 原始名稱是中文: '{chinese_name}'")
                    else:
                        # 原始名稱是英文，需要翻譯成中文
                        print(f"🔄 開始翻譯英文名稱: '{menu_item.item_name}' -> 中文")
                        try:
                            chinese_name = translate_text_with_fallback(menu_item.item_name, 'zh')
                            translated_name = menu_item.item_name
                            print(f"🔄 翻譯完成: '{translated_name}' -> '{chinese_name}'")
                            
                            # 驗證翻譯結果
                            if contains_cjk(chinese_name):
                                print(f"✅ 翻譯結果包含中日韓字元: '{chinese_name}'")
                            else:
                                print(f"⚠️ 翻譯結果不包含中日韓字元: '{chinese_name}'")
                        except Exception as e:
                            print(f"❌ 翻譯失敗: {e}")
                            chinese_name = menu_item.item_name
                            translated_name = menu_item.item_name
                
                # 使用 DTO 模型處理傳統菜單項目
                item_data = {
                    'menu_item_id': item.menu_item_id,
                    'original_name': chinese_name,  # 使用中文名稱
                    'translated_name': translated_name,  # 使用翻譯名稱
                    'quantity': item.quantity_small,
                    'price': item.subtotal // item.quantity_small if item.quantity_small > 0 else 0,
                    'subtotal': item.subtotal
                }
            except Exception as e:
                print(f"❌ 查詢翻譯資料時發生錯誤: {e}")
                chinese_name = menu_item.item_name
                translated_name = menu_item.item_name
                
                # 使用 DTO 模型處理傳統菜單項目
                item_data = {
                    'menu_item_id': item.menu_item_id,
                    'original_name': chinese_name,  # 使用中文名稱
                    'translated_name': translated_name,  # 使用翻譯名稱
                    'quantity': item.quantity_small,
                    'price': item.subtotal // item.quantity_small if item.quantity_small > 0 else 0,
                    'subtotal': item.subtotal
                }
        else:
            print(f"❌ 找不到菜單項目: menu_item_id={item.menu_item_id}")
            continue
        
        # 建立 DTO 物件
        order_item_dto = build_order_item_dto(item_data, user_language)
        order_items_dto.append(order_item_dto)
        print(f"✅ 建立 DTO 物件: original='{order_item_dto.name.original}', translated='{order_item_dto.name.translated}'")
    
    # 使用 GPT 建議的 deepcopy 方案，建立兩份完全獨立的表示層
    # 準備原始資料（中文店名/菜名）
    order_base = {
        'store_name': chinese_store_name,  # 中文摘要使用原始中文店名
        'items': [
            {
                'name': item.name.original,  # 中文原文
                'quantity': item.quantity,
                'price': item.price
            }
            for item in order_items_dto
        ],
        'total_amount': order.total_amount
    }
    
    # 建立兩份完全獨立的表示層
    chinese_summary, user_language_summary, zh_model = build_presentations(order_base, user_language)
    
    # 生成語音文字（一律使用中文）
    chinese_voice_text = render_tts_text(zh_model)
    
    # 記錄結構化日誌，驗證資料分離
    print(f"📊 資料分離驗證:")
    print(f"   native store_name: '{chinese_store_name}'")
    print(f"   native first item: '{order_base['items'][0]['name'] if order_base['items'] else 'N/A'}'")
    print(f"   display user_lang: '{user_language}'")
    print(f"   display first item: '{order_base['items'][0]['name'] if order_base['items'] else 'N/A'}'")
    
    print(f"🎤 生成中文語音文字: '{chinese_voice_text}'")
    print(f"📝 生成中文摘要:")
    print(f"   {chinese_summary.replace(chr(10), chr(10) + '   ')}")
    print(f"📝 生成使用者語言摘要:")
    print(f"   {user_language_summary.replace(chr(10), chr(10) + '   ')}")
    
    # 如果使用者語言不是中文，需要翻譯店家名稱
    if user_language != 'zh':
        print(f"🔧 開始翻譯店家名稱...")
        # 使用顯示店名進行翻譯（如果已經是英文就不需要再翻譯）
        if display_store_name and display_store_name != chinese_store_name:
            # 使用前端傳遞的店名或 OCR 菜單中的店名
            print(f"📝 使用顯示店名: '{display_store_name}'")
            translated_store_name = display_store_name
        else:
            # 使用資料庫中的店名進行翻譯
            store_translation = translate_store_info_with_db_fallback(store, user_language)
            translated_store_name = store_translation['translated_name']
            print(f"📝 店家翻譯結果: '{store.store_name}' → '{translated_store_name}'")
        
        # 更新使用者語言摘要中的店家名稱（只更新 display 版本）
        user_language_summary = user_language_summary.replace(f"Store: {chinese_store_name}", f"Store: {translated_store_name}")
        
        # 記錄結構化日誌，驗證資料分離
        print(f"📊 結構化日誌:")
        print(f"   store_name_native: '{chinese_store_name}'")
        print(f"   store_name_display: '{translated_store_name}'")
        print(f"   user_language: '{user_language}'")
        print(f"   chinese_summary: '{chinese_summary[:100]}...'")
        print(f"   user_language_summary: '{user_language_summary[:100]}...'")
        
        # 驗證資料分離
        print(f"✅ 資料分離驗證:")
        print(f"   - 中文摘要使用 native 店名: {'✓' if chinese_store_name in chinese_summary else '✗'}")
        print(f"   - 使用者語言摘要使用 display 店名: {'✓' if translated_store_name in user_language_summary else '✗'}")
        print(f"   - 語音使用中文原文: {'✓' if '招牌金湯酸菜' in chinese_voice_text or '白濃雞湯' in chinese_voice_text else '✗'}")
    
    print(f"📝 生成使用者語言摘要:")
    print(f"   {user_language_summary.replace(chr(10), chr(10) + '   ')}")
    
    # 交易式寫入資料庫（一次 commit，避免半套資料）
    try:
        from ..models import OrderSummary
        from sqlalchemy.orm import Session
        
        with db.session.begin():  # 交易自動 begin/commit/rollback
            order_summary = OrderSummary(
                order_id=order_id,
                ocr_menu_id=None,  # 合作店家沒有 OCR 菜單
                chinese_summary=chinese_summary,
                user_language_summary=user_language_summary,
                user_language=user_language,
                total_amount=order.total_amount
            )
            db.session.add(order_summary)
            db.session.flush()  # 獲取 ID
            summary_id = order_summary.summary_id
            
        print(f"✅ 訂單摘要已成功寫入資料庫: summary_id={summary_id}")
        
        # 更新 OrderItem 表的品項名稱欄位
        try:
            from ..models import OrderItem
            
            # 查詢該訂單的所有項目
            order_items = OrderItem.query.filter_by(order_id=order_id).all()
            
            for order_item in order_items:
                # 查詢對應的 menu_item
                menu_item = MenuItem.query.get(order_item.menu_item_id)
                if menu_item:
                    # 設定品項名稱
                    order_item.original_name = menu_item.item_name
                    order_item.translated_name = menu_item.item_name
                    
                    # 如果有翻譯資料，使用翻譯
                    if user_language != 'zh':
                        try:
                            translated_name = translate_text_with_fallback(menu_item.item_name, user_language)
                            if translated_name and translated_name != menu_item.item_name:
                                order_item.translated_name = translated_name
                                print(f"✅ 更新品項翻譯: '{menu_item.item_name}' → '{translated_name}'")
                        except Exception as e:
                            print(f"⚠️ 品項翻譯失敗: {e}")
                    
                    print(f"✅ 更新品項名稱: original='{order_item.original_name}', translated='{order_item.translated_name}'")
            
            # 不需要額外的 commit，因為已經在同一個交易中
            print(f"✅ OrderItem 品項名稱更新完成")
            
        except Exception as e:
            print(f"⚠️ 更新 OrderItem 品項名稱失敗: {e}")
            # 不影響主要流程，繼續執行
        
    except Exception as e:
        print(f"⚠️ 寫入訂單摘要失敗: {e}")
        # 不影響主要流程，繼續執行
    
    result = {
        "chinese_voice_text": chinese_voice_text,
        "chinese": chinese_summary,
        "translated": user_language_summary,
        "chinese_summary": chinese_summary,
        "translated_summary": user_language_summary,
        "user_language": user_language,
        "summary_id": summary_id if 'summary_id' in locals() else None
    }
    
    print(f"🎉 訂單確認生成完成!")
    print(f"📋 返回結果:")
    print(f"   chinese_voice_text: '{result['chinese_voice_text']}'")
    print(f"   chinese: '{result['chinese'][:100]}...'")
    print(f"   translated: '{result['translated'][:100]}...'")
    print(f"   user_language: '{result['user_language']}'")
    
    return result

def send_complete_order_notification(order_id, store_name=None):
    """
    發送完整的訂單確認通知到 LINE
    包含：兩則訂單文字摘要、中文語音檔、語速控制按鈕
    支援OCR菜單訂單的特殊處理
    
    Args:
        order_id: 訂單ID
        store_name: 前端傳遞的店家名稱（可選）
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
    
    # 從資料庫讀取訂單摘要（優先使用資料庫中的摘要）
    from ..models import OrderSummary
    
    order_summary = OrderSummary.query.filter_by(order_id=order_id).first()
    if order_summary:
        print(f"✅ 從資料庫讀取訂單摘要: summary_id={order_summary.summary_id}")
        confirmation = {
            "chinese_voice_text": "老闆，我要點餐，謝謝。",  # 簡化語音文字
            "chinese": order_summary.chinese_summary,
            "translated": order_summary.user_language_summary,
            "chinese_summary": order_summary.chinese_summary,
            "translated_summary": order_summary.user_language_summary,
            "user_language": order_summary.user_language
        }
    else:
        print(f"⚠️ 資料庫中沒有找到訂單摘要，使用即時生成")
        # 建立完整訂單確認內容
        confirmation = create_complete_order_confirmation(order_id, user.preferred_lang, store_name)
        if not confirmation:
            print(f"無法建立訂單確認內容: {order_id}")
            return
    
    try:
        print(f"開始發送訂單通知: {order_id} -> {user.line_user_id}")
        
        # 檢查是否為OCR菜單訂單
        is_ocr_order = any(item.original_name for item in order.items)
        ocr_menu_id = None
        
        if is_ocr_order:
            # 嘗試從訂單項目中提取OCR菜單ID
            for item in order.items:
                if item.original_name:
                    # 檢查是否有相關的OCR菜單記錄
                    from ..models import OCRMenu, OCRMenuItem
                    ocr_menu_item = OCRMenuItem.query.filter_by(
                        item_name=item.original_name
                    ).first()
                    if ocr_menu_item:
                        ocr_menu_id = ocr_menu_item.ocr_menu_id
                        break
        
        # 1. 生成中文語音檔（標準語速）
        voice_result = None
        try:
            voice_result = generate_voice_order(order_id, 1.0)
        except Exception as e:
            print(f"語音生成失敗，跳過語音發送: {e}")
            voice_result = None
        
        # 2. 處理語音結果
        if voice_result and isinstance(voice_result, str) and os.path.exists(voice_result):
            # 成功生成語音檔
            file_size = os.path.getsize(voice_result)
            print(f"語音檔生成成功: {voice_result}, 大小: {file_size} bytes")
            
            if file_size > 0:
                try:
                    # 構建正確的HTTPS URL
                    fname = os.path.basename(voice_result)
                    from ..config import URLConfig
                    audio_url = URLConfig.get_voice_url(fname)
                    
                    line_bot_api = get_line_bot_api()
                    if line_bot_api:
                        line_bot_api.push_message(
                            user.line_user_id,
                            AudioSendMessage(
                                original_content_url=audio_url,
                                duration=30000  # 預設30秒
                            )
                        )
                        print(f"語音檔已發送到 LINE: {audio_url}")
                    else:
                        print("LINE Bot API 不可用，跳過語音發送")
                except Exception as e:
                    print(f"發送語音檔失敗: {e}")
            else:
                print("語音檔案為空，跳過語音發送")
        elif voice_result and isinstance(voice_result, dict):
            # 備用方案：發送文字版本
            if voice_result.get('success'):
                print(f"使用備用語音方案: {voice_result.get('text', '')[:50]}...")
                line_bot_api = get_line_bot_api()
                if line_bot_api:
                    line_bot_api.push_message(
                        user.line_user_id,
                        TextSendMessage(text=f"🎤 點餐語音（文字版）:\n{voice_result.get('text', '')}")
                    )
                    print("備用語音文字已發送到 LINE")
            else:
                print(f"備用語音生成失敗: {voice_result.get('message', '')}")
        else:
            print("語音生成失敗，跳過語音發送")
        
        # 3. 發送中文點餐紀錄
        line_bot_api = get_line_bot_api()
        if line_bot_api:
            # 使用純淨的摘要內容，不包含系統資訊
            chinese_summary = confirmation["chinese_summary"]
            
            line_bot_api.push_message(
                user.line_user_id,
                TextSendMessage(text=chinese_summary)
            )
            print("中文訂單摘要已發送到 LINE")
        
        # 4. 發送使用者語言的點餐紀錄
        if user.preferred_lang != 'zh':
            translated_summary = confirmation.get("translated_summary", confirmation["chinese_summary"])
            
            # 使用純淨的摘要內容，不包含系統資訊
            
            line_bot_api.push_message(
                user.line_user_id,
                TextSendMessage(text=translated_summary)
            )
            print(f"{user.preferred_lang} 語訂單摘要已發送到 LINE")
        
        # 5. 語速控制卡片已移除（節省成本）
        print("語速控制卡片已移除")
        
        # 6. 儲存 OCR 菜單和訂單摘要到資料庫（新增功能）
        try:
            # 檢查是否為 OCR 菜單訂單
            order_items = order.items
            if order_items and any(item.original_name for item in order_items):
                print("🔄 檢測到 OCR 菜單訂單，開始儲存到資料庫...")
                
                # 準備 OCR 項目資料
                ocr_items = []
                for item in order_items:
                    if item.original_name:  # 只處理有原始中文名稱的項目
                        ocr_items.append({
                            'name': {
                                'original': item.original_name,
                                'translated': item.translated_name or item.original_name
                            },
                            'price': item.subtotal // item.quantity_small if item.quantity_small > 0 else 0,
                            'item_name': item.original_name,
                            'translated_name': item.translated_name
                        })
                
                if ocr_items:
                    # 儲存到資料庫
                    save_result = save_ocr_menu_and_summary_to_database(
                        order_id=order_id,
                        ocr_items=ocr_items,
                        chinese_summary=confirmation["chinese_summary"],
                        user_language_summary=confirmation.get("translated_summary", confirmation["chinese_summary"]),
                        user_language=user.preferred_lang,
                        total_amount=order.total_amount,
                        user_id=user.user_id,
                        store_id=order.store_id,  # 使用訂單的 store_id
                        store_name='非合作店家'  # 對於 OCR 訂單，使用預設店名
                    )
                    
                    if save_result['success']:
                        print(f"✅ OCR 菜單和訂單摘要已成功儲存到資料庫")
                        print(f"   OCR 菜單 ID: {save_result['ocr_menu_id']}")
                        print(f"   訂單摘要 ID: {save_result['summary_id']}")
                    else:
                        print(f"⚠️ OCR 菜單和訂單摘要儲存失敗: {save_result['message']}")
                else:
                    print("ℹ️ 沒有 OCR 項目需要儲存")
            else:
                print("ℹ️ 此訂單不是 OCR 菜單訂單，跳過資料庫儲存")
        except Exception as e:
            print(f"⚠️ 儲存 OCR 菜單和訂單摘要時發生錯誤: {e}")
            # 不影響主要流程，繼續執行
        
        # 7. 不立即清理語音檔案，讓靜態路由服務
        # 語音檔案會在60分鐘後由cleanup_old_voice_files自動清理
        print(f"訂單通知發送完成: {order_id}")
        if is_ocr_order:
            print(f"📋 OCR菜單訂單處理完成，OCR菜單ID: {ocr_menu_id}")
            
    except Exception as e:
        print(f"發送訂單確認失敗：{e}")
        import traceback
        traceback.print_exc()

# 語速控制卡片相關函數已移除（節省成本）

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
            from ..config import URLConfig
            audio_url = URLConfig.get_voice_url(fname)
            print(f"[Webhook] Reply with voice URL: {audio_url}")
            
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
        
        # 語速控制卡片已移除（節省成本）
            
    except Exception as e:
        print(f"發送臨時訂單通知失敗：{e}")

# 臨時訂單語速控制卡片相關函數已移除（節省成本）

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
            print(f"備用方案：找不到訂單: {order_id}")
            return None
        
        # 建立自然的中文訂單文字
        items_for_voice = []
        
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                # 改進：根據菜名類型選擇合適的量詞
                item_name = menu_item.item_name
                quantity = item.quantity_small
                
                # 判斷是飲料還是餐點
                if any(keyword in item_name for keyword in ['茶', '咖啡', '飲料', '果汁', '奶茶', '汽水', '可樂', '啤酒', '酒']):
                    # 飲料類用「杯」
                    if quantity == 1:
                        items_for_voice.append(f"{item_name}一杯")
                    else:
                        items_for_voice.append(f"{item_name}{quantity}杯")
                else:
                    # 餐點類用「份」
                    if quantity == 1:
                        items_for_voice.append(f"{item_name}一份")
                    else:
                        items_for_voice.append(f"{item_name}{quantity}份")
        
        # 生成自然的中文語音
        if len(items_for_voice) == 1:
            order_text = f"老闆，我要{items_for_voice[0]}，謝謝。"
        else:
            voice_items = "、".join(items_for_voice[:-1]) + "和" + items_for_voice[-1]
            order_text = f"老闆，我要{voice_items}，謝謝。"
        
        print(f"備用方案：生成文字版本語音: {order_text}")
        
        # 返回文字而非音檔
        return {
            'success': True,
            'text': order_text,
            'message': '語音生成功能暫時不可用，請使用文字版本',
            'is_fallback': True
        }
        
    except Exception as e:
        print(f"備用語音生成失敗：{e}")
        return {
            'success': False,
            'text': '抱歉，語音生成功能暫時不可用',
            'message': '請稍後再試或聯繫客服',
            'is_fallback': True
        }

# =============================================================================
# 新增：非合作店家專用函數
# 功能：使用 Gemini API 生成訂單摘要和語音檔
# =============================================================================

def generate_order_summary_with_gemini(items, user_language='zh'):
    """
    使用 Gemini API 生成訂單摘要
    新設計思路：
    1. 分離中文訂單（原始中文菜名）和使用者語言訂單（翻譯菜名）
    2. 分別生成對應的摘要和語音
    """
    try:
        # 分離中文訂單和使用者語言訂單
        chinese_order_items = []
        user_language_order_items = []
        total_amount = 0
        
        for item in items:
            # 獲取原始中文菜名和翻譯菜名
            original_name = item.get('original_name') or item.get('name', '')
            translated_name = item.get('translated_name') or item.get('name', '')
            quantity = item['quantity']
            price = item.get('price', 0)
            subtotal = item['subtotal']
            total_amount += subtotal
            
            # 中文訂單項目（使用原始中文菜名）
            chinese_order_items.append({
                'name': original_name,
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal
            })
            
            # 使用者語言訂單項目（根據使用者語言選擇菜名）
            if user_language == 'zh':
                # 中文使用者使用原始中文菜名
                user_language_order_items.append({
                    'name': original_name,
                    'quantity': quantity,
                    'price': price,
                    'subtotal': subtotal
                })
            else:
                # 其他語言使用者使用翻譯菜名
                user_language_order_items.append({
                    'name': translated_name,
                    'quantity': quantity,
                    'price': price,
                    'subtotal': subtotal
                })
        
        # 生成中文訂單摘要（使用原始中文菜名）
        chinese_summary = generate_chinese_order_summary(chinese_order_items, total_amount)
        
        # 生成使用者語言訂單摘要
        user_language_summary = generate_user_language_order_summary(user_language_order_items, total_amount, user_language)
        
        # 生成中文語音（使用原始中文菜名）
        chinese_voice = generate_chinese_voice_text(chinese_order_items)
        
        return {
            "chinese_voice": chinese_voice,
            "chinese_summary": chinese_summary,
            "user_summary": user_language_summary
        }
        
    except Exception as e:
        print(f"訂單摘要生成失敗: {e}")
        # 回傳預設格式
        return generate_fallback_order_summary(items, user_language)

def generate_chinese_order_summary(zh_items: List[Dict], total_amount: float) -> str:
    """
    生成中文訂單摘要（使用原始中文菜名）
    """
    try:
        # 快速失敗檢查
        if not zh_items:
            print("❌ zh_items 為空，無法生成中文摘要")
            return "點餐摘要"
        
        # 檢查每個項目是否有有效的菜名
        valid_items = []
        for item in zh_items:
            name = item.get('name', '')
            if not name or not isinstance(name, str):
                print(f"⚠️ 無效的菜名: {name}")
                continue
            valid_items.append(item)
        
        if not valid_items:
            print("❌ 沒有有效的菜名項目")
            return "點餐摘要"
        
        # 生成摘要
        items_text = ""
        for item in valid_items:
            name = item['name']
            quantity = item['quantity']
            items_text += f"{name} x{quantity}、"
        
        # 移除最後一個頓號
        if items_text.endswith('、'):
            items_text = items_text[:-1]
        
        result = items_text.replace('x', ' x ')
        print(f"✅ 中文摘要生成成功: {result}")
        return result
        
    except Exception as e:
        print(f"❌ 中文訂單摘要生成失敗: {e}")
        import traceback
        traceback.print_exc()
        return "點餐摘要"

def generate_user_language_order_summary(user_language_items, total_amount, user_language):
    """
    生成使用者語言訂單摘要（使用翻譯菜名）
    """
    try:
        items_text = ""
        for item in user_language_items:
            name = item['name']
            quantity = item['quantity']
            items_text += f"{name} x{quantity}、"
        
        # 移除最後一個頓號
        if items_text.endswith('、'):
            items_text = items_text[:-1]
        
        # 根據使用者語言格式化
        if user_language == 'zh':
            return items_text.replace('x', ' x ')
        else:
            return f"Order: {items_text.replace('x', ' x ')}"
        
    except Exception as e:
        print(f"使用者語言訂單摘要生成失敗: {e}")
        return "點餐摘要"

def generate_chinese_voice_text(chinese_items):
    """
    生成中文語音文字（使用原始中文菜名）
    """
    try:
        voice_items = []
        for item in chinese_items:
            name = item['name']
            quantity = item['quantity']
            
            # 根據菜名類型選擇量詞
            if any(keyword in name for keyword in ['茶', '咖啡', '飲料', '果汁', '奶茶', '汽水', '可樂', '啤酒', '酒']):
                # 飲料類用「杯」
                if quantity == 1:
                    voice_items.append(f"{name}一杯")
                else:
                    voice_items.append(f"{name}{quantity}杯")
            else:
                # 餐點類用「份」
                if quantity == 1:
                    voice_items.append(f"{name}一份")
                else:
                    voice_items.append(f"{name}{quantity}份")
        
        # 生成自然的中文語音
        if len(voice_items) == 1:
            return f"老闆，我要{voice_items[0]}，謝謝。"
        else:
            voice_text = "、".join(voice_items[:-1]) + "和" + voice_items[-1]
            return f"老闆，我要{voice_text}，謝謝。"
        
    except Exception as e:
        print(f"中文語音文字生成失敗: {e}")
        return "老闆，我要點餐，謝謝。"

def generate_fallback_order_summary(items, user_language):
    """
    生成備用訂單摘要（當主要方法失敗時）
    """
    try:
        chinese_items = []
        user_language_items = []
        
        for item in items:
            original_name = item.get('original_name') or item.get('name', '')
            translated_name = item.get('translated_name') or item.get('name', '')
            quantity = item['quantity']
            
            chinese_items.append({
                'name': original_name,
                'quantity': quantity
            })
            
            user_language_items.append({
                'name': translated_name,
                'quantity': quantity
            })
        
        # 生成備用摘要
        chinese_summary = generate_chinese_order_summary(chinese_items, 0)
        user_language_summary = generate_user_language_order_summary(user_language_items, 0, user_language)
        chinese_voice = generate_chinese_voice_text(chinese_items)
        
        return {
            "chinese_voice": chinese_voice,
            "chinese_summary": chinese_summary,
            "user_summary": user_language_summary
        }
        
    except Exception as e:
        print(f"備用訂單摘要生成失敗: {e}")
        return {
            "chinese_voice": "老闆，我要點餐，謝謝。",
            "chinese_summary": "點餐摘要",
            "user_summary": "點餐摘要"
        }

def generate_chinese_voice_with_azure(order_summary, order_id, speech_rate=1.0):
    """
    使用 gTTS 生成中文語音檔
    輸入：訂單摘要、訂單ID、語速
    輸出：語音檔絕對路徑
    """
    cleanup_old_voice_files()
    try:
        from gtts import gTTS
        import os
        
        # 準備語音文字（處理不同類型的輸入）
        if isinstance(order_summary, dict):
            chinese_text = order_summary.get('chinese_voice', order_summary.get('chinese_summary', '點餐摘要'))
        elif isinstance(order_summary, str):
            chinese_text = order_summary
        else:
            chinese_text = '點餐摘要'
        
        # 應用文本預處理（確保沒有遺漏的 x1 格式）
        chinese_text = normalize_order_text_for_tts(chinese_text)
        print(f"[TTS] gTTS 語音預處理後的文本: {chinese_text}")
        
        # 確保目錄存在
        os.makedirs(VOICE_DIR, exist_ok=True)
        
        # 生成語音檔路徑（存到 /tmp/voices）
        filename = f"{uuid.uuid4()}.mp3"
        voice_path = os.path.join(VOICE_DIR, filename)
        print(f"[TTS] Will save to {voice_path}")
        
        # 使用 gTTS 生成語音（中文）
        tts = gTTS(text=chinese_text, lang='zh-tw', slow=False)
        tts.save(voice_path)
        
        if os.path.exists(voice_path) and os.path.getsize(voice_path) > 0:
            print(f"[TTS] Success, file exists? {os.path.exists(voice_path)}")
            return voice_path
        else:
            print(f"語音生成失敗: 檔案不存在或為空")
            return None
            
    except Exception as e:
        print(f"gTTS 語音生成失敗: {e}")
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
        import re
        
        # 取得 LINE Bot 設定
        line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        line_channel_secret = os.getenv('LINE_CHANNEL_SECRET')
        
        if not line_channel_access_token:
            print("警告: LINE_CHANNEL_ACCESS_TOKEN 環境變數未設定")
            return False
        
        # 驗證 userId 格式
        if not user_id or not isinstance(user_id, str):
            print(f"❌ 無效的 userId: {user_id}")
            return False
        
        # 檢查是否為測試假值或無效格式
        if not re.match(r'^U[0-9a-f]{32}$', user_id):
            print(f"⚠️ 檢測到無效格式的 userId: {user_id}")
            return False
        
        # 準備訊息內容
        chinese_summary = order_data.get('chinese_summary') \
                     or order_data.get('zh_summary', '點餐摘要')
        user_summary = order_data.get('user_summary', '點餐摘要')
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
            from ..config import URLConfig
            audio_url = URLConfig.get_voice_url(fname)
            print(f"[Webhook] Reply with voice URL: {audio_url}")
            
            # 計算音訊檔案的實際長度（毫秒）
            duration_ms = 30000  # 預設30秒
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(voice_url)
                duration_ms = len(audio)  # pydub 回傳的是毫秒
                print(f"[Webhook] 計算的音訊長度: {duration_ms} ms")
            except Exception as e:
                print(f"[Webhook] 無法計算音訊長度，使用預設值: {e}")
            
            messages.append({
                "type": "audio",
                "originalContentUrl": audio_url,
                "duration": duration_ms
            })
        
        # 3. 語速控制卡片已移除（節省成本）
        
        # 發送訊息
        payload = {
            "to": user_id,
            "messages": messages
        }
        
        print(f"📤 準備發送 LINE Bot 訊息:")
        print(f"   userId: {user_id}")
        print(f"   訊息數量: {len(messages)}")
        print(f"   中文摘要: {chinese_summary[:50]}...")
        print(f"   使用者摘要: {user_summary[:50]}...")
        
        response = requests.post(line_api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"✅ 成功發送訂單到 LINE Bot，使用者: {user_id}")
            return True
        else:
            print(f"❌ LINE Bot 發送失敗: {response.status_code} - {response.text}")
            print(f"   請求 payload: {payload}")
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
            from ..config import URLConfig
            audio_url = URLConfig.get_voice_url(fname)
            print(f"[Webhook] Reply with voice URL: {audio_url}")
            
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

def process_order_with_dual_language(order_request: OrderRequest):
    """
    處理雙語訂單（新設計）
    按照GPT建議：從源頭就同時保留 original_name 與 translated_name
    """
    try:
        # 添加調試日誌
        logging.warning("🛰️ payload=%s", json.dumps(order_request.dict(), ensure_ascii=False))
        
        # 分離中文訂單和使用者語言訂單
        zh_items = []  # 中文訂單項目（使用原始中文菜名）
        user_items = []  # 使用者語言訂單項目（根據語言選擇菜名）
        total_amount = 0
        
        for item in order_request.items:
            # 計算小計
            subtotal = item.price * item.quantity
            total_amount += subtotal
            
            # 保護 original 欄位，避免被覆寫
            # 若偵測到 original 是英文但 translated 是中文，交換一次
            if not contains_cjk(item.name.original) and contains_cjk(item.name.translated):
                logging.warning("🔄 檢測到欄位顛倒，交換 original 和 translated")
                item.name.original, item.name.translated = item.name.translated, item.name.original
            
            # 檢查是否為非合作店家的 OCR 菜單項目
            # 對於 OCR 菜單，不傳遞 menu_item_id，讓後端自動創建
            menu_item_id = getattr(item, 'menu_item_id', None)
            
            # 中文訂單項目（使用原始中文菜名）
            zh_items.append({
                'name': item.name.original,
                'quantity': item.quantity,
                'price': item.price,
                'subtotal': subtotal,
                'menu_item_id': menu_item_id  # 可能為 None（OCR 菜單）
            })
            
            # 使用者語言訂單項目（根據語言選擇菜名）
            # 修復語言判斷：使用 startswith('zh') 來識別中文
            if order_request.lang.startswith('zh'):
                # 中文使用者使用原始中文菜名
                user_items.append({
                    'name': item.name.original,
                    'quantity': item.quantity,
                    'price': item.price,
                    'subtotal': subtotal,
                    'menu_item_id': menu_item_id  # 可能為 None（OCR 菜單）
                })
            else:
                # 其他語言使用者使用翻譯菜名
                user_items.append({
                    'name': item.name.translated,
                    'quantity': item.quantity,
                    'price': item.price,
                    'subtotal': subtotal,
                    'menu_item_id': menu_item_id  # 可能為 None（OCR 菜單）
                })
        
        # 添加調試日誌
        logging.warning("🎯 zh_items=%s", zh_items)
        logging.warning("🎯 user_items=%s", user_items)
        logging.warning("🎯 user_lang=%s", order_request.lang)
        
        # 生成中文訂單摘要（使用原始中文菜名）
        zh_summary = generate_chinese_order_summary(zh_items, total_amount)
        
        # 生成使用者語言訂單摘要
        user_summary = generate_user_language_order_summary(user_items, total_amount, order_request.lang)
        
        # 生成中文語音（使用原始中文菜名）
        voice_text = build_chinese_voice_text(zh_items)
        
        return {
            "zh_summary": zh_summary,
            "user_summary": user_summary,
            "voice_text": voice_text,
            "total_amount": total_amount,
            "zh_items": zh_items,  # 直接返回 zh_items 陣列
            "user_items": user_items,  # 直接返回 user_items 陣列
            "items": {
                "zh_items": zh_items,
                "user_items": user_items
            }
        }
        
    except Exception as e:
        print(f"雙語訂單處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_user_language_order_summary(user_items: List[Dict], total_amount: float, user_lang: str) -> str:
    """
    生成使用者語言訂單摘要
    """
    try:
        items_text = ""
        for item in user_items:
            name = item['name']
            quantity = item['quantity']
            items_text += f"{name} x{quantity}、"
        
        # 移除最後一個頓號
        if items_text.endswith('、'):
            items_text = items_text[:-1]
        
        # 根據使用者語言格式化
        if user_lang == 'zh-TW':
            return items_text.replace('x', ' x ')
        else:
            return f"Order: {items_text.replace('x', ' x ')}"
        
    except Exception as e:
        print(f"使用者語言訂單摘要生成失敗: {e}")
        return "點餐摘要"

def build_chinese_voice_text(zh_items: List[Dict]) -> str:
    """
    構建中文語音文字（使用原始中文菜名）
    """
    try:
        voice_items = []
        for item in zh_items:
            name = item['name']  # 這裡已經是中文原文
            quantity = item['quantity']
            
            # 根據菜名類型選擇量詞
            if any(keyword in name for keyword in ['茶', '咖啡', '飲料', '果汁', '奶茶', '汽水', '可樂', '啤酒', '酒']):
                # 飲料類用「杯」
                if quantity == 1:
                    voice_items.append(f"{name}一杯")
                else:
                    voice_items.append(f"{name}{quantity}杯")
            else:
                # 餐點類用「份」
                if quantity == 1:
                    voice_items.append(f"{name}一份")
                else:
                    voice_items.append(f"{name}{quantity}份")
        
        # 生成自然的中文語音
        if len(voice_items) == 1:
            return f"老闆，我要{voice_items[0]}，謝謝。"
        else:
            voice_text = "、".join(voice_items[:-1]) + "和" + voice_items[-1]
            return f"老闆，我要{voice_text}，謝謝。"
        
    except Exception as e:
        print(f"中文語音文字構建失敗: {e}")
        return "老闆，我要點餐，謝謝。"

async def synthesize_azure_tts(text: str) -> tuple[str, int]:
    """
    使用 gTTS 合成語音
    回傳：(語音檔URL, 持續時間毫秒)
    """
    try:
        from gtts import gTTS
        import os
        
        # 確保目錄存在
        os.makedirs(VOICE_DIR, exist_ok=True)
        
        # 生成語音檔路徑
        filename = f"{uuid.uuid4()}.mp3"
        voice_path = os.path.join(VOICE_DIR, filename)
        
        # 使用 gTTS 生成語音（中文）
        tts = gTTS(text=text, lang='zh-tw', slow=False)
        tts.save(voice_path)
        
        if os.path.exists(voice_path) and os.path.getsize(voice_path) > 0:
            # 估算持續時間（gTTS 沒有提供持續時間，我們根據文字長度估算）
            # 假設每個中文字符約 0.5 秒
            estimated_duration_ms = len(text) * 500
            return voice_path, estimated_duration_ms
        else:
            print(f"語音生成失敗: 檔案不存在或為空")
            return None, 0
            
    except Exception as e:
        print(f"gTTS 語音生成失敗: {e}")
        return None, 0

# =============================================================================
# 記憶體優化的語音生成函數
# 功能：在記憶體不足的情況下提供備用語音生成方案
# =============================================================================

def generate_voice_order_memory_optimized(order_id, speech_rate=1.0):
    """
    記憶體優化的語音生成函數
    在記憶體不足時提供備用方案
    """
    try:
        import gc
        import psutil
        
        # 檢查記憶體使用情況
        memory = psutil.virtual_memory()
        if memory.percent > 80:
            print(f"⚠️ 記憶體使用率過高 ({memory.percent}%)，使用備用語音方案")
            return generate_voice_order_fallback(order_id, speech_rate)
        
        # 強制垃圾回收
        gc.collect()
        
        # 嘗試生成語音
        voice_result = generate_voice_order(order_id, speech_rate)
        
        # 再次垃圾回收
        gc.collect()
        
        return voice_result
        
    except Exception as e:
        print(f"記憶體優化語音生成失敗: {e}")
        return generate_voice_order_fallback(order_id, speech_rate)

def generate_voice_order_fallback(order_id, speech_rate=1.0):
    """
    備用語音生成函數（當 Azure TTS 不可用或記憶體不足時）
    """
    try:
        from ..models import Order, OrderItem, MenuItem
        
        # 取得訂單資訊
        order = Order.query.get(order_id)
        if not order:
            return None
        
        # 建立中文訂單文字
        items_for_voice = []
        
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                item_name = menu_item.item_name
                quantity = item.quantity_small
                
                # 判斷是飲料還是餐點
                if any(keyword in item_name for keyword in ['茶', '咖啡', '飲料', '果汁', '奶茶', '汽水', '可樂', '啤酒', '酒']):
                    # 飲料類用「杯」
                    if quantity == 1:
                        items_for_voice.append(f"{item_name}一杯")
                    else:
                        items_for_voice.append(f"{item_name}{quantity}杯")
                else:
                    # 餐點類用「份」
                    if quantity == 1:
                        items_for_voice.append(f"{item_name}一份")
                    else:
                        items_for_voice.append(f"{item_name}{quantity}份")
        
        # 生成自然的中文語音
        if len(items_for_voice) == 1:
            order_text = f"老闆，我要{items_for_voice[0]}，謝謝。"
        else:
            voice_items = "、".join(items_for_voice[:-1]) + "和" + items_for_voice[-1]
            order_text = f"老闆，我要{voice_items}，謝謝。"
        
        # 返回文字而非音檔
        return {
            'success': True,
            'text': order_text,
            'message': '語音生成功能暫時不可用，請使用文字版本'
        }
        
    except Exception as e:
        print(f"備用語音生成失敗：{e}")
        return None

def generate_chinese_summary_optimized(order_id):
    """
    記憶體優化的中文摘要生成
    """
    try:
        from ..models import Order, OrderItem, MenuItem, Store
        
        order = Order.query.get(order_id)
        if not order:
            return "訂單摘要生成失敗"
        
        store = Store.query.get(order.store_id)
        
        # 中文摘要
        chinese_summary = f"店家：{store.store_name if store else '未知店家'}\n"
        chinese_summary += "訂購項目：\n"
        
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                chinese_summary += f"- {menu_item.item_name} x{item.quantity_small}\n"
        
        chinese_summary += f"總金額：${order.total_amount}"
        
        return chinese_summary
        
    except Exception as e:
        print(f"中文摘要生成失敗: {e}")
        return "訂單摘要生成失敗"

# =============================================================================
# 修復語音檔案和中文摘要消失的問題
# =============================================================================

def send_complete_order_notification_optimized(order_id):
    """
    記憶體優化的完整訂單通知發送
    """
    from ..models import Order, User
    from ..webhook.routes import get_line_bot_api
    from linebot.models import TextSendMessage, AudioSendMessage
    
    try:
        order = Order.query.get(order_id)
        if not order:
            print(f"找不到訂單: {order_id}")
            return
        
        user = User.query.get(order.user_id)
        if not user:
            print(f"找不到使用者: {order.user_id}")
            return
        
        print(f"開始發送訂單通知: {order_id} -> {user.line_user_id}")
        
        # 1. 生成中文摘要（優先處理）
        chinese_summary = generate_chinese_summary_optimized(order_id)
        
        # 2. 發送中文摘要
        line_bot_api = get_line_bot_api()
        if line_bot_api and chinese_summary:
            try:
                line_bot_api.push_message(
                    user.line_user_id,
                    TextSendMessage(text=chinese_summary)
                )
                print("✅ 中文訂單摘要已發送到 LINE")
            except Exception as e:
                print(f"❌ 發送中文摘要失敗: {e}")
        
        # 3. 嘗試生成語音檔（記憶體優化版本）
        try:
            voice_result = generate_voice_order_memory_optimized(order_id, 1.0)
            
            if voice_result and isinstance(voice_result, str) and os.path.exists(voice_result):
                # 成功生成語音檔
                print(f"✅ 語音檔生成成功: {voice_result}")
                try:
                    # 構建正確的HTTPS URL
                    fname = os.path.basename(voice_result)
                    from ..config import URLConfig
                    audio_url = URLConfig.get_voice_url(fname)
                    
                    if line_bot_api:
                        line_bot_api.push_message(
                            user.line_user_id,
                            AudioSendMessage(
                                original_content_url=audio_url,
                                duration=30000
                            )
                        )
                        print(f"✅ 語音檔已發送到 LINE: {audio_url}")
                except Exception as e:
                    print(f"❌ 發送語音檔失敗: {e}")
            elif voice_result and isinstance(voice_result, dict):
                # 備用方案：發送文字版本
                print(f"📝 使用備用語音方案: {voice_result.get('text', '')[:50]}...")
                if line_bot_api:
                    line_bot_api.push_message(
                        user.line_user_id,
                        TextSendMessage(text=f"🎤 點餐語音（文字版）:\n{voice_result.get('text', '')}")
                    )
                    print("✅ 備用語音文字已發送到 LINE")
            else:
                print("⚠️ 語音生成失敗，跳過語音發送")
        except Exception as e:
            print(f"❌ 語音生成處理失敗: {e}")
        
        # 6. 儲存 OCR 菜單和訂單摘要到資料庫（新增功能）
        try:
            # 檢查是否為 OCR 菜單訂單
            order_items = order.items
            if order_items and any(item.original_name for item in order_items):
                print("🔄 檢測到 OCR 菜單訂單，開始儲存到資料庫...")
                
                # 準備 OCR 項目資料
                ocr_items = []
                for item in order_items:
                    if item.original_name:  # 只處理有原始中文名稱的項目
                        ocr_items.append({
                            'name': {
                                'original': item.original_name,
                                'translated': item.translated_name or item.original_name
                            },
                            'price': item.subtotal // item.quantity_small if item.quantity_small > 0 else 0,
                            'item_name': item.original_name,
                            'translated_name': item.translated_name
                        })
                
                if ocr_items:
                    # 儲存到資料庫
                    save_result = save_ocr_menu_and_summary_to_database(
                        order_id=order_id,
                        ocr_items=ocr_items,
                        chinese_summary=chinese_summary,
                        user_language_summary=chinese_summary,  # 簡化版本只使用中文摘要
                        user_language=user.preferred_lang,
                        total_amount=order.total_amount,
                        user_id=user.user_id,
                        store_id=order.store_id,  # 使用訂單的 store_id
                        store_name='非合作店家'  # 對於 OCR 訂單，使用預設店名
                    )
                    
                    if save_result['success']:
                        print(f"✅ OCR 菜單和訂單摘要已成功儲存到資料庫")
                        print(f"   OCR 菜單 ID: {save_result['ocr_menu_id']}")
                        print(f"   訂單摘要 ID: {save_result['summary_id']}")
                    else:
                        print(f"⚠️ OCR 菜單和訂單摘要儲存失敗: {save_result['message']}")
                else:
                    print("ℹ️ 沒有 OCR 項目需要儲存")
            else:
                print("ℹ️ 此訂單不是 OCR 菜單訂單，跳過資料庫儲存")
        except Exception as e:
            print(f"⚠️ 儲存 OCR 菜單和訂單摘要時發生錯誤: {e}")
            # 不影響主要流程，繼續執行
        
        print(f"✅ 訂單通知發送完成: {order_id}")
            
    except Exception as e:
        print(f"❌ 發送訂單確認失敗：{e}")
        import traceback
        traceback.print_exc()

def build_order_message(zh_summary: str, user_summary: str, total: int, audio_url: str | None) -> list:
    """
    建立訂單訊息（修正版本）
    解決問題：
    1. 使用者語言摘要在第一行
    2. 金額去除小數點
    3. 語音檔上傳問題處理
    """
    import logging
    
    # 1. 確保兩種摘要都不是 None
    if not zh_summary or zh_summary.strip() == "":
        logging.error("zh_summary missing or empty")
        raise ValueError("zh_summary missing")
    
    if not user_summary or user_summary.strip() == "":
        # 允許 fallback 但要寫入日誌
        logging.warning("User summary missing, fallback to zh_summary")
        user_summary = zh_summary
    
    # 2. 構建文字訊息（修正排序：使用者語言摘要在前）
    text_parts = []
    
    # 使用者語言摘要在第一行（直接顯示，不加標籤）
    if user_summary and user_summary != zh_summary:
        text_parts.append(user_summary)
    
    # 中文摘要（給店家聽）
    text_parts.append(f"中文摘要（給店家聽）：{zh_summary}")
    
    # 總金額（修正：去除小數點）
    total_twd = int(round(total))
    text_parts.append(f"總金額：{total_twd} 元")
    
    text = "\n\n".join(text_parts)
    messages = [{"type": "text", "text": text}]
    
    # 3. audio_url 必須是 https 且可存取，否則不要附加
    if audio_url and audio_url.startswith("https://"):
        messages.append({
            "type": "audio",
            "originalContentUrl": audio_url,
            "duration": estimate_duration_ms(audio_url)
        })
        logging.info(f"✅ 附加音訊訊息: {audio_url}")
    else:
        logging.warning(f"Skip audio, invalid url={audio_url}")
    
    return messages

def detect_lang(text: str) -> str:
    """檢測語言並返回對應標籤"""
    if contains_cjk(text):
        return "中文"
    elif any(c.isalpha() for c in text) and not contains_cjk(text):
        return "English"
    else:
        return "摘要"

def get_language_label(text: str) -> str:
    """根據文字內容返回對應的語言標籤"""
    if contains_cjk(text):
        return "中文"
    elif any(c.isalpha() for c in text) and not contains_cjk(text):
        # 檢查是否包含日文字符
        if any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' for char in text):
            return "日本語"
        # 檢查是否包含韓文字符
        elif any('\uAC00' <= char <= '\uD7AF' for char in text):
            return "한국어"
        else:
            return "English"
    else:
        return "摘要"

def estimate_duration_ms(audio_url: str) -> int:
    """估算音訊時長（毫秒）"""
    # 根據檔案大小和內容估算，這裡使用預設值
    return 30000  # 30秒

def send_order_to_line_bot_fixed(user_id, order_data):
    """
    修復版本的 LINE Bot 發送函數
    解決摘要被預設字串覆蓋和 TTS 檔案沒有公開網址的問題
    """
    try:
        import os
        import requests
        import re
        import logging
        
        # 取得 LINE Bot 設定
        line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        line_channel_secret = os.getenv('LINE_CHANNEL_SECRET')
        
        if not line_channel_access_token:
            logging.error("LINE_CHANNEL_ACCESS_TOKEN 環境變數未設定")
            return False
        
        # 驗證 userId 格式
        if not user_id or not isinstance(user_id, str):
            logging.error(f"❌ 無效的 userId: {user_id}")
            return False
        
        # 檢查是否為測試假值或無效格式
        if not re.match(r'^U[0-9a-f]{32}$', user_id):
            logging.warning(f"⚠️ 檢測到無效格式的 userId: {user_id}")
            return False
        
        # 準備訊息內容（嚴謹檢查）
        zh_summary = order_data.get('chinese_summary') or order_data.get('zh_summary')
        user_summary = order_data.get('user_summary')
        voice_url = order_data.get('voice_url')
        total_amount = order_data.get('total_amount', 0)
        
        # 除錯：檢查變數值
        logging.debug(f"zh_summary={zh_summary}")
        logging.debug(f"user_summary={user_summary}")
        logging.debug(f"voice_url={voice_url}")
        
        # 使用新的訊息構建函數
        try:
            messages = build_order_message(zh_summary, user_summary, total_amount, voice_url)
        except ValueError as e:
            logging.error(f"訊息構建失敗: {e}")
            return False
        
        # 準備 LINE Bot API 請求
        line_api_url = "https://api.line.me/v2/bot/message/push"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {line_channel_access_token}'
        }
        
        # 發送訊息
        payload = {
            "to": user_id,
            "messages": messages
        }
        
        logging.info(f"📤 準備發送 LINE Bot 訊息:")
        logging.info(f"   userId: {user_id}")
        logging.info(f"   訊息數量: {len(messages)}")
        logging.info(f"   中文摘要: {zh_summary[:50] if zh_summary else 'None'}...")
        logging.info(f"   使用者摘要: {user_summary[:50] if user_summary else 'None'}...")
        
        response = requests.post(line_api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            logging.info(f"✅ 成功發送訂單到 LINE Bot，使用者: {user_id}")
            return True
        else:
            logging.error(f"❌ LINE Bot 發送失敗: {response.status_code} - {response.text}")
            logging.error(f"   請求 payload: {payload}")
            return False
            
    except Exception as e:
        logging.error(f"❌ LINE Bot 整合失敗: {e}")
        return False

def generate_and_upload_audio_to_gcs(text: str, order_id: str) -> str | None:
    """
    生成語音檔並上傳到 GCS，返回公開 HTTPS URL
    修正版本：解決 GCS bucket 不存在和權限問題
    """
    try:
        import os
        import tempfile
        from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig, ResultReason
        
        # 1. 生成語音檔
        speech_config = get_speech_config()
        if not speech_config:
            logging.error("Azure Speech 配置不可用")
            return None
        
        # 設定語音參數
        speech_config.speech_synthesis_voice_name = "zh-TW-HsiaoChenNeural"
        speech_config.speech_synthesis_speaking_rate = 1.0
        
        # 準備語音文字
        voice_text = normalize_order_text_for_tts(text)
        logging.info(f"[TTS] 生成語音文字: {voice_text}")
        
        # 生成臨時語音檔
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # 設定音訊輸出
        audio_config = AudioConfig(filename=temp_path)
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        
        # 生成語音
        result = synthesizer.speak_text_async(voice_text).get()
        
        if result.reason == ResultReason.SynthesizingAudioCompleted:
            logging.info(f"✅ 語音生成成功: {temp_path}")
        else:
            logging.error(f"❌ 語音生成失敗: {result.reason}")
            os.unlink(temp_path)
            return None
        
        # 2. 上傳到 GCS（修正版本）
        try:
            from google.cloud import storage
            
            # 初始化 GCS 客戶端
            storage_client = storage.Client()
            
            # 取得 bucket（修正 bucket 名稱）
            bucket_name = os.getenv('GCS_BUCKET_NAME', 'ordering-helper-voice-files')
            
            # 檢查 bucket 是否存在，如果不存在則創建
            bucket = storage_client.bucket(bucket_name)
            if not bucket.exists():
                logging.warning(f"❌ GCS bucket '{bucket_name}' 不存在，嘗試創建...")
                try:
                    # 創建 bucket（需要適當的權限）
                    bucket = storage_client.create_bucket(bucket_name, location='asia-east1')
                    logging.info(f"✅ 成功創建 GCS bucket: {bucket_name}")
                except Exception as create_error:
                    logging.error(f"❌ 無法創建 GCS bucket: {create_error}")
                    # 清理臨時檔案
                    os.unlink(temp_path)
                    return None
            else:
                logging.info(f"✅ GCS bucket '{bucket_name}' 已存在")
            
            # 生成 blob 名稱
            blob_name = f"voices/{order_id}_{os.path.basename(temp_path)}"
            blob = bucket.blob(blob_name)
            
            # 上傳檔案
            blob.upload_from_filename(temp_path)
            
            # 設定公開讀取權限
            blob.make_public()
            
            # 取得公開 URL
            public_url = blob.public_url
            
            # 清理臨時檔案
            os.unlink(temp_path)
            
            logging.info(f"✅ 語音檔已上傳到 GCS: {public_url}")
            return public_url
            
        except ImportError:
            logging.warning("Google Cloud Storage 不可用，跳過 GCS 上傳")
            # 清理臨時檔案
            os.unlink(temp_path)
            return None
        except Exception as e:
            logging.error(f"❌ GCS 上傳失敗: {e}")
            # 清理臨時檔案
            os.unlink(temp_path)
            return None
            
    except Exception as e:
        logging.error(f"❌ 語音生成和上傳失敗: {e}")
        return None

def process_order_with_enhanced_tts(order_request: OrderRequest):
    """
    增強版本的訂單處理函數
    包含完整的 TTS 和 GCS 上傳流程
    """
    try:
        # 添加調試日誌
        logging.warning("🛰️ payload=%s", json.dumps(order_request.dict(), ensure_ascii=False))
        
        # 分離中文訂單和使用者語言訂單
        zh_items = []  # 中文訂單項目（使用原始中文菜名）
        user_items = []  # 使用者語言訂單項目（根據語言選擇菜名）
        total_amount = 0
        
        for item in order_request.items:
            # 計算小計
            subtotal = item.price * item.quantity
            total_amount += subtotal
            
            # 保護 original 欄位，避免被覆寫
            if not contains_cjk(item.name.original) and contains_cjk(item.name.translated):
                logging.warning("🔄 檢測到欄位顛倒，交換 original 和 translated")
                item.name.original, item.name.translated = item.name.translated, item.name.original
            
            # 檢查是否為非合作店家的 OCR 菜單項目
            menu_item_id = getattr(item, 'menu_item_id', None)
            
            # 中文訂單項目（使用原始中文菜名）
            zh_items.append({
                'name': item.name.original,
                'quantity': item.quantity,
                'price': item.price,
                'subtotal': subtotal,
                'menu_item_id': menu_item_id
            })
            
            # 使用者語言訂單項目（根據語言選擇菜名）
            if order_request.lang.startswith('zh'):
                user_items.append({
                    'name': item.name.original,
                    'quantity': item.quantity,
                    'price': item.price,
                    'subtotal': subtotal,
                    'menu_item_id': menu_item_id
                })
            else:
                user_items.append({
                    'name': item.name.translated,
                    'quantity': item.quantity,
                    'price': item.price,
                    'subtotal': subtotal,
                    'menu_item_id': menu_item_id
                })
        
        # 添加調試日誌
        logging.warning("🎯 zh_items=%s", zh_items)
        logging.warning("🎯 user_items=%s", user_items)
        logging.warning("🎯 user_lang=%s", order_request.lang)
        
        # 生成中文訂單摘要（使用原始中文菜名）
        zh_summary = generate_chinese_order_summary(zh_items, total_amount)
        
        # 生成使用者語言訂單摘要
        user_summary = generate_user_language_order_summary(user_items, total_amount, order_request.lang)
        
        # 生成中文語音文字
        voice_text = build_chinese_voice_text(zh_items)
        
        # 生成語音檔並上傳到 GCS
        audio_url = None
        if voice_text:
            order_id = f"order_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            audio_url = generate_and_upload_audio_to_gcs(voice_text, order_id)
        
        return {
            "zh_summary": zh_summary,
            "user_summary": user_summary,
            "voice_text": voice_text,
            "audio_url": audio_url,  # 新增：GCS 公開 URL
            "total_amount": total_amount,
            "zh_items": zh_items,
            "user_items": user_items,
            "items": {
                "zh_items": zh_items,
                "user_items": user_items
            }
        }
        
    except Exception as e:
        logging.error(f"雙語訂單處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_voice_order_enhanced(order_id, speech_rate=1.0, emotion_style="cheerful", use_hd_voice=True):
    """
    使用 gTTS 生成增強版訂單語音
    
    Args:
        order_id: 訂單 ID
        speech_rate: 語速倍率 (0.5-2.0)
        emotion_style: 情感風格 ("cheerful", "friendly", "excited", "calm", "sad")
        use_hd_voice: 是否使用 HD 聲音（gTTS 不支援，保留參數相容性）
    """
    # 先 cleanup（延長清理時間）
    cleanup_old_voice_files(3600)  # 60分鐘
    
    try:
        from ..models import Order, OrderItem, MenuItem
        
        # 取得訂單資訊
        order = Order.query.get(order_id)
        if not order:
            print(f"找不到訂單: {order_id}")
            return None
        
        # 建立自然的中文訂單文字
        items_for_voice = []
        
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                # 改進：根據菜名類型選擇合適的量詞
                item_name = menu_item.item_name
                quantity = item.quantity_small
                
                # 判斷是飲料還是餐點
                if any(keyword in item_name for keyword in ['茶', '咖啡', '飲料', '果汁', '奶茶', '汽水', '可樂', '啤酒', '酒']):
                    # 飲料類用「杯」
                    if quantity == 1:
                        items_for_voice.append(f"{item_name}一杯")
                    else:
                        items_for_voice.append(f"{item_name}{quantity}杯")
                else:
                    # 餐點類用「份」
                    if quantity == 1:
                        items_for_voice.append(f"{item_name}一份")
                    else:
                        items_for_voice.append(f"{item_name}{quantity}份")
        
        # 生成自然的中文語音
        if len(items_for_voice) == 1:
            order_text = f"老闆，我要{items_for_voice[0]}，謝謝。"
        else:
            voice_items = "、".join(items_for_voice[:-1]) + "和" + items_for_voice[-1]
            order_text = f"老闆，我要{voice_items}，謝謝。"
        
        # 應用文本預處理（確保沒有遺漏的 x1 格式）
        order_text = normalize_order_text_for_tts(order_text)
        print(f"[TTS Enhanced] 預處理後的訂單文本: {order_text}")
        
        try:
            # 使用 gTTS 生成語音
            from gtts import gTTS
            
            # 確保目錄存在
            os.makedirs(VOICE_DIR, exist_ok=True)
            
            # 生成檔案路徑
            filename = f"{uuid.uuid4()}.mp3"
            audio_path = os.path.join(VOICE_DIR, filename)
            print(f"[TTS Enhanced] Will save to {audio_path}")
            
            # 使用 gTTS 生成語音（中文）
            # 注意：gTTS 不支援語速調整和情感風格，但我們可以通過 slow 參數來控制
            slow = speech_rate < 0.8  # 如果語速小於 0.8，使用慢速
            tts = gTTS(text=order_text, lang='zh-tw', slow=slow)
            tts.save(audio_path)
            
            # 檢查檔案是否真的生成
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                print(f"[TTS Enhanced] Success, file exists and size: {os.path.getsize(audio_path)} bytes")
                return audio_path
            else:
                print(f"[TTS Enhanced] 檔案生成失敗或為空: {audio_path}")
                return generate_voice_order_fallback(order_id, speech_rate)
                
        except Exception as e:
            print(f"gTTS Enhanced 處理失敗：{e}")
            return generate_voice_order_fallback(order_id, speech_rate)
            
    except Exception as e:
        print(f"語音生成失敗：{e}")
        return generate_voice_order_fallback(order_id, speech_rate)

def generate_voice_with_custom_rate_enhanced(text, speech_rate=1.0, emotion_style="cheerful", use_hd_voice=True):
    """
    使用 gTTS 生成增強版自訂語音檔
    
    Args:
        text: 要轉換的文字
        speech_rate: 語速倍率 (0.5-2.0)
        emotion_style: 情感風格 ("cheerful", "friendly", "excited", "calm", "sad")（gTTS 不支援，保留參數相容性）
        use_hd_voice: 是否使用 HD 聲音（gTTS 不支援，保留參數相容性）
    """
    try:
        # 確保目錄存在
        os.makedirs(VOICE_DIR, exist_ok=True)
        
        # 生成檔案名
        filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(VOICE_DIR, filename)
        print(f"[TTS Enhanced] Will save to {audio_path}")
        
        # 使用 gTTS 生成語音（中文）
        # 注意：gTTS 不支援語速調整和情感風格，但我們可以通過 slow 參數來控制
        slow = speech_rate < 0.8  # 如果語速小於 0.8，使用慢速
        tts = gTTS(text=text, lang='zh-tw', slow=slow)
        tts.save(audio_path)
        
        # 檢查檔案是否真的生成
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            print(f"[TTS Enhanced] Success, file exists and size: {os.path.getsize(audio_path)} bytes")
            return audio_path
        else:
            print(f"[TTS Enhanced] 檔案生成失敗或為空: {audio_path}")
            return None
            
    except Exception as e:
        print(f"gTTS Enhanced 處理失敗：{e}")
        return None

def create_order_summary(order_id, user_language='zh'):
    """
    建立訂單摘要（雙語）- 使用 Gemini API 強制翻譯英文菜名
    """
    from ..models import Order, OrderItem, MenuItem, Store
    
    order = Order.query.get(order_id)
    if not order:
        return None
    
    store = Store.query.get(order.store_id)
    
    # 中文摘要
    chinese_summary = f"店家：{store.store_name if store else '未知店家'}\n"
    chinese_summary += "訂購項目：\n"
    
    for item in order.items:
        menu_item = MenuItem.query.get(item.menu_item_id)
        if menu_item:
            # 檢查菜名是否為英文，如果是則強制翻譯為中文
            item_name = menu_item.item_name
            if not contains_cjk(item_name):
                try:
                    # 使用 Gemini API 強制翻譯為中文
                    translated_name = translate_text(item_name, 'zh')
                    if translated_name and contains_cjk(translated_name):
                        item_name = translated_name
                        print(f"🔄 Gemini 翻譯菜名：'{menu_item.item_name}' → '{item_name}'")
                    else:
                        print(f"⚠️ Gemini 翻譯失敗或結果非中文：'{menu_item.item_name}'")
                except Exception as e:
                    print(f"❌ Gemini 翻譯錯誤：{e}")
            
            chinese_summary += f"- {item_name} x{item.quantity_small}\n"
    
    chinese_summary += f"總金額：${order.total_amount}"
    
    # 翻譯摘要（使用者語言）
    if user_language != 'zh':
        translated_summary = f"Store: {store.store_name if store else 'Unknown Store'}\n"
        translated_summary += "Items:\n"
        
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                translated_summary += f"- {menu_item.item_name} x{item.quantity_small} (${item.subtotal})\n"
        
        translated_summary += f"Total: ${order.total_amount}"
    else:
        translated_summary = chinese_summary
    
    return {
        "chinese": chinese_summary,
        "translated": translated_summary
    }

def save_ocr_menu_and_summary_to_database(order_id, ocr_items, chinese_summary, user_language_summary, user_language, total_amount, user_id, store_id=None, store_name=None, existing_ocr_menu_id=None):
    """
    將 OCR 菜單和訂單摘要儲存到 Cloud MySQL 資料庫
    
    Args:
        order_id: 訂單 ID
        ocr_items: OCR 菜單項目列表
        chinese_summary: 中文訂單摘要
        user_language_summary: 使用者語言訂單摘要
        user_language: 使用者語言代碼
        total_amount: 訂單總金額
        user_id: 使用者 ID
        store_id: 店家 ID（可選）
        store_name: 店家名稱（可選）
        existing_ocr_menu_id: 現有的OCR菜單ID（可選）
    
    Returns:
        dict: 包含 ocr_menu_id 和 summary_id 的結果
    """
    import logging
    import datetime
    logging.basicConfig(level=logging.INFO)
    
    try:
        from ..models import db, OCRMenu, OCRMenuItem, OrderSummary
        from sqlalchemy import text
        
        print(f"🔄 開始儲存 OCR 菜單和訂單摘要到資料庫...")
        print(f"📋 輸入參數:")
        print(f"   order_id: {order_id} (型態: {type(order_id)})")
        print(f"   user_id: {user_id} (型態: {type(user_id)})")
        print(f"   total_amount: {total_amount} (型態: {type(total_amount)})")
        print(f"   user_language: {user_language} (型態: {type(user_language)})")
        print(f"   existing_ocr_menu_id: {existing_ocr_menu_id} (型態: {type(existing_ocr_menu_id)})")
        print(f"   store_name: {store_name} (型態: {type(store_name)})")
        print(f"   ocr_items 數量: {len(ocr_items) if ocr_items else 0}")
        
        # 1. 使用現有的OCR菜單ID或創建新的OCR菜單記錄
        if existing_ocr_menu_id:
            # 使用現有的OCR菜單ID
            ocr_menu_id = existing_ocr_menu_id
            print(f"✅ 使用現有的 OCR 菜單 ID: {ocr_menu_id}")
        else:
            # 創建新的OCR菜單記錄
            print(f"📝 準備創建新的 OCR 菜單記錄...")
            
            # 記錄OCR菜單插入SQL
            ocr_menu_sql = """
            INSERT INTO ocr_menus (user_id, store_id, store_name, upload_time)
            VALUES (:user_id, :store_id, :store_name, :upload_time)
            """
            ocr_menu_params = {
                "user_id": user_id,
                "store_id": store_id,  # 新增 store_id
                "store_name": store_name or '非合作店家',
                "upload_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logging.info(f"Executing OCR Menu SQL: {ocr_menu_sql}")
            logging.info(f"With parameters: {ocr_menu_params}")
            
            # 使用原生SQL執行
            result = db.session.execute(text(ocr_menu_sql), ocr_menu_params)
            db.session.commit()
            
            # 獲取插入的ID
            ocr_menu_id_result = db.session.execute(text("SELECT LAST_INSERT_ID() as id"))
            ocr_menu_id = ocr_menu_id_result.fetchone()[0]
            
            print(f"✅ 已建立新的 OCR 菜單記錄: {ocr_menu_id}")
        
        # 2. 儲存 OCR 菜單項目（只有在沒有現有OCR菜單ID時才創建）
        if not existing_ocr_menu_id and ocr_items:
            print(f"📝 準備創建 {len(ocr_items)} 個 OCR 菜單項目...")
            
            for i, item in enumerate(ocr_items):
                ocr_menu_item_sql = """
                INSERT INTO ocr_menu_items (ocr_menu_id, item_name, price_big, price_small, translated_desc)
                VALUES (:ocr_menu_id, :item_name, :price_big, :price_small, :translated_desc)
                """
                
                item_name = item.get('name', {}).get('original', item.get('item_name', '未知項目'))
                price = int(item.get('price', 0))
                translated_desc = item.get('name', {}).get('translated', item.get('translated_name', ''))
                ocr_menu_item_params = {
                    "ocr_menu_id": ocr_menu_id,
                    "item_name": item_name,
                    "price_big": price,
                    "price_small": price,
                    "translated_desc": translated_desc
                }
                
                logging.info(f"Executing OCR Menu Item {i+1} SQL: {ocr_menu_item_sql}")
                logging.info(f"With parameters: {ocr_menu_item_params}")
                
                db.session.execute(text(ocr_menu_item_sql), ocr_menu_item_params)
            
                # 獲取插入的 OCR 菜單項目 ID
                ocr_menu_item_id_result = db.session.execute(text("SELECT LAST_INSERT_ID() as id"))
                ocr_menu_item_id = ocr_menu_item_id_result.fetchone()[0]
                
                # 儲存翻譯到 ocr_menu_translations 表
                if translated_desc and translated_desc != item_name:
                    ocr_menu_translation_sql = """
                    INSERT INTO ocr_menu_translations (menu_item_id, lang_code, description)
                    VALUES (:menu_item_id, :lang_code, :description)
                    """
                    
                    ocr_menu_translation_params = {
                        "menu_item_id": ocr_menu_item_id,
                        "lang_code": user_language,
                        "description": translated_desc
                    }
                    
                    logging.info(f"Executing OCR Menu Translation SQL: {ocr_menu_translation_sql}")
                    logging.info(f"With parameters: {ocr_menu_translation_params}")
                    
                    db.session.execute(text(ocr_menu_translation_sql), ocr_menu_translation_params)
            
            db.session.commit()
            print(f"✅ 已儲存 {len(ocr_items)} 個 OCR 菜單項目和翻譯")
        
        # 3. 建立訂單摘要記錄
        print(f"📝 準備創建訂單摘要記錄...")
        
        order_summary_sql = """
        INSERT INTO order_summaries (order_id, ocr_menu_id, chinese_summary, user_language_summary, user_language, total_amount, created_at)
        VALUES (:order_id, :ocr_menu_id, :chinese_summary, :user_language_summary, :user_language, :total_amount, :created_at)
        """
        order_summary_params = {
            "order_id": order_id,
            "ocr_menu_id": ocr_menu_id,
            "chinese_summary": chinese_summary,
            "user_language_summary": user_language_summary,
            "user_language": user_language,
            "total_amount": total_amount,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logging.info(f"Executing Order Summary SQL: {order_summary_sql}")
        logging.info(f"With parameters: {order_summary_params}")
        
        # 使用原生SQL執行
        result = db.session.execute(text(order_summary_sql), order_summary_params)
        db.session.commit()
        
        # 獲取插入的ID
        summary_id_result = db.session.execute(text("SELECT LAST_INSERT_ID() as id"))
        summary_id = summary_id_result.fetchone()[0]
        
        print(f"✅ 已建立訂單摘要記錄: {summary_id}")
        
        # 4. 提交所有變更
        print(f"🎉 成功儲存 OCR 菜單和訂單摘要到資料庫")
        print(f"   OCR 菜單 ID: {ocr_menu_id}")
        print(f"   訂單摘要 ID: {summary_id}")
        
        return {
            'success': True,
            'ocr_menu_id': ocr_menu_id,
            'summary_id': summary_id,
            'message': 'OCR 菜單和訂單摘要已成功儲存到資料庫'
        }
        
    except Exception as e:
        print(f"❌ 儲存 OCR 菜單和訂單摘要到資料庫失敗: {e}")
        print(f"錯誤類型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        try:
            db.session.rollback()
            print("✅ 資料庫回滾成功")
        except Exception as rollback_error:
            print(f"❌ 資料庫回滾失敗: {rollback_error}")
        
        return {
            'success': False,
            'error': str(e),
            'message': '儲存 OCR 菜單和訂單摘要到資料庫失敗'
        }

def get_ocr_menu_translation_from_db(ocr_menu_item_id, target_language):
    """
    從資料庫取得 OCR 菜單翻譯
    """
    try:
        from ..models import OCRMenuTranslation
        
        print(f"🔍 查詢 OCR 菜單翻譯: ocr_menu_item_id={ocr_menu_item_id}, target_language={target_language}")
        
        translation = OCRMenuTranslation.query.filter_by(
            ocr_menu_item_id=ocr_menu_item_id,
            lang_code=target_language
        ).first()
        
        if translation:
            print(f"✅ 找到 OCR 菜單翻譯: translated_name='{translation.translated_name}'")
        else:
            print(f"❌ 資料庫中沒有找到 OCR 菜單翻譯")
            
            # 檢查是否有其他語言的翻譯
            all_translations = OCRMenuTranslation.query.filter_by(ocr_menu_item_id=ocr_menu_item_id).all()
            if all_translations:
                print(f"📋 該 OCR 菜單項目有其他語言翻譯: {[(t.lang_code, t.translated_name) for t in all_translations]}")
            else:
                print(f"📋 該 OCR 菜單項目完全沒有翻譯資料")
        
        return translation
    except Exception as e:
        print(f"❌ 取得 OCR 菜單翻譯失敗：{e}")
        return None

def translate_ocr_menu_items_with_db_fallback(ocr_menu_items, target_language):
    """
    翻譯 OCR 菜單項目，優先使用資料庫翻譯，如果沒有則使用 AI 翻譯
    """
    try:
        from ..models import OCRMenuTranslation
        
        print(f"🔄 開始翻譯 OCR 菜單項目，目標語言: {target_language}")
        
        # 正規化語言碼
        normalized_lang = normalize_language_code(target_language)
        print(f"📋 正規化語言碼: {target_language} -> {normalized_lang}")
        
        translated_items = []
        
        for item in ocr_menu_items:
            # 嘗試從資料庫獲取翻譯
            db_translation = None
            try:
                # 先嘗試完整語言碼
                db_translation = OCRMenuTranslation.query.filter_by(
                    ocr_menu_item_id=item.ocr_menu_item_id,
                    lang_code=target_language
                ).first()
                
                # 如果沒有找到，嘗試主要語言碼
                if not db_translation and '-' in target_language:
                    main_lang = target_language.split('-')[0]
                    db_translation = OCRMenuTranslation.query.filter_by(
                        ocr_menu_item_id=item.ocr_menu_item_id,
                        lang_code=main_lang
                    ).first()
                    
            except Exception as e:
                print(f"資料庫翻譯查詢失敗: {e}")
            
            # 如果資料庫有翻譯，使用資料庫翻譯
            if db_translation and db_translation.translated_name:
                translated_name = db_translation.translated_name
                translation_source = 'database'
            else:
                # 使用 AI 翻譯
                try:
                    # 使用正規化後的語言碼進行翻譯
                    translated_name = translate_text_with_fallback(item.item_name, normalized_lang)
                    translation_source = 'ai'
                except Exception as e:
                    print(f"AI 翻譯失敗: {e}")
                    translated_name = item.item_name
                    translation_source = 'original'
            
            # 建立翻譯後的項目
            translated_item = {
                'ocr_menu_item_id': item.ocr_menu_item_id,
                'original_name': item.item_name,
                'translated_name': translated_name,
                'price_small': item.price_small,
                'price_big': item.price_big,
                'translation_source': translation_source
            }
            
            translated_items.append(translated_item)
            print(f"✅ 項目 {item.ocr_menu_item_id}: '{item.item_name}' -> '{translated_name}' ({translation_source})")
        
        print(f"🎉 OCR 菜單翻譯完成，共處理 {len(translated_items)} 個項目")
        return translated_items
        
    except Exception as e:
        print(f"❌ OCR 菜單翻譯失敗: {e}")
        # 返回原始項目
        return [{
            'ocr_menu_item_id': item.ocr_menu_item_id,
            'original_name': item.item_name,
            'translated_name': item.item_name,
            'price_small': item.price_small,
            'price_big': item.price_big,
            'translation_source': 'error'
        } for item in ocr_menu_items]

def build_presentations(order_base, user_lang):
    """
    建立兩份完全獨立的表示層模型
    
    Args:
        order_base: 原始資料（中文店名/菜名），只做讀取不改寫
        user_lang: 使用者語言，例如 'en'
    
    Returns:
        tuple: (zh_summary, user_summary, zh_model)
    """
    print(f"🔧 開始建立兩份獨立表示層...")
    print(f"   使用者語言: {user_lang}")
    
    # 1. 建立兩份完全獨立的模型（深拷貝，避免共用物件）
    zh_model = deepcopy(order_base)               # 中文版：保持中文店名、中文菜名
    localized = deepcopy(order_base)              # 在地化版：全部翻成 user_lang
    
    print(f"   ✅ 深拷貝完成，兩份模型完全獨立")
    
    # 2. 翻譯店名（只翻譯 localized 版本）
    if user_lang != 'zh':
        print(f"   🔄 翻譯店名: '{localized['store_name']}' -> ", end="")
        localized['store_name'] = translate_text_with_fallback(localized['store_name'], user_lang)
        print(f"'{localized['store_name']}'")
    
    # 3. 翻譯每個菜名（只翻譯 localized 版本）
    if user_lang != 'zh':
        print(f"   🔄 翻譯菜名...")
        for item in localized['items']:
            original_name = item['name']
            item['name'] = translate_text_with_fallback(original_name, user_lang)
            print(f"      '{original_name}' -> '{item['name']}'")
    
    # 4. 組兩份摘要字串
    zh_summary = render_summary(zh_model, lang='zh')
    user_summary = render_summary(localized, lang=user_lang)
    
    print(f"   ✅ 兩份摘要生成完成")
    print(f"   📝 中文摘要長度: {len(zh_summary)} 字元")
    print(f"   📝 使用者語言摘要長度: {len(user_summary)} 字元")
    
    return zh_summary, user_summary, zh_model

def render_summary(model, lang='zh'):
    """
    渲染摘要文字
    
    Args:
        model: 資料模型（zh_model 或 localized）
        lang: 語言代碼
    
    Returns:
        str: 摘要文字
    """
    store_name = model['store_name']
    items = model['items']
    total_amount = model['total_amount']
    
    if lang == 'zh':
        # 中文摘要格式
        summary = f"店家：{store_name}\n"
        summary += "訂購項目：\n"
        for item in items:
            summary += f"- {item['name']} x{item['quantity']}\n"
        summary += f"總金額：${total_amount}"
    else:
        # 其他語言摘要格式
        summary = f"Store: {store_name}\n"
        summary += "Items:\n"
        for item in items:
            summary += f"- {item['name']} x{item['quantity']} (${item['price']})\n"
        summary += f"Total: ${total_amount}"
    
    return summary

def render_tts_text(zh_model):
    """
    渲染語音文字（一律使用中文）
    
    Args:
        zh_model: 中文模型
    
    Returns:
        str: 語音文字
    """
    items = zh_model['items']
    
    voice_items = []
    for item in items:
        name = item['name']
        quantity = item['quantity']
        
        # 根據菜名類型選擇量詞
        if any(keyword in name for keyword in ['茶', '咖啡', '飲料', '果汁', '奶茶', '汽水', '可樂', '啤酒', '酒']):
            # 飲料類用「杯」
            if quantity == 1:
                voice_items.append(f"{name}一杯")
            else:
                voice_items.append(f"{name}{quantity}杯")
        else:
            # 餐點類用「份」
            if quantity == 1:
                voice_items.append(f"{name}一份")
            else:
                voice_items.append(f"{name}{quantity}份")
    
    # 生成自然的中文語音
    if len(voice_items) == 1:
        return f"老闆，我要{voice_items[0]}，謝謝。"
    else:
        voice_text = "、".join(voice_items[:-1]) + "和" + voice_items[-1]
        return f"老闆，我要{voice_text}，謝謝。"
