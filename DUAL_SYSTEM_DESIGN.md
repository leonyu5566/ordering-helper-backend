# 雙系統架構設計：合作店家 vs 非合作店家

## 🎯 系統分離的核心概念

### 合作店家系統（Partner System）
- **資料來源**：資料庫中的預設菜單
- **功能**：完整的訂單管理、庫存追蹤、會員系統
- **特點**：穩定、可靠、功能完整

### 非合作店家系統（Guest System）
- **資料來源**：拍照辨識的臨時菜單
- **功能**：簡化的點餐、語音生成、訂單摘要
- **特點**：靈活、快速、即時處理

## 🏗️ 系統架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                    雙系統架構                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐               │
│  │   合作店家系統   │    │   非合作店家系統 │               │
│  │  Partner System │    │   Guest System  │               │
│  └─────────────────┘    └─────────────────┘               │
│           │                       │                        │
│           ▼                       ▼                        │
│  ┌─────────────────┐    ┌─────────────────┐               │
│  │   資料庫菜單    │    │   拍照辨識菜單  │               │
│  │  Database Menu  │    │  OCR Menu       │               │
│  └─────────────────┘    └─────────────────┘               │
│           │                       │                        │
│           ▼                       ▼                        │
│  ┌─────────────────┐    ┌─────────────────┐               │
│  │   完整訂單系統  │    │   簡化訂單系統  │               │
│  │  Full Order     │    │  Simple Order   │               │
│  └─────────────────┘    └─────────────────┘               │
│           │                       │                        │
│           ▼                       ▼                        │
│  ┌─────────────────┐    ┌─────────────────┐               │
│  │   會員管理      │    │   語音生成      │               │
│  │  Member Mgmt    │    │  Voice Gen      │               │
│  └─────────────────┘    └─────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## 📋 詳細系統設計

### 1. 合作店家系統（Partner System）

#### API 端點
```
GET    /api/stores/{store_id}          # 取得店家資訊
GET    /api/menu/{store_id}            # 取得店家菜單
POST   /api/orders                     # 建立正式訂單
GET    /api/orders/{order_id}/confirm  # 訂單確認
GET    /api/orders/history             # 訂單歷史
```

#### 資料流程
```
1. 使用者選擇合作店家
2. 從資料庫載入預設菜單
3. 使用者選擇商品和數量
4. 建立正式訂單（包含外鍵關聯）
5. 更新庫存和會員資料
6. 發送 LINE 通知
```

#### 特點
- ✅ 完整的資料庫關聯
- ✅ 庫存管理
- ✅ 會員積分系統
- ✅ 訂單歷史追蹤
- ✅ 店家管理後台
- ✅ 多語言翻譯支援

### 2. 非合作店家系統（Guest System）

#### API 端點
```
POST   /api/menu/simple-ocr           # 拍照辨識菜單
POST   /api/orders/simple             # 建立簡化訂單
GET    /api/test-simple-menu          # 測試頁面
```

#### 資料流程
```
1. 使用者拍照上傳菜單
2. AI 辨識菜單內容
3. 翻譯成使用者語言
4. 生成臨時菜單介面
5. 使用者選擇商品
6. 建立簡化訂單
7. 生成語音檔和摘要
```

#### 特點
- ✅ 即時拍照辨識
- ✅ 多語言翻譯
- ✅ 簡化訂單處理
- ✅ 語音生成
- ✅ 無需資料庫預設
- ✅ 靈活適應任何店家

## 🔧 技術實現

### 1. 路由分離

```python
# 合作店家路由
@api_bp.route('/stores/<int:store_id>', methods=['GET'])
@api_bp.route('/menu/<int:store_id>', methods=['GET'])
@api_bp.route('/orders', methods=['POST'])

# 非合作店家路由
@api_bp.route('/menu/simple-ocr', methods=['POST'])
@api_bp.route('/orders/simple', methods=['POST'])
```

### 2. 資料模型分離

```python
# 合作店家模型（現有）
class Store(db.Model):
    store_id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(100))
    # ... 其他欄位

class MenuItem(db.Model):
    menu_item_id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('store.store_id'))
    # ... 其他欄位

# 非合作店家模型（簡化）
class SimpleOrder(db.Model):
    order_id = db.Column(db.String(50), primary_key=True)
    items = db.Column(db.JSON)  # 直接儲存 JSON
    total_amount = db.Column(db.Float)
    created_at = db.Column(db.DateTime)
```

### 3. 前端分離

```javascript
// 合作店家前端
class PartnerMenuSystem {
    async loadStoreMenu(storeId) {
        // 從資料庫載入菜單
    }
    
    async createOrder(orderData) {
        // 建立正式訂單
    }
}

// 非合作店家前端
class GuestMenuSystem {
    async processMenuPhoto(imageFile) {
        // 拍照辨識菜單
    }
    
    async createSimpleOrder(orderData) {
        // 建立簡化訂單
    }
}
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

## 🚀 實施步驟

### 階段 1：系統分離
1. ✅ 創建簡化 API 端點
2. ✅ 實現拍照辨識功能
3. ✅ 實現簡化訂單處理
4. ✅ 創建測試頁面

### 階段 2：前端整合
1. 🔄 修改現有前端，支援雙系統
2. 🔄 創建系統選擇介面
3. 🔄 實現無縫切換

### 階段 3：優化完善
1. ⏳ 改善拍照辨識準確率
2. ⏳ 優化語音生成品質
3. ⏳ 增加更多語言支援

## 📱 使用者體驗流程

### 合作店家流程
```
1. 選擇合作店家
2. 瀏覽預設菜單
3. 選擇商品和數量
4. 確認訂單
5. 收到 LINE 通知
```

### 非合作店家流程
```
1. 拍照上傳菜單
2. 等待 AI 辨識
3. 瀏覽翻譯後菜單
4. 選擇商品和數量
5. 提交訂單
6. 獲得語音檔和摘要
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

這個雙系統架構完美解決了您提到的需求：**合作店家使用資料庫菜單，非合作店家使用拍照辨識**。兩個系統完全獨立，各自優化，為不同類型的店家提供最適合的解決方案。 