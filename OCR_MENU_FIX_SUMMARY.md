# OCR 菜單項目處理修正總結

## 問題分析

### 1. 錯誤訊息
```
⚠️ 寫入訂單摘要失敗: cannot access local variable 'db' where it is not associated with a value
```

### 2. 根本原因
- 在 `create_complete_order_confirmation` 函數中，`db` 變數沒有正確導入
- 程式碼中缺少對 OCR 菜單項目的處理邏輯
- 非合作店家的 OCR 菜單項目應該從 `ocr_menu_items` 和 `ocr_menu_translations` 表獲取資料

## 資料庫結構

### OCR 菜單相關表格
1. **`ocr_menu_items`**：
   - `item_name`：原始中文菜名（OCR 辨識結果）
   - `translated_desc`：翻譯後的菜名（使用者設定語言）

2. **`ocr_menu_translations`**：
   - `menu_item_id`：對應的 OCR 菜單項目 ID
   - `lang_code`：語言代碼
   - `description`：翻譯內容

## 修正內容

### 1. 修正 db import 問題
```python
# 在查詢翻譯資料前正確導入 db
from sqlalchemy import text
from app.models import db
```

### 2. 新增 OCR 菜單項目處理邏輯
```python
# 檢查是否為 OCR 菜單項目
if item.temp_item_id and item.temp_item_id.startswith('ocr_'):
    # OCR 菜單項目處理
    ocr_menu_item_id = int(item.temp_item_id.replace('ocr_', ''))
    
    # 查詢 OCR 菜單項目
    result = db.session.execute(text("""
        SELECT item_name, translated_desc 
        FROM ocr_menu_items 
        WHERE ocr_menu_item_id = :ocr_menu_item_id
    """), {"ocr_menu_item_id": ocr_menu_item_id})
    
    ocr_item = result.fetchone()
    if ocr_item:
        chinese_name = ocr_item[0]  # 原始中文菜名
        translated_name = ocr_item[1] if ocr_item[1] else ocr_item[0]  # 翻譯後的菜名
```

### 3. 修正縮排問題
- 修正了 `else` 語句的縮排錯誤

## 預期效果

### 修正後的行為
1. **中文摘要**：使用 `ocr_menu_items.item_name`（原始中文菜名）
2. **使用者語言摘要**：使用 `ocr_menu_items.translated_desc`（翻譯後的菜名）
3. **語音生成**：使用中文菜名進行語音合成
4. **錯誤處理**：正確處理 `db` 變數，避免 `cannot access local variable` 錯誤

### 資料流程
```
OCR 辨識 → ocr_menu_items.item_name (中文)
    ↓
翻譯處理 → ocr_menu_items.translated_desc (使用者語言)
    ↓
訂單處理 → 根據 temp_item_id 判斷是否為 OCR 項目
    ↓
摘要生成 → 中文摘要用中文菜名，使用者語言摘要用翻譯菜名
```

## 測試驗證

### 測試案例
1. **非合作店家 OCR 菜單訂單**：
   - 確認中文摘要顯示中文菜名
   - 確認使用者語言摘要顯示翻譯菜名
   - 確認語音使用中文菜名

2. **合作店家一般菜單訂單**：
   - 確認現有邏輯不受影響
   - 確認翻譯功能正常運作

## 部署狀態

✅ **已修正並部署到 Cloud Run**
- 修正了 `db` import 問題
- 新增了 OCR 菜單項目處理邏輯
- 修正了縮排錯誤
- 已推送到 GitHub 並觸發自動部署

## 後續建議

1. **監控日誌**：觀察修正後的日誌，確認錯誤已解決
2. **功能測試**：測試非合作店家的 OCR 菜單訂單
3. **效能優化**：考慮對 OCR 菜單查詢進行快取優化
