# OCR 菜單增強功能實作總結

## 功能概述

根據您的需求，我們已經完成了以下兩個主要功能的實作：

1. **OCR 菜單存入 Cloud MySQL 資料庫的 ocr_menu_id 要含 store_id**
2. **翻譯後（使用者語言設定）的 OCR 菜單存入 Cloud MySQL 資料庫的 ocr-menu-translations**

## 修改內容

### 1. 資料庫模型修改

#### OCRMenu 模型增強
- 新增 `store_id` 欄位，關聯到 `stores` 表
- 保持向後相容性，`store_id` 可為 NULL

```python
class OCRMenu(db.Model):
    ocr_menu_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=True)  # 新增
    store_name = db.Column(db.String(100))
    upload_time = db.Column(db.DateTime, server_default=db.func.current_timestamp())
```

#### 新增 OCRMenuTranslation 模型
- 專門儲存 OCR 菜單的翻譯資料
- 支援多語言翻譯

```python
class OCRMenuTranslation(db.Model):
    ocr_menu_translation_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    ocr_menu_item_id = db.Column(db.BigInteger, db.ForeignKey('ocr_menu_items.ocr_menu_item_id'), nullable=False)
    lang_code = db.Column(db.String(10), db.ForeignKey('languages.line_lang_code'), nullable=False)
    translated_name = db.Column(db.String(100), nullable=False)
    translated_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
```

### 2. 資料庫表結構修改

#### ocr_menus 表
```sql
ALTER TABLE ocr_menus ADD COLUMN store_id INT DEFAULT NULL;
ALTER TABLE ocr_menus ADD FOREIGN KEY (store_id) REFERENCES stores (store_id);
```

#### 新增 ocr_menu_translations 表
```sql
CREATE TABLE ocr_menu_translations (
    ocr_menu_translation_id BIGINT NOT NULL AUTO_INCREMENT,
    ocr_menu_item_id BIGINT NOT NULL,
    lang_code VARCHAR(10) NOT NULL,
    translated_name VARCHAR(100) COLLATE utf8mb4_bin NOT NULL,
    translated_description TEXT COLLATE utf8mb4_bin,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ocr_menu_translation_id),
    FOREIGN KEY (ocr_menu_item_id) REFERENCES ocr_menu_items (ocr_menu_item_id),
    FOREIGN KEY (lang_code) REFERENCES languages (line_lang_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='OCR菜單翻譯表'
```

### 3. 核心功能修改

#### OCR 菜單儲存邏輯增強
- 修改 `process_menu_ocr` 函數，包含 `store_id` 參數
- 修改 `save_ocr_menu_and_summary_to_database` 函數，支援 `store_id`
- 新增 OCR 菜單翻譯儲存邏輯

#### 翻譯機制增強
- 新增 `get_ocr_menu_translation_from_db` 函數：查詢 OCR 菜單翻譯
- 新增 `translate_ocr_menu_items_with_db_fallback` 函數：批量翻譯 OCR 菜單項目
- 優先使用資料庫翻譯，如果沒有則使用 AI 翻譯

#### OCR 菜單查詢增強
- 修改 `get_ocr_menu` 函數，使用新的翻譯機制
- 返回翻譯來源資訊（database/ai/original）

### 4. API 端點修改

#### POST /api/menu/process-ocr
- 現在會將 `store_id` 儲存到 `ocr_menus` 表
- 自動將翻譯結果儲存到 `ocr_menu_translations` 表

#### GET /api/menu/ocr/{ocr_menu_id}
- 使用新的翻譯機制
- 返回翻譯來源資訊

### 5. 資料庫修復腳本更新

- 更新 `app/api/routes.py` 中的 `/fix-database` 端點
- 更新 `create_missing_tables.py` 腳本
- 支援自動創建新的資料表結構

## 使用方式

### 1. 建立 OCR 菜單（包含 store_id）
```bash
POST /api/menu/process-ocr
Content-Type: multipart/form-data

{
  "image": [圖片檔案],
  "store_id": "123",  # 店家 ID
  "user_id": "U1234567890abcdef",  # LINE 用戶 ID
  "lang": "en"  # 目標語言
}
```

### 2. 查詢 OCR 菜單（包含翻譯）
```bash
GET /api/menu/ocr/123?lang=en
```

回應範例：
```json
{
  "success": true,
  "ocr_menu_id": 123,
  "store_name": "測試店家",
  "user_language": "en",
  "menu_items": [
    {
      "id": "ocr_123_456",
      "original_name": "測試菜名",
      "translated_name": "Test Dish Name",
      "price": 100,
      "translation_source": "database"
    }
  ]
}
```

## 測試

執行測試腳本驗證功能：
```bash
python test_ocr_enhancements.py
```

## 向後相容性

- 所有修改都保持向後相容性
- 現有的 OCR 菜單記錄不會受影響
- `store_id` 欄位可為 NULL，支援非合作店家
- 翻譯機制會自動 fallback 到 AI 翻譯

## 資料流程

1. **OCR 菜單上傳** → 儲存到 `ocr_menus` 表（包含 `store_id`）
2. **菜單項目儲存** → 儲存到 `ocr_menu_items` 表
3. **翻譯儲存** → 儲存到 `ocr_menu_translations` 表
4. **查詢時** → 優先使用資料庫翻譯，fallback 到 AI 翻譯

## 注意事項

1. 需要執行資料庫修復腳本來創建新的表結構
2. 翻譯資料會根據使用者語言設定自動儲存
3. 支援多語言翻譯，每個語言都有獨立的翻譯記錄
4. 翻譯來源會記錄在回應中，方便除錯和優化
