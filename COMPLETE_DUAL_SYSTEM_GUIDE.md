# 完整雙系統使用指南

## 🎯 系統概述

我們已經成功實現了完整的雙系統架構，完美分離了合作店家和非合作店家的需求：

### 🏪 合作店家系統（Partner System）
- **資料來源**：資料庫中的預設菜單
- **功能**：完整的訂單管理、庫存追蹤、會員系統
- **特點**：穩定、可靠、功能完整

### 📸 非合作店家系統（Guest System）
- **資料來源**：拍照辨識的臨時菜單
- **功能**：簡化的點餐、語音生成、訂單摘要
- **特點**：靈活、快速、即時處理

## 🚀 快速開始

### 1. 訪問系統選擇器
```
http://your-domain/api/system-selector
```

### 2. 選擇適合的系統
- **合作店家**：點擊「選擇合作店家」
- **非合作店家**：點擊「開始拍照辨識」

## 📋 詳細使用指南

### 合作店家系統使用流程

#### 1. 選擇店家
```
GET /api/stores
```
返回所有合作店家列表

#### 2. 載入菜單
```
GET /api/menu/{store_id}
```
從資料庫載入預設菜單

#### 3. 建立訂單
```
POST /api/orders
```
建立正式訂單，包含完整的外鍵關聯

#### 4. 訂單確認
```
GET /api/orders/{order_id}/confirm
```
查看訂單確認資訊

### 非合作店家系統使用流程

#### 1. 拍照辨識
```
POST /api/menu/simple-ocr
```
上傳菜單照片，AI 自動辨識和翻譯

#### 2. 建立簡化訂單
```
POST /api/orders/simple
```
建立簡化訂單，生成語音和摘要

#### 3. 測試頁面
```
GET /api/test-simple-menu
```
完整的測試介面

## 🔧 API 端點總覽

### 合作店家 API
| 端點 | 方法 | 功能 |
|------|------|------|
| `/api/stores` | GET | 取得所有店家 |
| `/api/stores/{store_id}` | GET | 取得店家資訊 |
| `/api/menu/{store_id}` | GET | 取得店家菜單 |
| `/api/orders` | POST | 建立正式訂單 |
| `/api/orders/{order_id}/confirm` | GET | 訂單確認 |
| `/api/orders/history` | GET | 訂單歷史 |

### 非合作店家 API
| 端點 | 方法 | 功能 |
|------|------|------|
| `/api/menu/simple-ocr` | POST | 拍照辨識菜單 |
| `/api/orders/simple` | POST | 建立簡化訂單 |
| `/api/test-simple-menu` | GET | 測試頁面 |
| `/api/system-selector` | GET | 系統選擇器 |

## 📊 資料模型

### 合作店家模型（現有）
```python
class Store(db.Model):
    store_id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(100))
    # ... 其他欄位

class MenuItem(db.Model):
    menu_item_id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('store.store_id'))
    # ... 其他欄位
```

### 非合作店家模型（新增）
```python
class SimpleOrder(db.Model):
    order_id = db.Column(db.String(50), primary_key=True)
    user_language = db.Column(db.String(10), default='zh')
    items = db.Column(db.JSON)  # 直接儲存 JSON
    total_amount = db.Column(db.Float, nullable=False)
    voice_url = db.Column(db.String(200))
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(20), default='pending')

class SimpleMenuProcessing(db.Model):
    processing_id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(200), nullable=False)
    target_language = db.Column(db.String(10), default='en')
    ocr_result = db.Column(db.JSON)
    menu_items = db.Column(db.JSON)
    processing_time = db.Column(db.Float)
    status = db.Column(db.String(20), default='processing')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
```

## 🎯 使用場景對比

| 功能 | 合作店家 | 非合作店家 |
|------|----------|------------|
| 菜單來源 | 資料庫預設 | 拍照辨識 |
| 訂單類型 | 正式訂單 | 簡化訂單 |
| 會員系統 | 完整支援 | 無需會員 |
| 庫存管理 | 即時更新 | 無需庫存 |
| 多語言 | 預設翻譯 | 即時翻譯 |
| 語音生成 | 可選功能 | 核心功能 |
| 訂單追蹤 | 完整歷史 | 簡單摘要 |
| 資料庫複雜度 | 高（多表關聯） | 低（簡單結構） |
| 維護難度 | 高 | 低 |
| 靈活性 | 低 | 高 |

## 📱 前端整合

### 合作店家前端
```javascript
class PartnerMenuSystem {
    async loadStoreMenu(storeId) {
        const response = await fetch(`/api/menu/${storeId}`);
        return response.json();
    }
    
    async createOrder(orderData) {
        const response = await fetch('/api/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });
        return response.json();
    }
}
```

### 非合作店家前端
```javascript
class GuestMenuSystem {
    async processMenuPhoto(imageFile, targetLang) {
        const formData = new FormData();
        formData.append('image', imageFile);
        formData.append('target_lang', targetLang);
        
        const response = await fetch('/api/menu/simple-ocr', {
            method: 'POST',
            body: formData
        });
        return response.json();
    }
    
    async createSimpleOrder(orderData) {
        const response = await fetch('/api/orders/simple', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });
        return response.json();
    }
}
```

## 🚀 部署和測試

### 1. 啟動服務器
```bash
python run.py
```

### 2. 測試系統選擇器
```
http://localhost:5000/api/system-selector
```

### 3. 測試合作店家系統
```
http://localhost:5000/api/stores
```

### 4. 測試非合作店家系統
```
http://localhost:5000/api/test-simple-menu
```

## 🎉 優勢總結

### 1. **完全分離**
- 兩個系統獨立運作
- 互不干擾
- 各自優化

### 2. **靈活性高**
- 合作店家：功能完整
- 非合作店家：快速適應

### 3. **維護簡單**
- 清晰的職責分離
- 容易除錯
- 獨立部署

### 4. **使用者友好**
- 根據需求選擇系統
- 簡化的操作流程
- 即時的反饋

## 🔮 未來擴展

### 1. 合作店家系統擴展
- 增加更多店家管理功能
- 改善庫存管理系統
- 增加會員積分功能

### 2. 非合作店家系統擴展
- 改善拍照辨識準確率
- 增加更多語言支援
- 優化語音生成品質

### 3. 系統整合
- 統一的用戶介面
- 無縫的系統切換
- 共享的用戶資料

這個雙系統架構完美解決了您的需求：**合作店家使用資料庫菜單，非合作店家使用拍照辨識**。兩個系統完全獨立，各自優化，為不同類型的店家提供最適合的解決方案。 