
# Cloud MySQL Schema Overview

## 1. 系統語系與菜單主檔

| 表 | 主要欄位 | 型別 & 約束 | 備註 |
| --- | --- | --- | --- |
| **languages** | `line_lang_code` | `varchar(10)` PK, NOT NULL | 語言代碼（zh-TW、en、ja…） |
|  | `translation_lang_code` | `varchar(5)` NOT NULL | 翻譯語言代碼 |
|  | `stt_lang_code` | `varchar(15)` NOT NULL | 語音辨識語言代碼 |
|  | `lang_name` | `varchar(50)` NOT NULL | 語言名稱 |
| **menus** | `menu_id` | `int(11)` PK | 菜單 ID |
|  | `store_id` | `int(11)` NOT NULL | 所屬店家 |
|  | `template_id` | `int(11)` NULL | VIP 模板 ID |
|  | `version` | `int(11)` NOT NULL DEFAULT 1 | 版本號 |
|  | `effective_date` | `datetime` NOT NULL | 生效日 |
|  | `created_at` | `datetime` DEFAULT CURRENT_TIMESTAMP | 建立時間 |
| **menu_crawls** | `crawl_id` | `bigint(20)` PK | 爬蟲紀錄 |
|  | `store_id` | `int(11)` NOT NULL | 店家 ID |
|  | `crawl_time` | `datetime` DEFAULT CURRENT_TIMESTAMP | 爬取時間 |
|  | `menu_version` | `int(11)` NULL | 菜單版本 |
|  | `menu_version_hash` | `varchar(64)` NULL | 版本雜湊 |
|  | `has_update` | `tinyint(1)` DEFAULT 0 | 是否更新 |
|  | `store_reviews_popular` | `json` NULL | 評論＋人氣菜色 |

## 2. 菜單明細與翻譯

| 表 | 主要欄位 | 型別 & 約束 | 備註 |
| --- | --- | --- | --- |
| **menu_items** | `menu_item_id` PK | `int(11)` | 菜單品項 |
|  | `menu_id` | `int(11)` NOT NULL | 對應菜單 |
|  | `item_name` | `varchar(100)` NOT NULL | 品項名稱（中文） |
|  | `price_big` | `int(11)` NULL | 大份價格 |
|  | `price_small` | `int(11)` NOT NULL | 小份價格 |
|  | `created_at` | `datetime` DEFAULT CURRENT_TIMESTAMP | 建立 |
| **menu_templates** | `template_id` PK | `int(11)` | 模板 |
|  | `template_name` | `varchar(100)` | 名稱 |
|  | `description` | `text` NULL | 說明 |
| **menu_translations** | `menu_translation_id` PK | `int(11)` | 多語描述 |
|  | `menu_item_id` | `int(11)` NOT NULL | 對應品項 |
|  | `lang_code` | `varchar(10)` NOT NULL | 語言 |
|  | `description` | `text` NULL | 介紹 |

## 3. OCR 菜單（非合作店家）

| 表 | 主要欄位 | 型別 & 約束 | 備註 |
| --- | --- | --- | --- |
| **ocr_menus** | `ocr_menu_id` PK | `bigint(20)` | OCR 菜單主檔 |
|  | `user_id` | `bigint(20)` NOT NULL | 上傳者 |
|  | `store_name` | `varchar(100)` NULL | 店名 |
|  | `upload_time` | `datetime` DEFAULT CURRENT_TIMESTAMP | 上傳 |
| **ocr_menu_items** | `ocr_menu_item_id` PK | `bigint(20)` | OCR 菜單品項 |
|  | `ocr_menu_id` | `bigint(20)` NOT NULL | 所屬 OCR 菜單 |
|  | `item_name` | `varchar(100)` NOT NULL | 名稱 |
|  | `price_big` | `int(11)` NULL | 大份價格 |
|  | `price_small` | `int(11)` NOT NULL | 小份價格 |
|  | `translated_desc` | `text` NULL | AI 翻譯介紹 |

## 4. 訂單主檔與明細

| 表 | 主要欄位 | 型別 & 約束 | 備註 |
| --- | --- | --- | --- |
| **orders** | `order_id` PK | `bigint(20)` | 訂單 ID |
|  | `user_id` | `bigint(20)` NOT NULL | 下單者 |
|  | `store_id` | `int(11)` NOT NULL | 店家 |
|  | `order_time` | `datetime` DEFAULT CURRENT_TIMESTAMP | 時間 |
|  | `total_amount` | `int(11)` NOT NULL DEFAULT 0 | 總金額 |
|  | `status` | `varchar(20)` DEFAULT 'pending' | 狀態 |
| **order_items** | `order_item_id` PK | `bigint(20)` | 品項明細 |
|  | `order_id` | `bigint(20)` NOT NULL | 所屬訂單 |
|  | `menu_item_id` | `bigint(20)` NULL | 對應菜單品項 |
|  | `quantity_small` | `int(11)` NOT NULL DEFAULT 0 | 數量 |
|  | `subtotal` | `int(11)` NOT NULL | 小計 |
|  | `created_at` | `datetime` DEFAULT CURRENT_TIMESTAMP | 建立時間 |
|  | `original_name` | `varchar(100)` NULL | 原始中文菜名（待新增） |
|  | `translated_name` | `varchar(100)` NULL | 翻譯菜名（待新增） |

## 5. 店家與多語介紹

| 表 | 主要欄位 | 型別 & 約束 | 備註 |
| --- | --- | --- | --- |
| **stores** | `store_id` PK | `int(11)` | 店家 ID |
|  | `store_name` | `varchar(100)` NOT NULL | 店名 |
|  | `partner_level` | `int(11)` NOT NULL DEFAULT 0 | 0=非合作, 1=合作, 2=VIP |
|  | `gps_lat` | `double` NULL | 店家緯度 |
|  | `gps_lng` | `double` NULL | 店家經度 |
|  | `place_id` | `varchar(255)` NULL | Google Place ID |
|  | `review_summary` | `text` NULL | 評論摘要 |
|  | `top_dish_1` | `varchar(100)` NULL | 熱門菜色1 |
|  | `top_dish_2` | `varchar(100)` NULL | 熱門菜色2 |
|  | `top_dish_3` | `varchar(100)` NULL | 熱門菜色3 |
|  | `top_dish_4` | `varchar(100)` NULL | 熱門菜色4 |
|  | `top_dish_5` | `varchar(100)` NULL | 熱門菜色5 |
|  | `main_photo_url` | `varchar(255)` NULL | 招牌照 |
|  | `created_at` | `datetime` DEFAULT CURRENT_TIMESTAMP | 建立 |
|  | `latitude` | `decimal(10,8)` NULL | 店家緯度（向後相容） |
|  | `longitude` | `decimal(11,8)` NULL | 店家經度（向後相容） |
| **store_translations** | `id` PK | `int(11)` | 多語介紹 |
|  | `store_id` | `int(11)` NOT NULL | 店家 |
|  | `language_code` | `varchar(10)` NOT NULL | 語言 |
|  | `description` | `text` NULL | 翻譯後的店家簡介 |
|  | `translated_summary` | `text` NULL | 翻譯後的評論摘要 |

## 6. 使用者與行為追蹤

| 表 | 主要欄位 | 型別 & 約束 | 備註 |
| --- | --- | --- | --- |
| **users** | `user_id` PK | `bigint(20)` | 使用者 |
|  | `line_user_id` | `varchar(100)` UNIQUE NOT NULL | LINE UID |
|  | `preferred_lang` | `varchar(10)` NOT NULL | 喜好語系 |
|  | `created_at` | `datetime` DEFAULT CURRENT_TIMESTAMP | 建立 |
|  | `state` | `varchar(50)` DEFAULT 'normal' | 狀態 |
| **user_actions** | `action_id` PK | `bigint(20)` | 行為紀錄 |
|  | `user_id` | `bigint(20)` NOT NULL | 使用者 |
|  | `action_type` | `varchar(50)` NOT NULL | 類型（點餐／播放語音…） |
|  | `action_time` | `datetime` DEFAULT CURRENT_TIMESTAMP | 發生時間 |
|  | `details` | `json` NULL | 行為細節 |

## 7. 語音檔案

| 表 | 主要欄位 | 型別 & 約束 | 備註 |
| --- | --- | --- | --- |
| **voice_files** | `voice_file_id` PK | `bigint(20)` | 語音檔案 ID |
|  | `order_id` | `bigint(20)` NOT NULL | 對應訂單 |
|  | `file_url` | `varchar(500)` NOT NULL | 語音檔案 URL |
|  | `file_type` | `varchar(10)` DEFAULT 'mp3' | 檔案類型 |
|  | `speech_rate` | `float` DEFAULT 1.0 | 語速倍率 |
|  | `created_at` | `datetime` DEFAULT CURRENT_TIMESTAMP | 建立時間 |

## 重要更新說明

### 修正的欄位名稱
1. **orders 表**: `order_date` → `order_time`
2. **stores 表**: 新增 `partner_level`, `gps_lat`, `gps_lng`, `place_id` 等欄位
3. **languages 表**: 主鍵改為 `line_lang_code`

### 已新增的欄位 ✅
1. **order_items 表**: 
   - `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP ✅
   - `original_name` VARCHAR(100) NULL ✅
   - `translated_name` VARCHAR(100) NULL ✅

### 實際資料庫結構差異
- 實際資料庫結構與原始 schema 文件有部分差異
- 已根據測試結果更新欄位名稱和類型
- 建議執行資料庫遷移以新增雙語欄位

### 實際資料庫中存在的額外表格
1. **account** - 帳戶管理表格
2. **crawl_logs** - 爬蟲日誌表格
3. **food_type_data** - 食物類型資料表格
4. **gemini_processing** - Gemini AI 處理表格
5. **reviews** - 評論資料表格

### 欄位類型差異
- 實際資料庫中多數 INT 欄位使用 INTEGER 類型
- TEXT 欄位包含 COLLATE "utf8mb4_bin" 設定
- 部分 BIGINT 欄位在 schema 中定義為 INT(11)

## 8. 實際資料庫中的額外表格

| 表 | 主要欄位 | 型別 & 約束 | 備註 |
| --- | --- | --- | --- |
| **account** | `id` | `int(11)` PK | 帳戶管理 |
|  | `username` | `varchar(255)` | 使用者名稱 |
|  | `password` | `varchar(255)` | 密碼 |
|  | `email` | `varchar(255)` | 電子郵件 |
|  | `created_at` | `datetime` | 建立時間 |
| **crawl_logs** | `id` | `int(11)` PK | 爬蟲日誌 |
|  | `store_id` | `int(11)` | 店家 ID |
|  | `crawl_time` | `datetime` | 爬取時間 |
|  | `status` | `varchar(50)` | 狀態 |
|  | `details` | `text` | 詳細資訊 |
| **food_type_data** | `id` | `int(11)` PK | 食物類型資料 |
|  | `food_type` | `varchar(100)` | 食物類型 |
|  | `description` | `text` | 描述 |
|  | `created_at` | `datetime` | 建立時間 |
| **gemini_processing** | `id` | `int(11)` PK | Gemini AI 處理 |
|  | `user_id` | `bigint(20)` | 使用者 ID |
|  | `input_text` | `text` | 輸入文字 |
|  | `output_text` | `text` | 輸出文字 |
|  | `processing_time` | `datetime` | 處理時間 |
|  | `status` | `varchar(50)` | 狀態 |
| **reviews** | `id` | `int(11)` PK | 評論資料 |
|  | `store_id` | `int(11)` | 店家 ID |
|  | `user_id` | `bigint(20)` | 使用者 ID |
|  | `rating` | `int(11)` | 評分 |
|  | `comment` | `text` | 評論內容 |
|  | `created_at` | `datetime` | 建立時間 |

## 9. 資料庫遷移建議

### 已執行的資料庫遷移 ✅
```sql
-- order_items 表格新增欄位（已執行）
ALTER TABLE order_items ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE order_items ADD COLUMN original_name VARCHAR(100) NULL;
ALTER TABLE order_items ADD COLUMN translated_name VARCHAR(100) NULL;
```

### 欄位類型統一建議
- 將 INTEGER 類型統一為 INT(11) 以符合 schema 文件
- 保持 TEXT 欄位的 COLLATE 設定以支援多語言
- 確認 BIGINT 欄位的使用場景是否正確
