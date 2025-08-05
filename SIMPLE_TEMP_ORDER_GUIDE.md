# 簡化的臨時訂單系統

## 為什麼要簡化？

你說得對！原本的系統確實太複雜了。我們試圖將臨時菜單項目強制塞進現有的資料庫結構中，這導致了複雜的外鍵約束問題。

## 新的簡化方案

### 核心概念

**分離關注點**：
- **合作店家**：使用完整的資料庫結構（Store → Menu → MenuItem → Order）
- **非合作店家**：使用簡化的臨時訂單系統（直接從拍照辨識結果創建訂單）

### 流程簡化

```
拍照辨識菜單 → 翻譯成使用者語言 → 點餐介面 → 生成語音檔和訂單摘要
```

**不需要**：
- ❌ 複雜的資料庫外鍵約束
- ❌ 強制創建店家記錄
- ❌ 複雜的菜單項目關聯

**只需要**：
- ✅ 簡單的訂單項目列表
- ✅ 基本的驗證
- ✅ 語音生成和訂單摘要

## API 使用方式

### 1. 發送臨時訂單

```javascript
const tempOrderData = {
    line_user_id: "U1234567890abcdef", // 可選
    language: "zh", // 可選，預設中文
    items: [
        {
            item_name: "奶香經典夏威夷",
            quantity: 1,
            price: 115
        },
        {
            item_name: "美國脆薯",
            quantity: 2,
            price: 55
        }
    ]
};

const response = await fetch('/api/orders/temp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(tempOrderData)
});
```

### 2. 回應格式

```json
{
    "message": "臨時訂單建立成功",
    "order_id": "temp_20250805103000_15",
    "order_details": [
        {
            "item_name": "奶香經典夏威夷",
            "quantity": 1,
            "price": 115,
            "subtotal": 115
        }
    ],
    "total_amount": 115,
    "voice_generated": true,
    "order_summary": {
        "order_id": "temp_20250805103000_15",
        "user_id": 15,
        "items": [...],
        "total_amount": 115,
        "order_time": "2025-08-05T10:30:00.000000",
        "status": "pending"
    }
}
```

## 前端整合

### 1. 拍照辨識結果處理

```javascript
// 假設你有拍照辨識的結果
function handleMenuPhotoRecognition(recognizedItems) {
    // 將辨識結果轉換為訂單項目
    window.tempOrderItems = recognizedItems.map(item => ({
        original_name: item.name,
        quantity: 1, // 預設數量
        price: item.price
    }));
    
    // 更新UI
    updateTempOrderUI();
}
```

### 2. 提交訂單

```javascript
async function submitTempOrder() {
    const tempItems = getTempOrderItems();
    
    const orderItems = tempItems.map(item => ({
        item_name: item.original_name,
        quantity: item.quantity || 1,
        price: item.price || 0
    }));
    
    const response = await fetch('/api/orders/temp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            items: orderItems
        })
    });
    
    if (response.ok) {
        const result = await response.json();
        alert(`訂單建立成功！\n訂單編號: ${result.order_id}`);
    }
}
```

## 優勢

### 1. 簡單明瞭
- 不需要複雜的資料庫關聯
- 直接從拍照辨識結果創建訂單
- 減少錯誤發生的機會

### 2. 靈活性高
- 支援任何語言的菜單
- 不需要預先建立店家資料
- 可以快速適應不同的使用場景

### 3. 維護容易
- 程式碼結構清晰
- 錯誤處理簡單
- 容易測試和除錯

## 使用場景

### 1. 非合作店家
- 使用者拍照上傳菜單
- 系統辨識並翻譯
- 使用者點餐
- 生成語音檔和訂單摘要

### 2. 合作店家（現有系統）
- 使用完整的資料庫結構
- 支援複雜的菜單管理
- 完整的訂單追蹤

## 總結

這個簡化方案的核心思想是：**不要試圖用複雜的資料庫結構來處理簡單的需求**。

對於拍照點餐這種簡單需求，我們只需要：
1. 拍照辨識菜單
2. 翻譯成使用者語言
3. 讓使用者點餐
4. 生成語音檔和訂單摘要

不需要複雜的店家、菜單、菜單項目關聯，直接處理訂單項目列表即可。

這樣既簡單又實用！🎉 