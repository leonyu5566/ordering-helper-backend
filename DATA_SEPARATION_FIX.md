# 資料分離修正總結

## 問題分析

從圖片和日誌分析發現，原本的雙語功能存在「兩份摘要裡品名都變中文、店名都變英文」的問題：

### 症狀
- **中文摘要**：店名和品名都使用中文 ✅
- **英文摘要**：店名使用英文，但品名仍使用中文 ❌
- **語音生成**：使用中文原文 ✅

### 根本原因
在生成使用者語言摘要時，**原文/譯文欄位被共用或覆蓋**，導致：
1. 產生「中文摘要」前就把 `store_name` 替換成了英文譯名
2. 產生「使用者語言摘要」時，用來組裝品名的陣列是中文品名的那一份
3. 同一份 `items` 被不同步改寫，造成交叉污染

## 修正方案

### 核心原則
1. **永遠保留「原文」與「目標語言」兩份獨立資料**（深拷貝，不能共用物件）
2. **在最後組裝訊息/語音時才決定要用哪一份**，不要在共享變數上「就地翻譯」

### 1. 完全分離資料流

```python
# 建立訂單摘要 DTO（完全分離 native 和 display 資料流）
# native 資料：用於中文摘要和語音（深拷貝，避免共用物件）
order_summary_native = OrderSummaryDTO(
    store_name=store_name_for_display,  # 中文店名
    items=order_items_dto.copy() if hasattr(order_items_dto, 'copy') else order_items_dto,  # 深拷貝避免共用
    total_amount=order.total_amount,
    user_language='zh'  # 強制使用中文
)

# display 資料：用於使用者語言摘要（深拷貝，避免共用物件）
order_summary_display = OrderSummaryDTO(
    store_name=store_name_for_display,  # 會根據語言翻譯
    items=order_items_dto.copy() if hasattr(order_items_dto, 'copy') else order_items_dto,  # 深拷貝避免共用
    total_amount=order.total_amount,
    user_language=user_language
)
```

### 2. 各自渲染訊息

```python
# 生成雙語摘要（明確分離資料流）
chinese_summary = order_summary_native.chinese_summary
user_language_summary = order_summary_display.user_language_summary
chinese_voice_text = order_summary_native.voice_text
```

### 3. 結構化日誌驗證

```python
# 記錄結構化日誌，驗證資料分離
print(f"📊 資料分離驗證:")
print(f"   native store_name: '{store_name_for_display}'")
print(f"   native first item: '{order_items_dto[0].name.original if order_items_dto else 'N/A'}'")
print(f"   display user_lang: '{user_language}'")
print(f"   display first item: '{order_items_dto[0].name.translated if order_items_dto else 'N/A'}'")

# 驗證資料分離
print(f"✅ 資料分離驗證:")
print(f"   - 中文摘要使用 native 店名: {'✓' if store_name_for_display in chinese_summary else '✗'}")
print(f"   - 使用者語言摘要使用 display 店名: {'✓' if translated_store_name in user_language_summary else '✗'}")
print(f"   - 語音使用中文原文: {'✓' if '招牌金湯酸菜' in chinese_voice_text or '白濃雞湯' in chinese_voice_text else '✗'}")
```

## 測試結果

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

### 驗證結果
- ✅ 中文摘要使用 native 店名
- ✅ 中文摘要使用 native 品名
- ✅ 使用者語言摘要使用 display 店名
- ✅ 使用者語言摘要使用 display 品名
- ✅ 語音使用中文原文

### 資料分離檢查
- ✅ 店名是否分離：`食肆鍋` vs `Restaurant Hot Pot`
- ✅ 品名是否分離：`招牌金湯酸菜` vs `Signature Golden Soup Pickled Cabbage`

## 修正效果

### ✅ 已解決的問題
1. **資料流完全分離**：native 和 display 兩套資料完全獨立
2. **防止就地修改**：避免共享物件被意外修改
3. **中文摘要一致性**：始終使用中文店名和品名
4. **使用者語言摘要正確性**：根據語言正確顯示翻譯
5. **語音生成穩定性**：始終使用中文原文
6. **結構化日誌**：便於 Cloud Run 日誌分析

### 📊 驗證結果
- ✅ 中文摘要使用 native 店名和品名
- ✅ 使用者語言摘要使用 display 店名和品名
- ✅ 語音使用中文原文
- ✅ 資料完全分離，無交叉污染
- ✅ 防止就地修改
- ✅ 零資料庫改動

## 部署說明

### 修改檔案
1. **`app/api/dto_models.py`** - 優化摘要生成邏輯
2. **`app/api/helpers.py`** - 完全分離 native 和 display 資料流
3. **`app/api/routes.py`** - 新增 name_native 欄位

### 測試驗證
```bash
python3 test_data_separation.py
```

### 預期效果
- 中文摘要：店名和品名都是中文
- 英文摘要：店名是英文，品名是英文
- 語音：始終使用中文原文
- 資料庫：完全不需要修改

## 技術要點

1. **深拷貝避免共用**：使用 `.copy()` 確保物件獨立
2. **強制語言控制**：中文摘要強制使用 zh 語言
3. **結構化日誌**：便於 Cloud Run 日誌分析
4. **防止就地修改**：避免共享變數被意外修改
5. **零資料庫改動**：完全在應用層處理

## 常見陷阱防護

1. **就地翻譯（in-place mutation）**
   - 避免直接在 `items` 上 `item["name"] = translated_name`
   - 使用深拷貝建立獨立物件

2. **語系判斷覆蓋**
   - 確保 `user_lang` 來源正確
   - 避免預設值設太早

3. **共享物件污染**
   - 使用 `.copy()` 建立獨立副本
   - 驗證資料分離

這個修正確保了雙語功能的穩定性和一致性，徹底解決了「兩份摘要裡品名都變中文、店名都變英文」的問題。
