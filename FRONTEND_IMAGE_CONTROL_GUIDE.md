# 前端圖片框框控制指南

## 概述

為了簡化點餐介面並為未來功能擴展做準備，我們在後端 API 中新增了 `show_image` 欄位來控制是否顯示圖片框框。

## API 回應格式

### 菜單項目結構

所有菜單項目現在都包含 `show_image` 欄位：

```json
{
  "menu_items": [
    {
      "id": "temp_789_0",
      "original_name": "原菜名",
      "translated_name": "Translated Name",
      "price": 100,
      "price_small": 100,
      "price_large": 100,
      "description": "描述",
      "category": "分類",
      "image_url": "/static/images/default-dish.png",
      "imageUrl": "/static/images/default-dish.png",
      "show_image": false,  // 新增：控制是否顯示圖片框框
      "inventory": 999,
      "available": true
    }
  ]
}
```

## 前端實作建議

### 1. 簡化模式（目前建議）

當 `show_image: false` 時，前端應該：

```javascript
// 檢查是否顯示圖片框框
if (menuItem.show_image) {
  // 顯示圖片框框
  renderImageContainer(menuItem.image_url);
} else {
  // 隱藏圖片框框，優化版面配置
  hideImageContainer();
  
  // 可以將原本圖片框框的空間用來：
  // - 顯示更多菜品資訊
  // - 增加價格顯示的視覺效果
  // - 優化數量選擇器的佈局
}
```

### 2. 版面配置優化

移除圖片框框後的建議佈局：

```
┌─────────────────────────────────────────┐
│ 菜品名稱                    NT$ 115    │
│ 描述文字                               │
│                    [-] 0 [+]           │
└─────────────────────────────────────────┘
```

而不是原本的：

```
┌─────────────────────────────────────────┐
│ [圖片框] 菜品名稱            NT$ 115   │
│        描述文字                        │
│                    [-] 0 [+]           │
└─────────────────────────────────────────┘
```

### 3. CSS 調整建議

```css
/* 原本的圖片框框樣式 */
.menu-item-image {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  background-color: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 當 show_image: false 時隱藏 */
.menu-item-image.hidden {
  display: none;
}

/* 優化菜品資訊的佈局 */
.menu-item-info {
  margin-left: 0; /* 原本有 margin-left 來避開圖片框 */
  flex: 1;
}
```

## 受影響的 API 端點

以下 API 端點都會返回包含 `show_image` 欄位的菜單項目：

1. **`GET /api/menu/<store_id>`** - 合作店家菜單查詢
2. **`GET /api/menu/by-place-id/<place_id>`** - 根據 place_id 查詢菜單
3. **`POST /api/menu/process-ocr`** - OCR 菜單處理
4. **`POST /api/menu/simple-ocr`** - 簡化版 OCR
5. **`POST /api/upload-menu-image`** - 上傳菜單圖片

## 向後相容性

- 所有現有的 API 端點保持不變
- 新增的 `show_image` 欄位預設值為 `false`
- 前端可以選擇是否使用這個新欄位

## 未來擴展

當需要重新啟用圖片功能時：

1. 後端可以將 `show_image` 設為 `true`
2. 前端根據這個欄位動態顯示/隱藏圖片框框
3. 可以支援實際的菜品圖片上傳和顯示

## 測試建議

1. **功能測試**
   - 確認所有菜單項目都包含 `show_image: false`
   - 測試前端隱藏圖片框框後的版面配置
   - 驗證數量選擇器和其他功能正常運作

2. **版面測試**
   - 測試不同螢幕尺寸下的版面效果
   - 確認菜品資訊的對齊和間距
   - 驗證整體視覺效果的一致性

3. **效能測試**
   - 確認移除圖片框框後的載入速度
   - 測試大量菜品時的滾動效能
   - 驗證記憶體使用量的改善
