# Flask 點餐助手後端功能說明書

## 🎯 系統概述

點餐助手後端是一個基於 Flask 框架開發的智慧點餐系統，提供多語言支援、AI 語音生成、OCR 菜單辨識等功能。系統採用微服務架構，部署在 Google Cloud Run 平台上。

## 🏗️ 技術架構

### 核心技術棧
- **後端框架**: Flask 2.3+
- **資料庫**: Cloud MySQL
- **ORM**: SQLAlchemy
- **部署平台**: Google Cloud Run
- **語音服務**: Azure Speech Service
- **AI 服務**: Google Gemini API
- **聊天機器人**: LINE Bot SDK

### 系統架構圖
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LINE Bot      │    │   LIFF Web      │    │   Admin Panel   │
│   (前端互動)     │    │   (點餐介面)     │    │   (管理後台)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Flask API     │
                    │   (後端服務)     │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cloud MySQL   │    │   Azure TTS     │    │   Gemini API    │
│   (資料庫)       │    │   (語音生成)     │    │   (AI 翻譯)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 專案結構

```
ordering-helper-backend/
├── app/                          # 主要應用程式目錄
│   ├── __init__.py              # Flask 應用程式初始化
│   ├── models.py                # 資料庫模型定義
│   ├── api/                     # API 路由模組
│   │   ├── __init__.py
│   │   ├── routes.py            # 主要 API 端點
│   │   └── helpers.py           # API 輔助函數
│   ├── admin/                   # 管理後台模組
│   │   └── routes.py
│   ├── webhook/                 # LINE Bot Webhook
│   │   └── routes.py
│   ├── errors.py                # 錯誤處理
│   ├── ai_enhancement.py        # AI 功能增強
│   ├── langchain_integration.py # LangChain 整合
│   └── prompts.py               # AI 提示詞
├── static/                      # 靜態檔案
│   ├── css/
│   ├── js/
│   └── voice/                   # 語音檔案
├── templates/                   # HTML 模板
├── tools/                       # 工具腳本
├── logs/                        # 日誌檔案
├── requirements.txt             # Python 依賴
├── run.py                      # 應用程式啟動檔案
└── Dockerfile                  # Docker 容器配置
```

## 🔧 核心功能模組

### 1. 使用者管理模組

#### 功能描述
管理系統使用者，包括 LINE 使用者註冊、語言偏好設定、使用狀態追蹤等。

#### 主要類別
```python
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.BigInteger, primary_key=True)
    line_user_id = db.Column(db.String(100), unique=True, nullable=False)
    preferred_lang = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    state = db.Column(db.String(50), default='normal')
```

#### API 端點
- `POST /api/users/register` - 使用者註冊
- `GET /api/users/{user_id}` - 取得使用者資訊
- `PUT /api/users/{user_id}/language` - 更新語言偏好

### 2. 店家管理模組

#### 功能描述
管理合作店家和非合作店家資訊，包括店家基本資料、多語言介紹、合作等級等。

#### 主要類別
```python
class Store(db.Model):
    __tablename__ = 'stores'
    store_id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(100), nullable=False)
    partner_level = db.Column(db.Integer, default=0)  # 0=非合作, 1=合作, 2=VIP
    gps_lat = db.Column(db.Float)
    gps_lng = db.Column(db.Float)
    place_id = db.Column(db.String(255))
    review_summary = db.Column(db.Text)
    main_photo_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
```

#### API 端點
- `GET /api/stores` - 取得所有店家列表
- `GET /api/stores/{store_id}` - 取得店家詳細資訊
- `GET /api/stores/check-partner-status` - 檢查店家合作狀態

### 3. 菜單管理模組

#### 功能描述
管理合作店家的結構化菜單，包括菜單項目、價格、多語言翻譯等。

#### 主要類別
```python
class Menu(db.Model):
    __tablename__ = 'menus'
    menu_id = db.Column(db.BigInteger, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=False)
    version = db.Column(db.Integer, default=1)
    effective_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    menu_item_id = db.Column(db.BigInteger, primary_key=True)
    menu_id = db.Column(db.BigInteger, db.ForeignKey('menus.menu_id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    price_big = db.Column(db.Integer)
    price_small = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
```

#### API 端點
- `GET /api/menu/{store_id}` - 取得店家菜單
- `GET /api/menu/{store_id}/items` - 取得菜單項目
- `POST /api/menu/process-ocr` - 處理 OCR 菜單

### 4. 訂單管理模組

#### 功能描述
處理訂單建立、查詢、狀態管理，支援合作店家和非合作店家兩種模式。

#### 主要類別
```python
class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=False)
    order_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    total_amount = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    order_item_id = db.Column(db.BigInteger, primary_key=True)
    order_id = db.Column(db.BigInteger, db.ForeignKey('orders.order_id'), nullable=False)
    menu_item_id = db.Column(db.BigInteger, db.ForeignKey('menu_items.menu_item_id'))
    quantity_small = db.Column(db.Integer, default=0)
    subtotal = db.Column(db.Integer, nullable=False)
    original_name = db.Column(db.String(100))
    translated_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
```

#### API 端點
- `POST /api/orders` - 建立訂單（合作店家）
- `POST /api/orders/simple` - 建立簡化訂單（非合作店家）
- `GET /api/orders/{order_id}` - 取得訂單詳情
- `GET /api/orders/{order_id}/confirm` - 取得訂單確認資訊

### 5. 語音生成模組

#### 功能描述
使用 Azure Speech Service 生成自然的中文語音，支援語速調整和多種語音選項。

#### 主要功能
```python
def generate_voice_order(order_id: int) -> str:
    """生成訂單語音檔案"""
    
def synthesize_azure_tts(text: str, voice_name: str = "zh-TW-HsiaoChenNeural") -> bytes:
    """使用 Azure TTS 合成語音"""
    
def generate_and_upload_audio_to_gcs(text: str, order_id: str) -> str:
    """生成語音檔並上傳到 GCS"""
```

#### API 端點
- `POST /api/voice/generate` - 生成自定義語音檔
- `GET /api/voices/{filename}` - 取得語音檔案
- `POST /api/voice/order/{order_id}` - 生成訂單語音

### 6. OCR 處理模組

#### 功能描述
使用 Google Gemini API 進行菜單圖片辨識和翻譯，支援非合作店家的菜單處理。

#### 主要功能
```python
def process_menu_image(image_data: bytes) -> dict:
    """處理菜單圖片 OCR"""
    
def translate_menu_items(items: list, target_lang: str) -> list:
    """翻譯菜單項目"""
    
def extract_menu_structure(ocr_text: str) -> list:
    """從 OCR 文字中提取菜單結構"""
```

#### API 端點
- `POST /api/menu/process-ocr` - 處理菜單圖片 OCR
- `POST /api/menu/simple-ocr` - 簡化 OCR 處理
- `POST /api/upload-menu-image` - 上傳菜單圖片

### 7. LINE Bot 整合模組

#### 功能描述
處理 LINE Bot 的 Webhook 事件，包括訊息接收、回覆、語音控制等。

#### 主要功能
```python
def handle_line_webhook(request_data: dict) -> dict:
    """處理 LINE Webhook 事件"""
    
def send_order_to_line_bot(user_id: str, order_data: dict) -> bool:
    """發送訂單到 LINE Bot"""
    
def process_voice_control_command(command: str, user_id: str) -> dict:
    """處理語音控制指令"""
```

#### API 端點
- `POST /webhook/line` - LINE Bot Webhook
- `POST /api/line/send-message` - 發送訊息到 LINE
- `POST /api/line/voice-control` - 語音控制處理

## 🔌 API 端點詳細說明

### 核心 API 端點

#### 1. 健康檢查
```http
GET /api/health
```
**功能**: 檢查服務健康狀態
**回應**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-08T19:00:32Z",
  "version": "1.0.0"
}
```

#### 2. 店家相關 API

**取得店家列表**
```http
GET /api/stores
```
**參數**:
- `lang` (可選): 語言代碼 (zh-TW, en, ja, ko)
- `partner_level` (可選): 合作等級篩選

**回應**:
```json
{
  "success": true,
  "stores": [
    {
      "store_id": 1,
      "store_name": "經典義大利麵店",
      "partner_level": 2,
      "description": "提供正宗義大利麵",
      "main_photo_url": "https://...",
      "gps_lat": 25.0330,
      "gps_lng": 121.5654
    }
  ]
}
```

**取得店家詳細資訊**
```http
GET /api/stores/{store_id}
```
**參數**:
- `lang` (可選): 語言代碼

**回應**:
```json
{
  "success": true,
  "store": {
    "store_id": 1,
    "store_name": "經典義大利麵店",
    "partner_level": 2,
    "description": "提供正宗義大利麵",
    "review_summary": "顧客評價很高",
    "top_dishes": ["經典夏威夷", "奶油培根"],
    "main_photo_url": "https://...",
    "gps_lat": 25.0330,
    "gps_lng": 121.5654
  }
}
```

#### 3. 菜單相關 API

**取得店家菜單**
```http
GET /api/menu/{store_id}
```
**參數**:
- `lang` (可選): 語言代碼

**回應**:
```json
{
  "success": true,
  "menu": {
    "menu_id": 1,
    "store_id": 1,
    "version": 1,
    "items": [
      {
        "menu_item_id": 1,
        "item_name": "經典夏威夷奶醬義大利麵",
        "translated_name": "Classic Hawaiian Cream Pasta",
        "price_small": 115,
        "price_big": 145,
        "description": "使用新鮮奶油製作的經典義大利麵"
      }
    ]
  }
}
```

**處理 OCR 菜單**
```http
POST /api/menu/process-ocr
```
**請求體**:
```json
{
  "image_data": "base64_encoded_image",
  "target_lang": "en",
  "store_name": "非合作店家"
}
```

**回應**:
```json
{
  "success": true,
  "menu_items": [
    {
      "name": {
        "original": "蜂蜜茶",
        "translated": "Honey Tea"
      },
      "price": 150,
      "quantity": 1
    }
  ]
}
```

#### 4. 訂單相關 API

**建立訂單（合作店家）**
```http
POST /api/orders
```
**請求體**:
```json
{
  "user_id": 123,
  "store_id": 1,
  "items": [
    {
      "menu_item_id": 1,
      "quantity": 2,
      "price": 115
    }
  ],
  "lang": "zh-TW"
}
```

**建立簡化訂單（非合作店家）**
```http
POST /api/orders/simple
```
**請求體**:
```json
{
  "line_user_id": "U1234567890abcdef",
  "items": [
    {
      "name": {
        "original": "蜂蜜茶",
        "translated": "Honey Tea"
      },
      "quantity": 1,
      "price": 150
    }
  ],
  "lang": "en"
}
```

**回應**:
```json
{
  "success": true,
  "order_id": 21,
  "message": "訂單建立成功",
  "total_amount": 150,
  "items_count": 1,
  "voice_url": "https://...",
  "zh_summary": "蜂蜜茶 x 1",
  "user_summary": "Honey Tea x 1"
}
```

#### 5. 語音相關 API

**生成自定義語音**
```http
POST /api/voice/generate
```
**請求體**:
```json
{
  "text": "老闆，我要蜂蜜茶一杯，謝謝。",
  "voice_name": "zh-TW-HsiaoChenNeural",
  "speech_rate": 1.0
}
```

**回應**:
```json
{
  "success": true,
  "voice_url": "https://...",
  "duration": 3000,
  "file_size": 45000
}
```

### LINE Bot 相關 API

#### 1. Webhook 處理
```http
POST /webhook/line
```
**功能**: 接收 LINE Bot 事件
**支援事件**:
- 文字訊息
- 圖片訊息
- 語音控制指令
- 位置訊息

#### 2. 語音控制指令
- `voice_slow_{order_id}` - 慢速播放 (0.7x)
- `voice_normal_{order_id}` - 正常播放 (1.0x)
- `voice_fast_{order_id}` - 快速播放 (1.3x)
- `voice_replay_{order_id}` - 重新播放

## 🔧 配置和環境變數

### 必要環境變數
```bash
# 資料庫配置
DATABASE_URL=mysql+aiomysql://user:password@host:port/database
DB_USER=gae252g1usr
DB_PASSWORD=gae252g1PSWD!
DB_HOST=35.201.153.17
DB_DATABASE=gae252g1_db

# LINE Bot 配置
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# Azure Speech Service
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=australiaeast

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Google Cloud Storage
GCS_BUCKET_NAME=ordering-helper-voice-files
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json

# 應用程式配置
FLASK_ENV=production
SECRET_KEY=your_secret_key
BASE_URL=https://ordering-helper-backend-1095766716155.asia-east1.run.app
```

### 可選環境變數
```bash
# 強制使用 Cloud MySQL
FORCE_CLOUD_MYSQL=true

# 日誌等級
LOG_LEVEL=INFO

# CORS 設定
CORS_ORIGINS=https://liff.line.me,https://your-domain.com
```

## 🚀 部署指南

### 1. 本地開發環境
```bash
# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
export FLASK_ENV=development
export DATABASE_URL=mysql://user:password@localhost:3306/database

# 啟動應用程式
python run.py
```

### 2. Docker 部署
```bash
# 建構 Docker 映像
docker build -t ordering-helper-backend .

# 執行容器
docker run -p 5000:5000 ordering-helper-backend
```

### 3. Google Cloud Run 部署
```bash
# 部署到 Cloud Run
gcloud run deploy ordering-helper-backend \
  --source . \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated
```

## 📊 監控和日誌

### 日誌配置
```python
import logging

# 設定日誌格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 關鍵指標
- **API 回應時間**: < 3 秒
- **資料庫查詢時間**: < 1 秒
- **語音生成時間**: < 5 秒
- **OCR 處理時間**: < 10 秒

### 健康檢查端點
```http
GET /api/health
```
檢查項目：
- 資料庫連線狀態
- 外部 API 連線狀態
- 系統資源使用情況

## 🔒 安全性

### 1. 身份驗證
- LINE Bot 使用 Channel Access Token 驗證
- API 端點使用適當的 CORS 設定
- 敏感資料使用環境變數管理

### 2. 資料保護
- 資料庫連線使用 SSL/TLS
- 語音檔案使用 HTTPS 傳輸
- 使用者資料加密儲存

### 3. 錯誤處理
- 完整的錯誤訊息處理
- 不會暴露敏感資訊
- 適當的 HTTP 狀態碼

## 🧪 測試

### 單元測試
```bash
# 執行測試
python -m pytest tests/

# 執行特定測試
python -m pytest tests/test_api.py::test_order_creation
```

### 整合測試
```bash
# 測試 API 端點
python tools/test_api_endpoints.py

# 測試資料庫連線
python tools/test_database_connection.py

# 測試語音生成
python tools/test_voice_generation.py
```

## 📈 效能優化

### 1. 資料庫優化
- 使用適當的索引
- 查詢結果快取
- 連線池管理

### 2. API 優化
- 回應壓縮
- 靜態檔案快取
- 非同步處理

### 3. 語音處理優化
- 語音檔案快取
- 並行處理
- 檔案大小優化

## 🔄 版本控制

### 版本號格式
```
MAJOR.MINOR.PATCH
例如: 1.2.3
```

### 更新日誌
- **v1.0.0**: 初始版本
- **v1.1.0**: 新增語音功能
- **v1.2.0**: 新增 OCR 功能
- **v1.3.0**: 效能優化

## 📞 支援和維護

### 問題回報
- 使用 GitHub Issues
- 提供詳細的錯誤訊息
- 包含重現步驟

### 維護計劃
- 定期安全更新
- 效能監控
- 功能增強

---

**最後更新**: 2025-08-08  
**版本**: 1.3.0  
**維護狀態**: 🟢 正常維護
