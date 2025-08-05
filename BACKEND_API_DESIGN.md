# 後端 API 設計：純 API 端點

## 🎯 後端職責

作為後端，我們的職責是：
- ✅ 提供 API 端點
- ✅ 處理資料庫操作
- ✅ 實現業務邏輯
- ❌ 不處理前端頁面
- ❌ 不處理系統選擇介面

## 📋 API 端點設計

### 合作店家 API（現有）
```
GET    /api/stores                    # 取得所有店家
GET    /api/stores/{store_id}         # 取得店家資訊
GET    /api/menu/{store_id}           # 取得店家菜單
POST   /api/orders                    # 建立正式訂單
GET    /api/orders/{order_id}/confirm # 訂單確認
GET    /api/orders/history            # 訂單歷史
```

### 非合作店家 API（新增）
```
POST   /api/menu/simple-ocr           # 拍照辨識菜單
POST   /api/orders/simple             # 建立簡化訂單
```

## 🔧 移除不必要的路由

### 移除的端點
- ❌ `/api/system-selector` - 系統選擇器頁面
- ❌ `/api/test-simple-menu` - 測試頁面
- ❌ 所有 `render_template` 相關路由

### 保留的端點
- ✅ 純 API 端點
- ✅ JSON 回應
- ✅ 無前端頁面

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

## 🎯 使用流程

### LIFF 前端負責：
1. **系統選擇介面** - 讓使用者選擇合作店家或拍照辨識
2. **頁面路由** - 根據選擇導向不同頁面
3. **使用者體驗** - 介面設計和互動

### 後端負責：
1. **API 端點** - 提供資料和處理邏輯
2. **資料庫操作** - 儲存和查詢資料
3. **業務邏輯** - 訂單處理、語音生成等

## 📱 API 使用範例

### 合作店家流程
```javascript
// LIFF 前端調用
const response = await fetch('/api/stores');
const stores = await response.json();

const menuResponse = await fetch(`/api/menu/${storeId}`);
const menu = await menuResponse.json();

const orderResponse = await fetch('/api/orders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData)
});
```

### 非合作店家流程
```javascript
// LIFF 前端調用
const formData = new FormData();
formData.append('image', imageFile);
formData.append('target_lang', userLanguage);

const ocrResponse = await fetch('/api/menu/simple-ocr', {
    method: 'POST',
    body: formData
});

const orderResponse = await fetch('/api/orders/simple', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData)
});
```

## 🚀 部署重點

### 1. 純 API 服務
- 只提供 JSON 回應
- 不包含任何前端頁面
- 支援 CORS 跨域請求

### 2. 錯誤處理
```python
# 統一的錯誤回應格式
{
    "success": false,
    "error": "錯誤訊息",
    "details": "詳細資訊"
}
```

### 3. 成功回應
```python
# 統一的成功回應格式
{
    "success": true,
    "data": {...},
    "message": "操作成功"
}
```

## 🎉 總結

後端的職責是：
1. **提供 API 端點** - 合作店家和非合作店家的所有功能
2. **處理資料庫** - 儲存和查詢資料
3. **實現業務邏輯** - 訂單處理、語音生成等
4. **不處理前端** - 頁面設計和系統選擇由 LIFF 前端負責

這樣的分離讓：
- **後端**：專注於 API 和業務邏輯
- **前端**：專注於使用者體驗和介面設計
- **職責清晰**：各自負責自己的領域 