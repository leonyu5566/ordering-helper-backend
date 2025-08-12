# Store Resolver 解決方案

## 問題描述

你的應用程式遇到了資料型別不符的錯誤：

```
(pymysql.err.DataError) (1366, "Incorrect integer value: 'ChlJ0boght2rQjQRsH-_buCo3S4' for column 'store_id' at row 1")
```

**根本原因**：
- 前端傳送的是 **Google Place ID 字串**（如 `ChlJ0boght2rQjQRsH-_buCo3S4`）
- 資料庫的 `menus.store_id` 欄位期望的是 **整數**
- 在建立臨時菜單項目時，系統嘗試將字串插入整數欄位

## 解決方案

我們建立了一個 **Store Resolver** 服務，自動處理 Place ID 到內部整數 `store_id` 的轉換。

### 核心功能

1. **自動識別輸入格式**：
   - 整數：`123` → 直接使用
   - 數字字串：`"456"` → 轉換為整數
   - Google Place ID：`"ChlJ0boght2rQjQRsH-_buCo3S4"` → 查詢或建立店家記錄

2. **智能店家管理**：
   - 如果 Place ID 已存在 → 返回現有的 `store_id`
   - 如果 Place ID 不存在 → 自動建立新店家記錄，返回新的 `store_id`

3. **資料庫一致性**：
   - 所有寫入操作都使用整數 `store_id`
   - 保持資料庫 schema 不變
   - 支援現有的外鍵關聯

## 檔案結構

```
app/
├── api/
│   ├── store_resolver.py      # 核心解析服務
│   └── routes.py              # 已整合 store resolver
├── models.py                  # 資料庫模型（未修改）
└── ...
```

## 使用方法

### 1. 在 Python 程式碼中使用

```python
from app.api.store_resolver import resolve_store_id

# 解析 Google Place ID
place_id = "ChlJ0boght2rQjQRsH-_buCo3S4"
store_db_id = resolve_store_id(place_id)
print(f"解析結果: {place_id} -> {store_db_id}")

# 解析數字字串
store_db_id = resolve_store_id("123")
print(f"解析結果: '123' -> {store_db_id}")

# 解析整數
store_db_id = resolve_store_id(456)
print(f"解析結果: 456 -> {store_db_id}")
```

### 2. 在 API 路由中使用

```python
@api_bp.route('/upload-menu-image', methods=['POST'])
def upload_menu_image():
    # 取得前端傳送的 store_id（可能是 Place ID）
    raw_store_id = request.form.get('store_id')
    
    # 使用 store resolver 解析
    try:
        from .store_resolver import resolve_store_id
        store_db_id = resolve_store_id(raw_store_id)
        print(f"✅ 店家ID解析成功: {raw_store_id} -> {store_db_id}")
    except Exception as e:
        return jsonify({"error": "店家ID格式錯誤"}), 400
    
    # 後續操作都使用整數 store_db_id
    menu = Menu(store_id=store_db_id, ...)
    # ...
```

### 3. 測試 API 端點

```bash
# 測試 Google Place ID 解析
curl "https://your-api.com/api/stores/resolve?place_id=ChlJ0boght2rQjQRsH-_buCo3S4&store_name=測試店家"

# 回應
{
  "success": true,
  "original_place_id": "ChlJ0boght2rQjQRsH-_buCo3S4",
  "resolved_store_id": 123,
  "store_name": "測試店家",
  "message": "成功解析店家識別碼: ChlJ0boght2rQjQRsH-_buCo3S4 -> 123"
}
```

## 已修改的 API 端點

### 1. `POST /api/upload-menu-image`
- ✅ 已整合 store resolver
- ✅ 自動處理 Place ID 轉換
- ✅ 返回解析後的整數 `store_id`

### 2. `POST /api/menu/process-ocr`
- ✅ 已整合 store resolver
- ✅ 自動處理 Place ID 轉換

### 3. `POST /api/orders`
- ✅ 已整合 store resolver
- ✅ 自動處理 Place ID 轉換

### 4. `POST /api/orders/ocr`
- ✅ 已整合 store resolver
- ✅ 自動處理 Place ID 轉換

## 資料庫變更

**無需修改現有 schema**！系統會自動：

1. 在 `stores` 表中建立新記錄（如果 Place ID 不存在）
2. 使用自動遞增的整數 `store_id`
3. 將 Place ID 儲存在 `stores.place_id` 欄位中

## 測試

### 1. 執行測試腳本

```bash
python test_store_resolver.py
```

### 2. 測試 API 端點

```bash
# 測試 Place ID 解析
curl "https://your-api.com/api/stores/resolve?place_id=ChlJ0boght2rQjQRsH-_buCo3S4"

# 測試 OCR 菜單上傳（使用 Place ID）
curl -X POST "https://your-api.com/api/upload-menu-image" \
  -F "image=@menu.jpg" \
  -F "store_id=ChlJ0boght2rQjQRsH-_buCo3S4"
```

## 錯誤處理

### 1. 無效的 Place ID 格式

```json
{
  "error": "無效的 place_id 格式",
  "place_id": "invalid_id",
  "valid_formats": [
    "整數 (如: 123)",
    "數字字串 (如: '456')", 
    "Google Place ID (如: 'ChlJ0boght2rQjQRsH-_buCo3S4')"
  ]
}
```

### 2. 資料庫連線錯誤

```json
{
  "error": "店家識別碼解析失敗",
  "details": "資料庫連線失敗",
  "place_id": "ChlJ0boght2rQjQRsH-_buCo3S4"
}
```

## 優勢

1. **向後相容**：不影響現有的整數 `store_id` 使用
2. **自動化**：無需手動轉換，系統自動處理
3. **資料一致性**：所有資料庫操作都使用整數
4. **效能優化**：重複的 Place ID 會快取現有結果
5. **錯誤處理**：完整的錯誤處理和日誌記錄

## 部署注意事項

1. **確保資料庫連線正常**
2. **檢查 `stores` 表是否有 `place_id` 欄位**
3. **測試 Place ID 解析功能**
4. **監控日誌中的解析結果**

## 未來改進

1. **快取機制**：Redis 快取常用的 Place ID 映射
2. **批量處理**：支援批量 Place ID 解析
3. **地理資訊**：整合 Google Places API 取得店家詳細資訊
4. **統計分析**：追蹤 Place ID 使用頻率和轉換率

---

## 總結

這個解決方案完全解決了你的資料型別不符問題：

- ✅ **前端可以繼續傳送 Google Place ID**
- ✅ **後端自動轉換為整數 store_id**
- ✅ **資料庫保持原有的整數 schema**
- ✅ **無需修改現有程式碼邏輯**
- ✅ **支援所有現有的 API 端點**

現在你可以重新測試你的應用程式，應該不會再出現 `Incorrect integer value for column 'store_id'` 的錯誤了！
