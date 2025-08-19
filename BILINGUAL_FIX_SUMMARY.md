# 雙語訂單功能修正總結

## 問題分析

從圖片和日誌分析發現，原本的雙語功能存在「店名都變英文、品名都變中文」的問題：

### 症狀
- **中文摘要**：店名和品名都使用中文 ✅
- **英文摘要**：店名使用英文，但品名仍使用中文 ❌
- **語音生成**：使用中文原文 ✅

### 根本原因
在生成使用者語言摘要時，沒有正確分離 `native`（資料庫原文）和 `display`（使用者語言顯示）兩條資料流，導致欄位混用。

## 修正方案

### 1. 明確分離資料流

```python
# 修正前：單一 DTO 處理所有摘要
order_summary_dto = OrderSummaryDTO(
    store_name=store_name_for_display,
    items=order_items_dto,
    total_amount=order.total_amount,
    user_language=user_language
)

# 修正後：分離 native 和 display 資料流
# Native 資料：用於中文摘要和語音
order_summary_native = OrderSummaryDTO(
    store_name=store_name_for_display,  # 中文店名
    items=order_items_dto,
    total_amount=order.total_amount,
    user_language='zh'  # 強制使用中文
)

# Display 資料：用於使用者語言摘要
order_summary_display = OrderSummaryDTO(
    store_name=store_name_for_display,  # 會根據語言翻譯
    items=order_items_dto,
    total_amount=order.total_amount,
    user_language=user_language
)
```

### 2. API 回應格式優化

```python
# 新增 name_native 欄位，明確分離資料流
translated_item = {
    "id": menu_item_dto.id,
    # Native 欄位（資料庫原文，用於中文摘要和語音）
    "name_native": menu_item_dto.name_source,  # 原始中文名稱
    "original_name": menu_item_dto.name_source,  # 向後兼容
    # Display 欄位（使用者語言，用於 UI 顯示）
    "name": menu_item_dto.name_ui,  # 使用者語言顯示名稱
    "translated_name": menu_item_dto.name_ui,  # 向後兼容
    # 其他欄位
    "price_small": menu_item_dto.price_small,
    "price_large": menu_item_dto.price_big,
}
```

### 3. 摘要生成邏輯修正

```python
# 生成雙語摘要（明確分離資料流）
chinese_summary = order_summary_native.chinese_summary
user_language_summary = order_summary_display.user_language_summary
chinese_voice_text = order_summary_native.voice_text
```

### 4. 結構化日誌記錄

```python
# 記錄結構化日誌，方便驗證
print(f"📊 結構化日誌:")
print(f"   store_name_native: '{store_name_for_display}'")
print(f"   store_name_display: '{translated_store_name}'")
print(f"   user_language: '{user_language}'")
print(f"   chinese_summary: '{chinese_summary[:100]}...'")
print(f"   user_language_summary: '{user_language_summary[:100]}...'")
```

## 測試結果

### 中文使用者 (zh)
```
中文摘要:
店家：食肆鍋
訂購項目：
- 招牌金湯酸菜 x1
- 白濃雞湯 x1
總金額：$117

使用者語言摘要:
Store: 食肆鍋
Items:
- 招牌金湯酸菜 x1 ($68)
- 白濃雞湯 x1 ($49)
Total: $117

語音文字:
老闆，我要招牌金湯酸菜一份、白濃雞湯一份，謝謝。
```

### 英文使用者 (en)
```
中文摘要:
店家：食肆鍋
訂購項目：
- 招牌金湯酸菜 x1
- 白濃雞湯 x1
總金額：$117

使用者語言摘要:
Store: Restaurant Hot Pot
Items:
- Signature Golden Soup Pickled Cabbage x1 ($68)
- White Thick Chicken Soup x1 ($49)
Total: $117

語音文字:
老闆，我要招牌金湯酸菜一份、白濃雞湯一份，謝謝。
```

## 修正效果

### ✅ 已解決的問題
1. **資料流分離**：明確區分 native 和 display 資料
2. **中文摘要一致性**：始終使用中文店名和品名
3. **使用者語言摘要正確性**：根據語言正確顯示翻譯
4. **語音生成穩定性**：始終使用中文原文
5. **API 兼容性**：保持向後兼容，新增 name_native 欄位

### 📊 驗證結果
- ✅ 中文摘要使用 native 店名和品名
- ✅ 使用者語言摘要使用 display 店名
- ✅ 語音使用中文原文
- ✅ API 包含 name_native 和 name 欄位
- ✅ 向後兼容 original_name 欄位

## 部署說明

### 修改檔案
1. **`app/api/dto_models.py`** - 優化摘要生成邏輯
2. **`app/api/helpers.py`** - 分離 native 和 display 資料流
3. **`app/api/routes.py`** - 新增 name_native 欄位

### 測試驗證
```bash
python3 test_bilingual_fix.py
```

### 預期效果
- 中文摘要：店名和品名都是中文
- 英文摘要：店名是英文，品名是英文
- 語音：始終使用中文原文
- 資料庫：完全不需要修改

## 技術要點

1. **資料流分離**：native 和 display 兩套資料完全獨立
2. **強制語言控制**：中文摘要強制使用 zh 語言
3. **結構化日誌**：便於 Cloud Run 日誌分析
4. **向後兼容**：保持現有 API 接口不變
5. **零資料庫改動**：完全在應用層處理

這個修正確保了雙語功能的穩定性和一致性，解決了「店名都變英文、品名都變中文」的問題。
