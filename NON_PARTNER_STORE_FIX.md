# 非合作店家中文摘要菜品名稱修正總結

## 🎯 問題描述

從截圖分析發現，非合作店家的中文摘要訂單中，菜品名稱沒有中文：

### 症狀
- **中文摘要**：顯示英文菜品名稱（如 "Seafood Tofu Hot Pot"）
- **英文摘要**：正常顯示英文菜品名稱
- **語音生成**：使用英文菜品名稱，不符合中文語音需求

### 影響範圍
- 非合作店家的訂單摘要
- 中文語音生成
- 用戶體驗（中文用戶看到英文菜品名）

## 🔍 根本原因分析

### 1. 資料庫查詢錯誤
```python
# 錯誤的查詢
result = db.session.execute(text("""
    SELECT description 
    FROM menu_item_translations  # ❌ 錯誤的表格名稱
    WHERE menu_item_id = :menu_item_id AND language_code = :language_code  # ❌ 錯誤的欄位名稱
"""))
```

**實際資料庫結構**：
- 表格名稱：`menu_translations`（不是 `menu_item_translations`）
- 欄位名稱：`lang_code`（不是 `language_code`）

### 2. 缺少翻譯資料
從資料庫查詢發現：
```sql
SELECT * FROM menu_translations WHERE menu_item_id IN (263, 264, 191) AND lang_code = 'zh';
-- 結果：空（沒有中文翻譯資料）
```

### 3. 缺少英文到中文的翻譯邏輯
當沒有翻譯資料時，系統直接使用原始英文名稱，沒有進行翻譯。

## 🔧 修正方案

### 1. 修正資料庫查詢

**修正前**：
```python
result = db.session.execute(text("""
    SELECT description 
    FROM menu_item_translations 
    WHERE menu_item_id = :menu_item_id AND language_code = :language_code
"""))
```

**修正後**：
```python
result = db.session.execute(text("""
    SELECT description 
    FROM menu_translations 
    WHERE menu_item_id = :menu_item_id AND lang_code = :language_code
"""))
```

### 2. 添加中日韓字符檢測

```python
from .translation_service import contains_cjk

if contains_cjk(menu_item.item_name):
    # 原始名稱是中文
    chinese_name = menu_item.item_name
    translated_name = menu_item.item_name
    print(f"✅ 原始名稱是中文: '{chinese_name}'")
else:
    # 原始名稱是英文，需要翻譯成中文
    chinese_name = translate_text_with_fallback(menu_item.item_name, 'zh')
    translated_name = menu_item.item_name
    print(f"🔄 翻譯英文名稱: '{translated_name}' -> '{chinese_name}'")
```

### 3. 完善翻譯邏輯

```python
translation = result.fetchone()
if translation and translation[0]:
    chinese_name = translation[0]  # 使用翻譯的中文名稱
    translated_name = menu_item.item_name  # 使用原始英文名稱
    print(f"✅ 找到翻譯: '{translated_name}' -> '{chinese_name}'")
else:
    # 如果沒有翻譯資料，需要判斷原始名稱是否為中文
    if contains_cjk(menu_item.item_name):
        # 原始名稱是中文
        chinese_name = menu_item.item_name
        translated_name = menu_item.item_name
    else:
        # 原始名稱是英文，需要翻譯成中文
        chinese_name = translate_text_with_fallback(menu_item.item_name, 'zh')
        translated_name = menu_item.item_name
```

## 📊 修正效果

### 修正前
```
中文摘要：
店家：葉來香50年古早味麵飯美食
訂購項目：
- Seafood Tofu Hot Pot x1
- Kimchi Hot Pot x1
- Satay Fish Head Hot Pot x1
總金額：$500
```

### 修正後
```
中文摘要：
店家：葉來香50年古早味麵飯美食
訂購項目：
- 海鮮豆腐火鍋 x1
- 泡菜火鍋 x1
- 沙爹魚頭火鍋 x1
總金額：$500
```

## ✅ 驗證結果

### 測試腳本：`test_non_partner_fix.py`

**測試結果**：
- ✅ 中日韓字符檢測：通過
- ✅ 翻譯邏輯：通過
- ✅ 中文摘要生成：通過
- ✅ 資料庫查詢：通過

### 具體驗證項目

1. **中日韓字符檢測**：
   - `'Seafood Tofu Hot Pot'` -> CJK: False
   - `'海鮮豆腐火鍋'` -> CJK: True
   - `'Mixed 火鍋 Hot Pot'` -> CJK: True

2. **翻譯邏輯**：
   - 有翻譯資料：使用資料庫翻譯
   - 無翻譯資料 + 英文名稱：自動翻譯成中文
   - 無翻譯資料 + 中文名稱：直接使用

3. **中文摘要生成**：
   - 使用中文店名：✅
   - 使用中文菜品名：✅
   - 沒有英文菜品名：✅

## 🎉 最終成果

### 完全解決的問題
1. **✅ 資料庫查詢錯誤**：修正表格名稱和欄位名稱
2. **✅ 缺少翻譯邏輯**：添加英文到中文的翻譯
3. **✅ 中日韓字符檢測**：正確識別中文菜品名稱
4. **✅ 中文摘要菜品名**：確保使用中文菜品名稱
5. **✅ 語音生成**：使用中文菜品名稱生成語音

### 技術特色
- **智能檢測**：自動檢測菜品名稱是否為中文
- **自動翻譯**：英文菜品名稱自動翻譯成中文
- **資料庫兼容**：使用正確的表格和欄位名稱
- **向後兼容**：不影響現有功能

## 🚀 部署建議

1. **立即部署**：修正已完成，可以立即部署到 Cloud Run
2. **測試驗證**：部署後測試非合作店家的訂單流程
3. **監控日誌**：觀察翻譯功能和中文摘要生成

## 📋 修正檔案

### 修改檔案
- `app/api/helpers.py` - 修正資料庫查詢和翻譯邏輯

### 新增檔案
- `test_non_partner_fix.py` - 測試腳本
- `NON_PARTNER_STORE_FIX.md` - 修正總結文檔

---

**🎊 恭喜！非合作店家中文摘要菜品名稱修正完成！**

現在非合作店家的訂單摘要將正確顯示：
- 中文摘要使用中文菜品名稱
- 英文摘要使用英文菜品名稱
- 語音生成使用中文菜品名稱
- 完全符合中文用戶的使用需求
