# 合作/非合作店家點餐流程分析

## 店家分類

### 合作店家 (partner_level = 1)
- 有預先建立的菜單資料
- 使用 `menu_items` 表儲存菜品資訊
- 有完整的翻譯資料在 `menu_translations` 表

### 非合作店家 (partner_level = 0)
- 沒有預先建立的菜單
- 使用 OCR 辨識菜單
- 菜單資料儲存在 `ocr_menus` 和 `ocr_menu_items` 表

## 資料庫結構分析

### 核心表格

#### 1. stores 表
```sql
store_id | store_name | partner_level
---------|------------|---------------
2        | 預設店家   | 0 (非合作)
4        | 食肆鍋     | 1 (合作)
```

#### 2. orders 表
```sql
order_id | user_id | store_id | total_amount | status
---------|---------|----------|--------------|--------
261      | 123     | 59       | 2000         | pending
265      | 124     | 4        | 117          | pending
```

#### 3. order_items 表
```sql
order_item_id | order_id | menu_item_id | temp_item_id | temp_item_name | is_temp_item
--------------|----------|--------------|--------------|----------------|-------------
614           | 261      | 268          | NULL         | NULL           | 0
635           | 265      | 122          | NULL         | NULL           | 0
```

### 菜單資料表格

#### 合作店家：menu_items 表
```sql
menu_item_id | menu_id | item_name           | price_small
-------------|---------|-------------------|------------
268          | 10      | Stinky Tofu Hot Pot| 160
122          | 5       | 招牌金湯酸菜       | 68
```

#### 非合作店家：ocr_menu_items 表
```sql
ocr_menu_item_id | ocr_menu_id | item_name | translated_desc
-----------------|-------------|-----------|----------------
525              | 43          | 爆冰濃縮   | Super Ice Espresso
526              | 43          | 曼巴黑咖啡 | Special Coffee
```

## 點餐流程分析

### 合作店家點餐流程

#### 1. 前端流程
```
用戶選擇合作店家 → 載入預設菜單 → 選擇菜品 → 提交訂單
```

#### 2. API 端點
- **菜單載入**: `GET /api/menu/{store_id}`
- **訂單建立**: `POST /api/orders`

#### 3. 資料庫互動
```python
# 1. 查詢店家資訊
store = Store.query.get(store_id)
# partner_level = 1

# 2. 載入菜單項目
menu_items = MenuItem.query.filter_by(menu_id=store.menu_id).all()

# 3. 建立訂單
order = Order(user_id=user_id, store_id=store_id, total_amount=total)
db.session.add(order)

# 4. 建立訂單項目
for item in items:
    order_item = OrderItem(
        order_id=order.order_id,
        menu_item_id=item.menu_item_id,  # 使用預設菜單ID
        quantity_small=item.quantity,
        subtotal=item.subtotal
    )
    db.session.add(order_item)
```

#### 4. 資料流向
```
menu_items → order_items.menu_item_id → 訂單處理
```

### 非合作店家點餐流程

#### 1. 前端流程
```
用戶選擇非合作店家 → 上傳菜單圖片 → OCR辨識 → 選擇菜品 → 提交訂單
```

#### 2. API 端點
- **OCR處理**: `POST /api/menu/process-ocr`
- **OCR菜單載入**: `GET /api/menu/ocr/{ocr_menu_id}`
- **OCR訂單建立**: `POST /api/orders/ocr`

#### 3. 資料庫互動
```python
# 1. OCR處理並儲存
ocr_menu = OCRMenu(user_id=user_id, store_id=store_id, store_name=store_name)
db.session.add(ocr_menu)

# 2. 儲存OCR菜單項目
for item in ocr_items:
    ocr_menu_item = OCRMenuItem(
        ocr_menu_id=ocr_menu.ocr_menu_id,
        item_name=item.original_name,      # 中文菜名
        translated_desc=item.translated_name,  # 翻譯菜名
        price_small=item.price
    )
    db.session.add(ocr_menu_item)

# 3. 建立訂單
order = Order(user_id=user_id, store_id=store_id, total_amount=total)
db.session.add(order)

# 4. 建立訂單項目（使用temp_item_id）
for item in items:
    order_item = OrderItem(
        order_id=order.order_id,
        temp_item_id=f"ocr_{item.ocr_menu_item_id}",  # 標識為OCR項目
        temp_item_name=item.item_name,
        temp_item_price=item.price_small,
        is_temp_item=1
    )
    db.session.add(order_item)
```

#### 4. 資料流向
```
OCR辨識 → ocr_menu_items → order_items.temp_item_id → 訂單處理
```

## 關鍵差異分析

### 1. 菜單資料來源
| 項目 | 合作店家 | 非合作店家 |
|------|----------|------------|
| 菜單來源 | 預設菜單 | OCR辨識 |
| 資料表 | menu_items | ocr_menu_items |
| 菜品ID | menu_item_id | ocr_menu_item_id |

### 2. 訂單項目標識
| 項目 | 合作店家 | 非合作店家 |
|------|----------|------------|
| 主要ID | menu_item_id | temp_item_id |
| 格式 | 整數ID | "ocr_數字ID" |
| 標識欄位 | is_temp_item=0 | is_temp_item=1 |

### 3. 翻譯資料
| 項目 | 合作店家 | 非合作店家 |
|------|----------|------------|
| 翻譯表 | menu_translations | ocr_menu_items.translated_desc |
| 原始名稱 | menu_items.item_name | ocr_menu_items.item_name |
| 翻譯名稱 | menu_translations.description | ocr_menu_items.translated_desc |

## 訂單處理邏輯

### 合作店家訂單處理
```python
# 在 create_complete_order_confirmation 中
for item in order.items:
    if item.menu_item_id:  # 合作店家
        menu_item = MenuItem.query.get(item.menu_item_id)
        chinese_name = menu_item.item_name  # 或從翻譯表查詢
        translated_name = get_translation(menu_item.menu_item_id, user_language)
```

### 非合作店家訂單處理
```python
# 在 create_complete_order_confirmation 中
for item in order.items:
    if item.temp_item_id and item.temp_item_id.startswith('ocr_'):  # OCR項目
        ocr_menu_item_id = int(item.temp_item_id.replace('ocr_', ''))
        ocr_item = OCRMenuItem.query.get(ocr_menu_item_id)
        chinese_name = ocr_item.item_name
        translated_name = ocr_item.translated_desc
```

## 問題分析

### 當前問題
1. **非合作店家訂單 261**：
   - 使用 `menu_item_id` 而不是 `temp_item_id`
   - 菜品名稱都是英文（如 "Stinky Tofu Hot Pot"）
   - 缺少中文翻譯資料

2. **資料不一致**：
   - 非合作店家應該使用 OCR 菜單
   - 但實際訂單使用的是預設菜單項目

### 解決方案
1. **修正訂單處理邏輯**：
   - 正確識別 OCR 菜單項目
   - 從 `ocr_menu_items` 表獲取中文菜名

2. **資料一致性**：
   - 確保非合作店家使用 OCR 流程
   - 或為現有菜品添加中文翻譯

## 建議

1. **短期修正**：修正訂單處理邏輯，正確處理 OCR 菜單項目
2. **長期改善**：統一資料流程，確保非合作店家使用 OCR 流程
3. **資料清理**：為現有英文菜品添加中文翻譯資料
