# 非合作店家 OCR 菜單資料庫整合

## 功能概述

現在非合作店家的菜單照片辨識結果也會自動儲存到資料庫中，讓使用者可以：
- 查看歷史辨識的菜單
- 重複使用已辨識的菜單
- 追蹤辨識記錄

## 修改的 API 端點

### 1. `POST /api/menu/simple-ocr`

**功能變更**：原本只是即時辨識，現在會自動儲存到資料庫

**新增參數**：
- `user_id`：使用者 ID（可選，預設為 1）

**回應新增欄位**：
- `ocr_menu_id`：儲存的 OCR 菜單 ID
- `saved_to_database`：是否成功儲存到資料庫

**資料庫儲存**：
- 建立 `OCRMenu` 記錄
- 建立 `OCRMenuItem` 記錄
- 自動提交到資料庫

### 2. `POST /api/upload-menu-image`

**功能變更**：非合作店家（`store_id` 為空或 'temp'）的辨識結果也會儲存到資料庫

**新增回應欄位**：
- `ocr_menu_id`：儲存的 OCR 菜單 ID
- `saved_to_database`：是否成功儲存到資料庫

## 新增的 API 端點

### 3. `GET /api/menu/ocr/{ocr_menu_id}`

**功能**：取得指定的 OCR 菜單詳細資料

**回應格式**：
```json
{
  "success": true,
  "ocr_menu": {
    "ocr_menu_id": 123,
    "store_name": "店家名稱",
    "user_id": 1,
    "upload_time": "2024-01-01T12:00:00",
    "items": [
      {
        "id": 456,
        "name": "菜名",
        "price": 100,
        "price_big": 120,
        "description": "描述"
      }
    ],
    "total_items": 1
  }
}
```

### 4. `GET /api/menu/ocr?user_id={user_id}`

**功能**：列出指定使用者的所有 OCR 菜單

**回應格式**：
```json
{
  "success": true,
  "ocr_menus": [
    {
      "ocr_menu_id": 123,
      "store_name": "店家名稱",
      "upload_time": "2024-01-01T12:00:00",
      "item_count": 5
    }
  ],
  "total_menus": 1
}
```

## 資料庫模型

### OCRMenu（OCR 菜單主檔）
- `ocr_menu_id`：主鍵
- `user_id`：使用者 ID
- `store_name`：店家名稱
- `upload_time`：上傳時間

### OCRMenuItem（OCR 菜單項目）
- `ocr_menu_item_id`：主鍵
- `ocr_menu_id`：關聯到 OCRMenu
- `item_name`：品項名稱
- `price_small`：小份價格
- `price_big`：大份價格
- `translated_desc`：翻譯後描述

## 使用流程

### 1. 上傳菜單照片
```bash
POST /api/menu/simple-ocr
Content-Type: multipart/form-data

image: [菜單圖片檔案]
user_id: 1
target_lang: en
```

### 2. 檢查儲存結果
回應中會包含：
- `saved_to_database: true`
- `ocr_menu_id: 123`

### 3. 查詢儲存的菜單
```bash
GET /api/menu/ocr/123
```

### 4. 列出使用者的菜單
```bash
GET /api/menu/ocr?user_id=1
```

## 錯誤處理

- 如果資料庫儲存失敗，會自動回滾
- 回應中會包含錯誤訊息和處理備註
- 即使儲存失敗，辨識功能仍然正常運作

## 測試

使用提供的測試腳本：
```bash
python test_ocr_database.py
```

**注意**：需要準備一張測試用的菜單圖片 `test_menu.jpg`

## 向後相容性

- 所有現有的 API 端點保持不變
- 新增的資料庫儲存功能是可選的
- 如果沒有提供 `user_id`，會使用預設值 1

## 注意事項

1. **資料庫連線**：確保資料庫連線正常
2. **使用者 ID**：建議前端傳送真實的使用者 ID
3. **圖片大小**：仍然有 10MB 的限制
4. **錯誤處理**：資料庫錯誤不會影響 OCR 辨識功能
5. **效能**：資料庫操作會增加一些處理時間

## 未來改進

- 新增菜單分類功能
- 支援菜單版本管理
- 新增菜單分享功能
- 支援菜單評分和評論
