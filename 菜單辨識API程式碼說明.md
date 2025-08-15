# 菜單辨識 API 程式碼說明

## 📋 目錄
- [功能概述](#功能概述)
- [程式碼架構](#程式碼架構)
- [核心檔案位置](#核心檔案位置)
- [API 端點說明](#api-端點說明)
- [核心辨識流程](#核心辨識流程)
- [資料庫模型](#資料庫模型)
- [錯誤處理](#錯誤處理)
- [使用範例](#使用範例)

## 🎯 功能概述

菜單辨識 API 是一個基於 Google Gemini 2.5 Flash API 的智能菜單解析系統，能夠：

- **OCR 辨識**: 自動辨識菜單圖片中的文字內容
- **結構化處理**: 將辨識結果整理成結構化資料
- **多語言翻譯**: 支援多語言菜名翻譯
- **資料庫儲存**: 自動儲存辨識結果供後續使用
- **訂單整合**: 與訂單系統無縫整合

## 🏗️ 程式碼架構

```
app/
├── api/
│   ├── routes.py          # 主要 API 端點
│   ├── helpers.py         # 核心辨識函數
│   └── store_resolver.py  # 店家 ID 解析
├── prompts.py             # 提示詞模板
├── models.py              # 資料庫模型
└── config/
    └── settings.py        # 配置設定
```

## 📁 核心檔案位置

### 1. 主要 API 端點
**檔案**: `app/api/routes.py`
**函數**: `process_menu_ocr()` (第 398 行)

```python
@api_bp.route('/menu/process-ocr', methods=['POST', 'OPTIONS'])
def process_menu_ocr():
    """
    處理菜單圖片上傳和 OCR 辨識
    支援檔案上傳、參數驗證、店家 ID 解析、AI 辨識、資料庫儲存
    """
```

### 2. 核心辨識函數
**檔案**: `app/api/helpers.py`
**函數**: `process_menu_with_gemini()` (第 277 行)

```python
def process_menu_with_gemini(image_path, target_language='en'):
    """
    使用 Gemini 2.5 Flash API 處理菜單圖片
    1. OCR 辨識菜單文字
    2. 結構化為菜單項目
    3. 翻譯為目標語言
    """
```

### 3. 提示詞模板
**檔案**: `app/prompts.py`
**類別**: `PromptEngineer`
**方法**: `_get_menu_ocr_prompt()` (第 30 行)

```python
class PromptEngineer:
    """提示詞工程師類別"""
    
    def __init__(self):
        self.prompts = {
            'menu_ocr': self._get_menu_ocr_prompt(),
            'voice_processing': self._get_voice_processing_prompt(),
            'order_summary': self._get_order_summary_prompt()
        }
    
    def _get_menu_ocr_prompt(self) -> str:
        """菜單 OCR 辨識提示詞"""
        return """
你是一個專業的菜單辨識專家。請仔細分析這張菜單圖片，並執行以下任務：

## 任務要求：
1. **OCR 辨識**：準確辨識所有菜單項目、價格和描述
2. **結構化處理**：將辨識結果整理成結構化資料
3. **語言翻譯**：將菜名翻譯為目標語言
4. **價格標準化**：統一價格格式（數字）

## 輸出格式要求：
請嚴格按照以下 JSON 格式輸出，不要包含任何其他文字：

```json
{
  "success": true,
  "menu_items": [
    {
      "original_name": "原始菜名（中文）",
      "translated_name": "翻譯後菜名",
      "price": 數字價格,
      "description": "菜單描述（如果有）",
      "category": "分類（如：主食、飲料、小菜等）"
    }
  ],
  "store_info": {
    "name": "店家名稱",
    "address": "地址（如果有）",
    "phone": "電話（如果有）"
  },
  "processing_notes": "處理備註"
}
```

## 重要注意事項：
- 價格必須是數字格式
- 如果無法辨識某個項目，請在 processing_notes 中說明
- 確保 JSON 格式完全正確，可以直接解析
- 如果圖片模糊或無法辨識，請將 success 設為 false
"""
```

### 4. 其他相關端點
**檔案**: `app/api/routes.py`
- `upload_menu_image()` (第 2021 行) - 舊版上傳端點
- `create_order()` (第 632 行) - 處理 OCR 菜單訂單

## 🔌 API 端點說明

### 主要端點: `POST /api/menu/process-ocr`

#### 請求參數
| 參數名稱 | 類型 | 必填 | 說明 |
|---------|------|------|------|
| `image` | File | ✅ | 菜單圖片檔案 |
| `store_id` | String | ✅ | 店家識別碼 |
| `user_id` | String | ❌ | 使用者 ID (LINE 用戶 ID) |
| `lang` | String | ❌ | 目標語言 (預設: 'en') |
| `simple_mode` | String | ❌ | 簡化模式 ('true'/'false') |

#### 支援的檔案格式
```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
```

#### 檔案大小限制
- 最大檔案大小: 10MB
- 圖片壓縮: 自動壓縮至最大邊長 1024px

## 🔄 核心辨識流程

### 步驟 1: 檔案上傳與驗證
```python
# 檔案格式檢查
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 支援的檔案格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 檔案上傳處理
if 'image' not in request.files:
    return jsonify({'error': '沒有上傳檔案'}), 400

file = request.files['image']
if file.filename == '':
    return jsonify({'error': '沒有選擇檔案'}), 400

if not allowed_file(file.filename):
    return jsonify({'error': '不支援的檔案格式'}), 400
```

### 步驟 2: 檔案儲存與壓縮
```python
def save_uploaded_file(file, folder='uploads'):
    """儲存上傳的檔案並進行圖片壓縮"""
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
```

### 步驟 3: Gemini API 客戶端初始化
```python
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
```

### 步驟 4: 核心辨識函數
```python
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
            
            # 使用 Gemini 2.5 Flash Lite 模型 + JSON Mode
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash-lite",
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
```

### 步驟 5: 主要 API 端點實作
```python
@api_bp.route('/menu/process-ocr', methods=['POST', 'OPTIONS'])
def process_menu_ocr():
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    # 檢查是否有檔案
    if 'image' not in request.files:
        response = jsonify({'error': '沒有上傳檔案'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    
    file = request.files['image']
    
    # 檢查檔案名稱
    if file.filename == '':
        response = jsonify({'error': '沒有選擇檔案'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    
    # 檢查檔案格式
    if not allowed_file(file.filename):
        response = jsonify({'error': '不支援的檔案格式'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    
    # 取得參數
    raw_store_id = request.form.get('store_id')  # 可能是整數、數字字串或 Google Place ID
    user_id = request.form.get('user_id')  # 移除 type=int，因為前端傳遞的是字串格式的 LINE 用戶 ID
    target_lang = request.form.get('lang', 'en')
    
    # 新增：簡化模式參數
    simple_mode = request.form.get('simple_mode', 'false').lower() == 'true'
    
    if not raw_store_id:
        response = jsonify({"error": "需要提供店家ID"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    
    # 使用 store resolver 解析店家 ID
    try:
        from .store_resolver import resolve_store_id
        store_db_id = resolve_store_id(raw_store_id)
        print(f"✅ 店家ID解析成功: {raw_store_id} -> {store_db_id}")
    except Exception as e:
        print(f"❌ 店家ID解析失敗: {e}")
        response = jsonify({
            "error": "店家ID格式錯誤",
            "details": str(e),
            "received_store_id": raw_store_id
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    
    try:
        # 儲存上傳的檔案
        filepath = save_uploaded_file(file)
        
        # 先處理圖片獲取店家資訊
        print("開始使用 Gemini API 處理圖片...")
        result = process_menu_with_gemini(filepath, target_lang)
        
        # 檢查處理結果
        if result and result.get('success', False):
            # 處理 user_id - 使用 LINE 用戶 ID 或創建臨時使用者
            if user_id:
                # 檢查是否已存在該 LINE 用戶
                existing_user = User.query.filter_by(line_user_id=user_id).first()
                if existing_user:
                    actual_user_id = existing_user.user_id
                    print(f"✅ 使用現有使用者，ID: {actual_user_id} (LINE ID: {user_id})")
                else:
                    # 創建新使用者
                    new_user = User(
                        line_user_id=user_id,
                        preferred_lang=target_lang or 'zh'
                    )
                    db.session.add(new_user)
                    db.session.flush()  # 獲取 user_id
                    actual_user_id = new_user.user_id
                    print(f"✅ 創建新使用者，ID: {actual_user_id} (LINE ID: {user_id})")
            else:
                # 沒有提供 user_id，創建臨時使用者
                temp_user = User(
                    line_user_id=f"temp_guest_{int(time.time())}",
                    preferred_lang=target_lang or 'zh'
                )
                db.session.add(temp_user)
                db.session.flush()  # 獲取 user_id
                actual_user_id = temp_user.user_id
                print(f"✅ 創建臨時使用者，ID: {actual_user_id}")
            
            # 建立 OCR 菜單記錄（使用解析後的整數 store_id）
            ocr_menu = OCRMenu(
                user_id=actual_user_id,
                store_id=store_db_id,  # 使用解析後的 store_db_id
                store_name=result.get('store_info', {}).get('name', '臨時店家')
            )
            db.session.add(ocr_menu)
            db.session.flush()  # 獲取 ocr_menu_id
            
            # 儲存菜單項目到資料庫
            menu_items = result.get('menu_items', [])
            dynamic_menu = []
            
            for i, item in enumerate(menu_items):
                # 儲存到 ocr_menu_items 表
                ocr_menu_item = OCRMenuItem(
                    ocr_menu_id=ocr_menu.ocr_menu_id,
                    item_name=str(item.get('original_name', '') or ''),
                    price_small=item.get('price', 0),
                    price_big=item.get('price', 0),  # 使用相同價格
                    translated_desc=str(item.get('translated_name', '') or '')
                )
                db.session.add(ocr_menu_item)
                
                # 根據模式生成不同的菜單資料
                if simple_mode:
                    # 簡化模式：只包含必要欄位
                    dynamic_menu.append({
                        'id': f"ocr_{ocr_menu.ocr_menu_id}_{i}",
                        'name': str(item.get('original_name', '') or ''),
                        'translated_name': str(item.get('translated_name', '') or ''),
                        'price': item.get('price', 0),
                        'description': str(item.get('description', '') or ''),
                        'category': str(item.get('category', '') or '其他')
                    })
                else:
                    # 完整模式：包含所有前端相容欄位
                    dynamic_menu.append({
                        'temp_id': f"temp_{ocr_menu.ocr_menu_id}_{i}",
                        'id': f"temp_{ocr_menu.ocr_menu_id}_{i}",
                        'original_name': str(item.get('original_name', '') or ''),
                        'translated_name': str(item.get('translated_name', '') or ''),
                        'en_name': str(item.get('translated_name', '') or ''),
                        'price': item.get('price', 0),
                        'price_small': item.get('price', 0),
                        'price_large': item.get('price', 0),
                        'description': str(item.get('description', '') or ''),
                        'category': str(item.get('category', '') or '其他'),
                        'image_url': '/static/images/default-dish.png',
                        'imageUrl': '/static/images/default-dish.png',
                        'show_image': False,  # 控制是否顯示圖片框框
                        'inventory': 999,
                        'available': True,
                        'processing_id': ocr_menu.ocr_menu_id
                    })
            
            # 提交資料庫變更
            db.session.commit()
            
            # 根據模式準備回應資料
            if simple_mode:
                # 簡化模式回應
                response_data = {
                    "success": True,
                    "menu_items": dynamic_menu,
                    "store_name": result.get('store_info', {}).get('name', '臨時店家'),
                    "target_language": target_lang,
                    "processing_notes": result.get('processing_notes', ''),
                    "ocr_menu_id": ocr_menu.ocr_menu_id,
                    "saved_to_database": True
                }
            else:
                # 完整模式回應
                response_data = {
                    "message": "菜單處理成功",
                    "processing_id": ocr_menu.ocr_menu_id,
                    "store_info": result.get('store_info', {}),
                    "menu_items": dynamic_menu,
                    "total_items": len(dynamic_menu),
                    "target_language": target_lang,
                    "processing_notes": result.get('processing_notes', ''),
                    "ocr_menu_id": ocr_menu.ocr_menu_id,
                    "saved_to_database": True
                }
            
            response = jsonify(response_data)
            response.headers.add('Access-Control-Allow-Origin', '*')
            
            # 加入 API 回應的除錯 log
            mode_text = "簡化模式" if simple_mode else "完整模式"
            print(f"🎉 API 成功回應 201 Created ({mode_text})")
            print(f"📊 回應統計:")
            print(f"  - OCR菜單ID: {ocr_menu.ocr_menu_id}")
            print(f"  - 菜單項目數: {len(dynamic_menu)}")
            print(f"  - 目標語言: {target_lang}")
            print(f"  - 回應模式: {mode_text}")
            print(f"  - 店家資訊: {result.get('store_info', {})}")
            print(f"  - 處理備註: {result.get('processing_notes', '')}")
            print(f"  - 已儲存到資料庫: True")
            
            return response, 201
        else:
            # 檢查是否是 JSON 解析錯誤或其他可恢復的錯誤
            error_message = result.get('error', '菜單處理失敗，請重新拍攝清晰的菜單照片')
            processing_notes = result.get('processing_notes', '')
            
            # 如果是 JSON 解析錯誤或其他可恢復的錯誤，返回 422
            if 'JSON 解析失敗' in error_message or 'extra_forbidden' in error_message:
                print(f"❌ API 返回 422 錯誤")
                print(f"🔍 錯誤詳情:")
                print(f"  - 錯誤訊息: {error_message}")
                print(f"  - 處理備註: {processing_notes}")
                print(f"  - 處理ID: 無")
                
                response = jsonify({
                    "error": error_message,
                    "processing_notes": processing_notes
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 422
            else:
                # 其他錯誤返回 500
                print(f"❌ API 返回 500 錯誤")
                print(f"🔍 錯誤詳情:")
                print(f"  - 錯誤訊息: {error_message}")
                print(f"  - 處理備註: {processing_notes}")
                print(f"  - 處理ID: 無")
                
                response = jsonify({
                    "error": error_message,
                    "processing_notes": processing_notes
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 500
                
    except Exception as e:
        print(f"❌ 處理過程中發生錯誤: {e}")
        response = jsonify({
            "error": "處理過程中發生錯誤",
            "details": str(e) if current_app.debug else '請稍後再試'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
```

## 🗄️ 資料庫模型

### OCRMenu (OCR 菜單主檔)
```python
class OCRMenu(db.Model):
    """OCR 菜單主檔（符合同事的資料庫結構）"""
    __tablename__ = 'ocr_menus'
    
    ocr_menu_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=True)  # 新增 store_id 欄位
    store_name = db.Column(db.String(100))  # 非合作店家名稱
    upload_time = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    
    # 關聯到菜單項目
    items = db.relationship('OCRMenuItem', backref='ocr_menu', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<OCRMenu {self.ocr_menu_id}>'
```

### OCRMenuItem (OCR 菜單項目)
```python
class OCRMenuItem(db.Model):
    """OCR 菜單品項（符合同事的資料庫結構）"""
    __tablename__ = 'ocr_menu_items'
    
    ocr_menu_item_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    ocr_menu_id = db.Column(db.BigInteger, db.ForeignKey('ocr_menus.ocr_menu_id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)  # 品項名稱
    price_big = db.Column(db.Integer)  # 大份量價格
    price_small = db.Column(db.Integer, nullable=False)  # 小份量價格
    translated_desc = db.Column(db.Text)  # 翻譯後介紹
    
    def __repr__(self):
        return f'<OCRMenuItem {self.ocr_menu_item_id}>'
```

### OCRMenuTranslation (OCR 菜單翻譯)
```python
class OCRMenuTranslation(db.Model):
    """OCR 菜單翻譯（儲存翻譯後的 OCR 菜單）"""
    __tablename__ = 'ocr_menu_translations'
    
    ocr_menu_translation_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    ocr_menu_item_id = db.Column(db.BigInteger, db.ForeignKey('ocr_menu_items.ocr_menu_item_id'), nullable=False)
    lang_code = db.Column(db.String(10), db.ForeignKey('languages.line_lang_code'), nullable=False)
    translated_name = db.Column(db.String(100), nullable=False)  # 翻譯後的菜名
    translated_description = db.Column(db.Text)  # 翻譯後的描述
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    
    # 關聯到 OCR 菜單項目
    ocr_menu_item = db.relationship('OCRMenuItem', backref='translations', lazy=True)
    
    def __repr__(self):
        return f'<OCRMenuTranslation {self.ocr_menu_translation_id}>'
```

### OrderSummary (訂單摘要)
```python
class OrderSummary(db.Model):
    """訂單摘要儲存模型"""
    __tablename__ = 'order_summaries'
    
    summary_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(db.BigInteger, db.ForeignKey('orders.order_id', ondelete='CASCADE'), nullable=False)
    ocr_menu_id = db.Column(db.BigInteger, db.ForeignKey('ocr_menus.ocr_menu_id', ondelete='CASCADE'), nullable=True)  # 可為空，因為合作店家可能沒有 OCR 菜單
    chinese_summary = db.Column(db.Text, nullable=False)  # 中文訂單摘要
    user_language_summary = db.Column(db.Text, nullable=False)  # 使用者語言訂單摘要
    user_language = db.Column(db.String(10), nullable=False)  # 使用者語言代碼
    total_amount = db.Column(db.Integer, nullable=False)  # 訂單總金額
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    
    # 關聯到訂單和 OCR 菜單
    order = db.relationship('Order', backref='summaries', lazy=True)
    ocr_menu = db.relationship('OCRMenu', backref='order_summaries', lazy=True)
    
    def __repr__(self):
        return f'<OrderSummary {self.summary_id}>'
```

## ⚠️ 錯誤處理

### 檔案相關錯誤 (HTTP 400)
```python
# 沒有上傳檔案
if 'image' not in request.files:
    response = jsonify({'error': '沒有上傳檔案'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 400

# 檔案名稱檢查
if file.filename == '':
    response = jsonify({'error': '沒有選擇檔案'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 400

# 檔案格式不支援
if not allowed_file(file.filename):
    response = jsonify({'error': '不支援的檔案格式'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 400

# 檔案太大檢查
file_size = os.path.getsize(image_path)
max_size = 10 * 1024 * 1024  # 10MB
if file_size > max_size:
    return {
        'success': False,
        'error': f'檔案太大 ({file_size / 1024 / 1024:.1f}MB)，請上傳較小的圖片'
    }
```

### 店家 ID 錯誤 (HTTP 400)
```python
# 店家 ID 參數檢查
if not raw_store_id:
    response = jsonify({"error": "需要提供店家ID"})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 400

# 店家 ID 解析錯誤
try:
    from .store_resolver import resolve_store_id
    store_db_id = resolve_store_id(raw_store_id)
    print(f"✅ 店家ID解析成功: {raw_store_id} -> {store_db_id}")
except Exception as e:
    print(f"❌ 店家ID解析失敗: {e}")
    response = jsonify({
        "error": "店家ID格式錯誤",
        "details": str(e),
        "received_store_id": raw_store_id
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 400
```

### Gemini API 錯誤處理
```python
# Gemini 客戶端初始化失敗
gemini_client = get_gemini_client()
if not gemini_client:
    return {
        'success': False,
        'error': 'Gemini API 客戶端初始化失敗',
        'processing_notes': '請檢查 GEMINI_API_KEY 環境變數'
    }

# Gemini API 回應為空
if not response or not hasattr(response, 'text'):
    return {
        'success': False,
        'error': 'Gemini API 回應為空',
        'processing_notes': '請檢查 API 金鑰和網路連線'
    }

# JSON 解析錯誤
try:
    result = json.loads(json_text)
except json.JSONDecodeError as e:
    print(f"JSON 解析失敗: {e}")
    return {
        'success': False,
        'error': 'JSON 解析失敗',
        'processing_notes': f'Gemini 回應格式錯誤: {str(e)}'
    }

# 回應格式驗證
if not isinstance(result, dict):
    return {
        'success': False,
        'error': 'Gemini 回應格式錯誤',
        'processing_notes': '回應不是有效的 JSON 物件'
    }

# 菜單項目檢查
if not result.get('menu_items') or len(result['menu_items']) == 0:
    result['success'] = False
    result['error'] = '無法從圖片中辨識菜單項目'
    result['processing_notes'] = '圖片可能模糊或不是菜單'
    return result
```

### 處理失敗 (HTTP 422/500)
```python
# 檢查是否是 JSON 解析錯誤或其他可恢復的錯誤
error_message = result.get('error', '菜單處理失敗，請重新拍攝清晰的菜單照片')
processing_notes = result.get('processing_notes', '')

# 如果是 JSON 解析錯誤或其他可恢復的錯誤，返回 422
if 'JSON 解析失敗' in error_message or 'extra_forbidden' in error_message:
    print(f"❌ API 返回 422 錯誤")
    print(f"🔍 錯誤詳情:")
    print(f"  - 錯誤訊息: {error_message}")
    print(f"  - 處理備註: {processing_notes}")
    print(f"  - 處理ID: 無")
    
    response = jsonify({
        "error": error_message,
        "processing_notes": processing_notes
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 422
else:
    # 其他錯誤返回 500
    print(f"❌ API 返回 500 錯誤")
    print(f"🔍 錯誤詳情:")
    print(f"  - 錯誤訊息: {error_message}")
    print(f"  - 處理備註: {processing_notes}")
    print(f"  - 處理ID: 無")
    
    response = jsonify({
        "error": error_message,
        "processing_notes": processing_notes
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 500
```

### 超時處理
```python
def timeout_handler(signum, frame):
    raise TimeoutError("Gemini API 處理超時")

# 設定 240 秒超時（與 Cloud Run 300秒保持安全邊距）
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(240)

try:
    # Gemini API 呼叫
    response = gemini_client.models.generate_content(...)
    
    # 取消超時
    signal.alarm(0)
    
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
```

### 一般異常處理
```python
try:
    # 主要處理邏輯
    filepath = save_uploaded_file(file)
    result = process_menu_with_gemini(filepath, target_lang)
    # ... 其他處理
except Exception as e:
    print(f"❌ 處理過程中發生錯誤: {e}")
    response = jsonify({
        "error": "處理過程中發生錯誤",
        "details": str(e) if current_app.debug else '請稍後再試'
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 500
```

### CORS 處理
```python
def handle_cors_preflight():
    """處理 CORS 預檢請求"""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

# 在每個端點中加入 CORS 處理
if request.method == 'OPTIONS':
    return handle_cors_preflight()

# 在回應中加入 CORS 標頭
response = jsonify(response_data)
response.headers.add('Access-Control-Allow-Origin', '*')
```

## 💻 使用範例

### JavaScript/TypeScript
```javascript
// 建立 FormData
const formData = new FormData();
formData.append('image', imageFile);
formData.append('store_id', '123');
formData.append('user_id', 'U1234567890');
formData.append('lang', 'en');
formData.append('simple_mode', 'false');

// 發送請求
const response = await fetch('https://your-cloud-run', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result);
```

### Python
```python
import requests

# 準備檔案和參數
files = {'image': open('menu.jpg', 'rb')}
data = {
    'store_id': '123',
    'user_id': 'U1234567890',
    'lang': 'en',
    'simple_mode': 'false'
}

# 發送請求
response = requests.post(
    'https://your-cloud-run',
    files=files,
    data=data
)

result = response.json()
print(result)
```

### cURL
```bash
curl -X POST \
  https://your-cloud-run\
  -F "image=@menu.jpg" \
  -F "store_id=123" \
  -F "user_id=U1234567890" \
  -F "lang=en" \
  -F "simple_mode=false"
```

## 🔧 配置設定

### 環境變數
```bash
# 必要環境變數
GEMINI_API_KEY=your_gemini_api_key
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_mysql_host
DB_DATABASE=your_database

# 可選環境變數
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_CHANNEL_SECRET=your_line_secret
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_azure_region
```

### 檔案上傳設定
```python
# 支援的檔案格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 檔案大小限制
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 圖片壓縮設定
MAX_IMAGE_DIMENSION = 1024  # 最大邊長
```

## 📊 效能優化

### 圖片處理優化
- 自動圖片壓縮減少處理時間
- 支援多種圖片格式
- 檔案大小限制避免記憶體問題

### API 呼叫優化
- 240 秒超時控制
- 錯誤重試機制
- 非同步處理支援

### 資料庫優化
- 批次插入菜單項目
- 索引優化查詢效能
- 連線池管理

## 🔍 除錯與監控

### 日誌記錄
```python
print(f"處理圖片: {image_path}, 大小: {file_size / 1024:.1f}KB")
print(f"圖片已壓縮至: {image.size}")
print(f"✅ 店家ID解析成功: {raw_store_id} -> {store_db_id}")
print(f"🎉 API 成功回應 201 Created ({mode_text})")
```

### 錯誤追蹤
```python
print(f"❌ 店家ID解析失敗: {e}")
print(f"❌ Gemini API 處理失敗: {e}")
print(f"❌ 處理過程中發生錯誤: {e}")
```

## 📈 未來擴展

### 功能擴展
- 支援更多圖片格式 (PDF, WebP)
- 多語言 OCR 辨識
- 智能分類和標籤
- 圖片品質評估

### 效能擴展
- 快取機制
- 批次處理
- 分散式處理
- CDN 整合

## 🔧 完整程式碼整合

### 主要檔案結構
```
app/
├── api/
│   ├── routes.py          # 主要 API 端點
│   ├── helpers.py         # 核心辨識函數
│   └── store_resolver.py  # 店家 ID 解析
├── prompts.py             # 提示詞模板
├── models.py              # 資料庫模型
└── config/
    └── settings.py        # 配置設定
```

### 必要的 import 語句
```python
# 在 routes.py 中需要的 import
from flask import Blueprint, jsonify, request, current_app
from flask_cors import cross_origin
import os
import json
import time
import uuid
from datetime import datetime
from PIL import Image
import signal
import mimetypes

# 在 helpers.py 中需要的 import
from google import genai
from werkzeug.utils import secure_filename
import io
```

### 環境變數設定
```bash
# 必要環境變數
export GEMINI_API_KEY="your_gemini_api_key"
export DB_USER="your_db_user"
export DB_PASSWORD="your_db_password"
export DB_HOST="your_mysql_host"
export DB_DATABASE="your_database"

# 可選環境變數
export LINE_CHANNEL_ACCESS_TOKEN="your_line_token"
export LINE_CHANNEL_SECRET="your_line_secret"
export AZURE_SPEECH_KEY="your_azure_speech_key"
export AZURE_SPEECH_REGION="your_azure_region"

# 後台管理系統驗證 (可選)
export ADMIN_API_TOKEN="your_admin_token"
```

### 依賴套件 (requirements.txt)
```txt
flask==2.3.3
flask-sqlalchemy==3.0.5
flask-cors==4.0.0
google-genai==0.3.2
pillow==10.0.1
pymysql==1.1.0
werkzeug==2.3.7
azure-cognitiveservices-speech==1.34.0
```

### 部署檢查清單
- [ ] 環境變數已正確設定
- [ ] 資料庫連線正常
- [ ] Gemini API 金鑰有效
- [ ] 檔案上傳目錄有寫入權限
- [ ] CORS 設定正確
- [ ] 錯誤處理機制完整
- [ ] 日誌記錄功能正常

### 測試建議
1. **基本功能測試**
   - 上傳不同格式的圖片
   - 測試各種檔案大小
   - 驗證回應格式

2. **錯誤處理測試**
   - 無效的店家 ID
   - 無效的圖片格式
   - 網路連線問題

3. **效能測試**
   - 大檔案處理
   - 並發請求處理
   - 記憶體使用情況

4. **整合測試**
   - 與前端整合
   - 與資料庫整合
   - 與其他 API 整合

## 🏢 後台管理系統整合

### ⚠️ 重要提醒：API 端點區別

**LIFF 前端請使用**：
- `POST /api/menu/process-ocr` - 一般使用者菜單辨識
- `GET /api/menu/ocr/{ocr_menu_id}` - 查詢使用者菜單
- `GET /api/menu/ocr/user/{user_id}` - 查詢使用者菜單歷史

**後台管理系統請使用**：
- `POST /admin/menu/process-ocr` - 後台管理菜單辨識
- `GET /admin/menu/ocr/{ocr_menu_id}` - 後台查詢菜單詳情
- `GET /admin/menu/ocr` - 後台查詢菜單列表

### 新增的後台專用 API 端點

#### 1. 菜單辨識與儲存 API
**端點**: `POST /admin/menu/process-ocr`

**功能**: 專門為後台管理系統設計的菜單辨識 API，直接將辨識結果儲存到資料庫

**請求參數**:
| 參數名稱 | 類型 | 必填 | 說明 |
|---------|------|------|------|
| `image` | File | ✅ | 菜單圖片檔案 |
| `store_id` | String | ✅ | 店家識別碼 |
| `user_id` | String | ❌ | 後台系統使用者 ID (預設: 'admin_system') |
| `lang` | String | ❌ | 目標語言 (預設: 'zh') |
| `store_name` | String | ❌ | 店家名稱 (可選) |
| `admin_token` | String | ❌ | 管理員權限驗證 (可選) |

**成功回應** (HTTP 201):
```json
{
  "success": true,
  "ocr_menu_id": 123,
  "store_id": 456,
  "store_name": "店家名稱",
  "total_items": 5,
  "upload_time": "2024-12-01T12:00:00",
  "processing_notes": "處理備註",
  "message": "成功辨識並儲存 5 個菜單項目"
}
```

#### 2. 查詢 OCR 菜單詳情 API
**端點**: `GET /admin/menu/ocr/{ocr_menu_id}`

**功能**: 根據 OCR 菜單 ID 查詢詳細的菜單資料

**查詢參數**:
| 參數名稱 | 類型 | 說明 |
|---------|------|------|
| `admin_token` | String | 管理員權限驗證 (可選) |

**成功回應** (HTTP 200):
```json
{
  "success": true,
  "ocr_menu": {
    "ocr_menu_id": 123,
    "store_id": 456,
    "store_name": "店家名稱",
    "user_id": 789,
    "upload_time": "2024-12-01T12:00:00",
    "items": [
      {
        "ocr_menu_item_id": 1,
        "item_name": "菜名",
        "translated_desc": "翻譯菜名",
        "price_small": 100,
        "price_big": 120
      }
    ],
    "total_items": 1
  }
}
```

#### 3. 查詢 OCR 菜單列表 API
**端點**: `GET /admin/menu/ocr`

**功能**: 列出所有 OCR 菜單的基本資訊，支援分頁和過濾

**查詢參數**:
| 參數名稱 | 類型 | 說明 |
|---------|------|------|
| `page` | Integer | 頁碼 (預設: 1) |
| `per_page` | Integer | 每頁數量 (預設: 20) |
| `store_id` | Integer | 店家 ID 過濾 (可選) |
| `admin_token` | String | 管理員權限驗證 (可選) |

**成功回應** (HTTP 200):
```json
{
  "success": true,
  "ocr_menus": [
    {
      "ocr_menu_id": 123,
      "store_id": 456,
      "store_name": "店家名稱",
      "user_id": 789,
      "upload_time": "2024-12-01T12:00:00",
      "item_count": 5
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

### 後台系統整合範例

#### JavaScript/TypeScript
```javascript
// 上傳菜單圖片並儲存到資料庫
const formData = new FormData();
formData.append('image', imageFile);
formData.append('store_id', '123');
formData.append('user_id', 'admin_system');
formData.append('store_name', '測試店家');

const response = await fetch('https://your-cloud-run/admin/menu/process-ocr', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('OCR 菜單 ID:', result.ocr_menu_id);

// 查詢菜單詳情
const menuResponse = await fetch(`https://your-cloud-run/admin/menu/ocr/${result.ocr_menu_id}`);
const menuData = await menuResponse.json();
console.log('菜單詳情:', menuData.ocr_menu);

// 查詢菜單列表
const listResponse = await fetch('https://your-cloud-run/admin/menu/ocr?page=1&per_page=10');
const listData = await listResponse.json();
console.log('菜單列表:', listData.ocr_menus);
```

#### Python
```python
import requests

# 上傳菜單圖片
files = {'image': open('menu.jpg', 'rb')}
data = {
    'store_id': '123',
    'user_id': 'admin_system',
    'store_name': '測試店家'
}

response = requests.post(
    'https://your-cloud-run/admin/menu/process-ocr',
    files=files,
    data=data
)

result = response.json()
ocr_menu_id = result['ocr_menu_id']

# 查詢菜單詳情
menu_response = requests.get(f'https://your-cloud-run/admin/menu/ocr/{ocr_menu_id}')
menu_data = menu_response.json()

# 查詢菜單列表
list_response = requests.get('https://your-cloud-run/admin/menu/ocr?page=1&per_page=10')
list_data = list_response.json()
```

### 後台系統整合特點

1. **簡化回應格式**: 只返回必要的資訊，不包含完整的菜單資料
2. **直接資料庫儲存**: 辨識結果直接儲存到 `ocr_menus` 和 `ocr_menu_items` 表
3. **後台使用者管理**: 自動創建和管理後台系統使用者
4. **分頁查詢支援**: 支援大量資料的分頁查詢
5. **店家過濾功能**: 可以按店家 ID 過濾菜單列表
6. **完整的 CRUD 操作**: 提供查詢、列表等基本操作

### 資料庫表格結構

後台系統會直接操作以下表格：
- `ocr_menus`: OCR 菜單主檔
- `ocr_menu_items`: OCR 菜單項目
- `users`: 使用者資料 (後台系統使用者)

### 安全考量

1. **CORS 設定**: 已設定跨域支援
2. **錯誤處理**: 完整的錯誤處理和日誌記錄
3. **參數驗證**: 嚴格的參數驗證和格式檢查
4. **資料庫安全**: 使用參數化查詢防止 SQL 注入
5. **API 隔離**: 後台管理系統 API 使用 `/admin/` 路徑，與 LIFF 前端 API 完全分離
6. **權限驗證**: 可選的管理員權限驗證機制

---

**最後更新**: 2024年12月
**版本**: 1.0.0
**維護者**: 開發團隊
