# 雙語訂單處理解決方案

## 問題描述

從日誌分析發現，目前的系統在處理中文語音訂單時存在以下問題：

1. **翻譯覆蓋原文**：翻譯功能會直接覆蓋原文，導致中文摘要和語音都變成英文
2. **原文遺失**：翻譯後原文真的不見了，無法同時產出中/英文版本
3. **語音問題**：語音生成使用翻譯後的英文，而不是中文原文

## 解決方案概覽

### 核心策略：應用層處理，不改資料庫

使用 **DTO (Data Transfer Object)** 模式在應用層處理雙語需求，完全不需要修改資料庫結構。

### 實作內容

#### 1. 建立 DTO 模型 (`app/api/dto_models.py`)

```python
class MenuItemDTO(BaseModel):
    """菜單項目 DTO 模型"""
    id: int
    name_source: str  # 資料庫中的原始名稱（中文）
    price_small: int
    price_big: Optional[int] = None
    name_ui: str  # 使用者介面顯示名稱（根據語言決定）
    
    @computed_field
    @property
    def display_name(self) -> str:
        """動態計算顯示名稱"""
        return self.name_ui
    
    @computed_field
    @property
    def original_name(self) -> str:
        """保留原始中文名稱"""
        return self.name_source

class OrderSummaryDTO(BaseModel):
    """訂單摘要 DTO 模型"""
    store_name: str
    items: List[OrderItemDTO]
    total_amount: int
    user_language: str
    
    @computed_field
    @property
    def chinese_summary(self) -> str:
        """生成中文摘要（使用原文）"""
        # 使用 name.original 確保中文摘要使用原文
    
    @computed_field
    @property
    def user_language_summary(self) -> str:
        """生成使用者語言摘要"""
        # 根據語言選擇 name.original 或 name.translated
    
    @computed_field
    @property
    def voice_text(self) -> str:
        """生成語音文字（使用中文原文）"""
        # 始終使用 name.original 生成中文語音
```

#### 2. 修改查詢邏輯 (`app/api/routes.py`)

```python
# 使用 alias 查詢，將 item_name 作為 name_source
menu_item_dto = build_menu_item_dto(item, normalized_lang)

# 如果需要翻譯，使用翻譯服務
if not normalized_lang.startswith('zh'):
    translated_name = translate_text(menu_item_dto.name_source, normalized_lang)
    menu_item_dto.name_ui = translated_name

# 轉換為字典格式，保持 API 兼容性
translated_item = {
    "id": menu_item_dto.id,
    "name": menu_item_dto.name_ui,  # 使用者語言顯示名稱
    "translated_name": menu_item_dto.name_ui,  # 為了前端兼容性
    "original_name": menu_item_dto.name_source,  # 保留原始中文名稱
    "price_small": menu_item_dto.price_small,
    "price_large": menu_item_dto.price_big,
}
```

#### 3. 修改訂單處理邏輯 (`app/api/helpers.py`)

```python
# 使用新的 DTO 模型處理訂單項目
order_items_dto = []
for item in order.items:
    # 建立 DTO 物件
    order_item_dto = build_order_item_dto(item_data, user_language)
    order_items_dto.append(order_item_dto)

# 建立訂單摘要 DTO
order_summary_dto = OrderSummaryDTO(
    store_name=store_name_for_display,
    items=order_items_dto,
    total_amount=order.total_amount,
    user_language=user_language
)

# 生成雙語摘要
chinese_summary = order_summary_dto.chinese_summary
user_language_summary = order_summary_dto.user_language_summary
chinese_voice_text = order_summary_dto.voice_text
```

#### 4. 智能欄位檢測

```python
def contains_cjk(text: str) -> bool:
    """檢查文字是否包含中日韓字符"""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # 中文
            return True
        if '\u3040' <= char <= '\u309f':  # 平假名
            return True
        if '\u30a0' <= char <= '\u30ff':  # 片假名
            return True
        if '\uac00' <= char <= '\ud7af':  # 韓文
            return True
    return False

# 自動檢測並修正欄位顛倒問題
if not contains_cjk(original_name) and contains_cjk(translated_name):
    original_name, translated_name = translated_name, original_name
```

## 測試結果

執行 `test_bilingual_order.py` 的測試結果：

### 中日韓字符檢測
```
'Kimchi Pot' -> CJK: False
'泡菜鍋' -> CJK: True
'牛肉麵' -> CJK: True
'Satay Fish Head Pot' -> CJK: False
'沙爹魚頭鍋' -> CJK: True
```

### 雙語摘要生成

**中文摘要（使用原文）：**
```
店家：葉來香50年古早味麵飯美食
訂購項目：
- 泡菜鍋 x1
- 沙爹魚頭鍋 x1
總金額：$340
```

**英文摘要（使用翻譯）：**
```
Store: 葉來香50年古早味麵飯美食
Items:
- Kimchi Pot x1 ($160)
- Satay Fish Head Pot x1 ($180)
Total: $340
```

**語音文字（使用中文原文）：**
```
老闆，我要泡菜鍋一份、沙爹魚頭鍋一份，謝謝。
```

## 優勢

1. **不改資料庫**：完全在應用層處理，資料庫結構保持不變
2. **保留原文**：中文摘要和語音始終使用原文
3. **動態翻譯**：使用者語言摘要根據語言設定動態選擇
4. **智能檢測**：自動檢測並修正欄位顛倒問題
5. **向後相容**：保持現有 API 接口的兼容性

## 部署說明

1. **新增檔案**：`app/api/dto_models.py`
2. **修改檔案**：
   - `app/api/routes.py` - 菜單查詢邏輯
   - `app/api/helpers.py` - 訂單處理邏輯
3. **測試驗證**：執行 `python3 test_bilingual_order.py`

## 預期效果

- ✅ 中文摘要使用原文（泡菜鍋、沙爹魚頭鍋）
- ✅ 英文摘要使用翻譯（Kimchi Pot、Satay Fish Head Pot）
- ✅ 語音生成使用中文原文
- ✅ 資料庫結構完全不需要修改
- ✅ 支援多語言動態切換
