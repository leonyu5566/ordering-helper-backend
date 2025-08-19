# 店名翻譯修正總結

## 問題描述

前端顯示「中文店名 + (en)」的問題，原因是後端 API 沒有正確回傳翻譯後的店名欄位。

## 根本原因

1. **前端邏輯依賴後端提供翻譯後店名**
   - 前端會優先使用 `display_name || translated_name || store_name`
   - 如果後端只回傳 `store_name`（中文），前端就會顯示中文

2. **後端 API 缺少翻譯欄位**
   - `/api/stores/check-partner-status` 沒有回傳 `translated_name` 欄位
   - 菜單端點使用舊的翻譯邏輯

## 修正內容

### 1. 修正 `/api/stores/check-partner-status` 端點

**修改前**：
```json
{
  "store_id": 123,
  "store_name": "本家精選村",
  "display_name": "Ben Jia Choice Village",
  "original_name": "本家精選村",
  "is_partner": true
}
```

**修改後**：
```json
{
  "store_id": 123,
  "store_name": "本家精選村",
  "display_name": "Ben Jia Choice Village",  // 前端優先使用
  "translated_name": "Ben Jia Choice Village",  // 前端也會檢查
  "original_name": "本家精選村",
  "is_partner": true
}
```

### 2. 更新菜單端點翻譯邏輯

**修改的端點**：
- `/api/menu/<store_id>`
- `/api/menu/by-place-id/<place_id>`

**修改內容**：
- 移除重複的語言碼正規化函數
- 統一使用 `translation_service` 模組
- 確保菜單項目名稱和分類都會翻譯

### 3. 統一語言碼正規化

**修改前**：每個端點都有自己的語言碼正規化函數
**修改後**：統一使用 `app/api/translation_service.py` 中的 `normalize_lang()` 函數

## 修正的檔案

### 修改檔案
- `app/api/routes.py` - 更新所有相關 API 端點

### 新增檔案
- `test_store_name_fix.py` - 測試腳本
- `STORE_NAME_TRANSLATION_FIX.md` - 修正總結文檔

## 測試驗證

### 測試腳本
```bash
python3 test_store_name_fix.py
```

### 預期結果
1. ✅ `/api/stores/check-partner-status` 回傳 `display_name` 和 `translated_name`
2. ✅ `/api/store/resolve` 回傳翻譯後的店名
3. ✅ 菜單端點回傳翻譯後的菜名
4. ✅ 翻譯 API 正常工作

## API 回應格式

### `/api/stores/check-partner-status`
```json
{
  "store_id": 123,
  "store_name": "本家精選村",
  "display_name": "Ben Jia Choice Village",
  "translated_name": "Ben Jia Choice Village",
  "original_name": "本家精選村",
  "place_id": "ChlJ0boght2rQjQRsH-_buCo3S4",
  "partner_level": 1,
  "is_partner": true,
  "has_menu": true
}
```

### `/api/menu/<store_id>`
```json
{
  "store_id": 123,
  "user_language": "en-US",
  "normalized_language": "en",
  "menu_items": [
    {
      "id": 1,
      "name": "Translated Item Name",
      "original_name": "原始菜名",
      "price_small": 50,
      "price_large": 80,
      "category": "Translated Category",
      "original_category": "原始分類"
    }
  ]
}
```

## 部署狀態

- ✅ 程式碼已提交到 GitHub
- ✅ 語法檢查通過
- 🔄 等待 Cloud Run 自動部署
- 🔄 需要測試實際部署效果

## 下一步

1. **等待部署完成**
   - GitHub Actions 會自動觸發 Cloud Run 部署
   - 檢查部署日誌確認無錯誤

2. **測試實際效果**
   - 使用 `test_store_name_fix.py` 測試生產環境
   - 確認前端不再顯示中文店名

3. **監控效果**
   - 觀察前端是否正確顯示翻譯後店名
   - 確認菜單項目也正確翻譯

## 注意事項

1. **翻譯服務依賴**
   - 需要 Google Cloud Translation API 正常運作
   - 翻譯失敗時會回傳原文

2. **語言碼支援**
   - 支援 BCP-47 格式（如 `en-US`, `ja-JP`）
   - 自動正規化為支援的短碼

3. **錯誤處理**
   - 所有端點都永遠回傳 200 狀態碼
   - 翻譯失敗時有 fallback 機制

## 總結

這次修正解決了前端顯示中文店名的根本問題：
- ✅ 確保後端正確回傳翻譯欄位
- ✅ 統一翻譯服務邏輯
- ✅ 支援完整的 BCP-47 語言碼
- ✅ 提供完善的錯誤處理

修正後，前端應該能正確顯示翻譯後的店名，不再出現「中文店名 + (en)」的問題。
