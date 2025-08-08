
# Cloud MySQL Schema Overview

## 1. 系統語系與菜單主檔

| 表 | 主要欄位 | 型別 & 約束 | 備註 |
| --- | --- | --- | --- |
| **languages** | `lang_code` | `varchar(5)` PK, NOT NULL | 語言代碼（en、zh、jp…） |
|  | `lang_name` | `varchar(50)` NOT NULL | 語言名稱 |
| **menus** | `menu_id` | `bigint(20)` PK | 菜單 ID |
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
| **menu_items** | `menu_item_id` PK | `bigint(20)` | 菜單品項 |
|  | `menu_id` | `bigint(20)` NOT NULL | 對應菜單 |
|  | `item_name` | `varchar(100)` NOT NULL | 品項名稱 |
|  | `price_big` / `price_small` | `int(11)` | 大／小份價 |
|  | `created_at` | `datetime` DEFAULT CURRENT_TIMESTAMP | 建立 |
| **menu_templates** | `template_id` PK | `int(11)` | 模板 |
|  | `template_name` | `varchar(100)` | 名稱 |
|  | `description` | `text` NULL | 說明 |
| **menu_translations** | `menu_translation_id` PK | `bigint(20)` | 多語描述 |
|  | `menu_item_id` | `bigint(20)` | 對應品項 |
|  | `lang_code` | `varchar(5)` | 語言 |
|  | `description` | `text` NULL | 介紹 |

## 3. OCR 菜單（非合作店家）

| 表 | 主要欄位 | 型別 & 約束 | 備註 |
| --- | --- | --- | --- |
| **ocr_menus** | `ocr_menu_id` PK | `bigint(20)` | OCR 菜單主檔 |
|  | `user_id` | `bigint(20)` NOT NULL | 上傳者 |
|  | `store_name` | `varchar(100)` NULL | 店名 |
|  | `upload_time` | `datetime` DEFAULT CURRENT_TIMESTAMP | 上傳 |
| **ocr_menu_items** | `ocr_menu_item_id` PK | `bigint(20)` | OCR 菜單品項 |
|  | `ocr_menu_id` | `bigint(20)` | 所屬 OCR 菜單 |
|  | `item_name` | `varchar(100)` | 名稱 |
|  | `price_big` / `price_small` | `int(11)` | 價格 |
|  | `translated_desc` | `text` NULL | AI 翻譯介紹 |

## 4. 訂單主檔與明細

| 表 | 主要欄位 | 型別 & 約束 | 備註 |
| --- | --- | --- | --- |
| **orders** | `order_id` PK | `bigint(20)` | 訂單 ID |
|  | `user_id` | `bigint(20)` | 下單者 |
|  | `store_id` | `int(11)` | 店家 |
|  | `order_time` | `datetime` DEFAULT CURRENT_TIMESTAMP | 時間 |
|  | `language_used` | `varchar(5)` DEFAULT 'zh' | 系統語系 |
|  | `total_amount` | `int(11)` DEFAULT 0 | 總金額 |
| **order_items** | `order_item_id` PK | `bigint(20)` | 品項明細 |
|  | `order_id` | `bigint(20)` | 所屬訂單 |
|  | `menu_item_id` | `bigint(20)` | 對應菜單品項 |
|  | `quantity_big` / `quantity_small` | `int(11)` DEFAULT 0 | 數量 |
|  | `price_big` / `price_small` | `int(11)` | 單價 |
|  | `subtotal` | `int(11)` | 小計（計算欄） |

## 5. 店家與多語介紹

| 表 | 主要欄位 | 型別 & 約束 | 備註 |
| --- | --- | --- | --- |
| **stores** | `store_id` PK | `int(11)` | 店家 ID |
|  | `store_name` | `varchar(100)` | 店名 |
|  | `partner_level` | `tinyint(4)` DEFAULT 0 | 0 = 非合作／1 = 合作／2 = VIP |
|  | `gps_lat` / `gps_lng` | `double` NULL | 座標 |
|  | `place_id` | `varchar(100)` NULL | Google Place ID |
|  | `review_summary` | `text` NULL | 評論摘要 |
|  | `top_dish_1 ~ 5` | `varchar(100)` NULL | 熱門菜 |
|  | `main_photo_url` | `varchar(255)` NULL | 招牌照 |
|  | `created_at` | `datetime` DEFAULT CURRENT_TIMESTAMP | 建立 |
| **store_translations** | `store_translation_id` PK | `int(11)` | 多語介紹 |
|  | `store_id` | `int(11)` | 店家 |
|  | `lang_code` | `varchar(5)` | 語言 |
|  | `description` / `reviews` | `text` NULL | 介紹／評論 |

## 6. 使用者與行為追蹤

| 表 | 主要欄位 | 型別 & 約束 | 備註 |
| --- | --- | --- | --- |
| **users** | `user_id` PK | `bigint(20)` | 使用者 |
|  | `line_user_id` | `varchar(100)` | LINE UID |
|  | `preferred_lang` | `varchar(5)` | 喜好語系 |
|  | `created_at` | `datetime` DEFAULT CURRENT_TIMESTAMP | 建立 |
| **user_actions** | `action_id` PK | `bigint(20)` | 行為紀錄 |
|  | `user_id` | `bigint(20)` | 使用者 |
|  | `action_type` | `varchar(50)` | 類型（點餐／播放語音…） |
|  | `action_time` | `datetime` DEFAULT CURRENT_TIMESTAMP | 發生時間 |
|  | `details` | `json` NULL | 行為細節 |
