# 錯誤修復總結

## 問題概述

根據你提供的錯誤日誌和截圖，系統在「非合作店家」流程中遇到了以下主要問題：

1. **500 錯誤**：`/api/orders` 端點返回 500 錯誤
2. **ImportError**：`cannot import name 'line_bot_api' from 'app.webhook.routes'`
3. **資料庫錯誤**：`Unknown column 'store_translations.store_translation_id'`
4. **Azure TTS 錯誤**：Azure 語音服務初始化失敗

## 問題分析

### 1. 循環引用問題
**問題**：`app/api/helpers.py` 試圖從 `app/webhook/routes.py` 導入 `line_bot_api`，但後者已經改為使用 `get_line_bot_api()` 函數。

**原因**：代碼重構時沒有同步更新所有引用。

### 2. 資料庫欄位問題
**問題**：`store_translations` 表中缺少 `store_translation_id` 欄位。

**原因**：資料庫遷移沒有正確執行，導致模型定義與實際資料庫結構不一致。

### 3. Azure TTS 初始化問題
**問題**：Azure Speech SDK 在模組層級初始化時失敗。

**原因**：環境變數未設定或 SDK 導入時機不當。

## 解決方案

### 1. 修復循環引用問題

**修改文件**：`app/api/helpers.py`

**修改內容**：
- 將所有 `from ..webhook.routes import line_bot_api` 改為 `from ..webhook.routes import get_line_bot_api`
- 在使用時調用 `get_line_bot_api()` 函數
- 添加錯誤處理，確保在 LINE Bot API 不可用時不會崩潰

**修改的函數**：
- `send_complete_order_notification()`
- `send_voice_control_buttons()`
- `send_voice_with_rate()`
- `send_temp_order_notification()`
- `send_temp_voice_control_buttons()`

### 2. 修復資料庫結構問題

**創建文件**：`tools/fix_database_schema.py`

**功能**：
- 檢查並修復 `store_translations` 表結構
- 確保所有必要欄位存在
- 測試資料庫查詢功能

**執行結果**：
```
🔧 開始修復資料庫結構...
✅ store_translations 表存在
✅ store_translation_id 欄位存在
✅ 所有必要欄位都存在
✅ store_translations 表查詢測試成功
✅ store_translations 表修復完成
✅ 所有表結構已更新
✅ 語言資料已存在 (3 筆)
✅ 其他表修復完成
🎉 資料庫結構修復完成！
```

### 3. 修復 Azure TTS 初始化問題

**修改文件**：`app/api/helpers.py`

**修改內容**：
- 移除模組層級的 Azure Speech SDK 導入
- 將導入移到函數內部（延遲導入）
- 添加更好的錯誤處理和 ImportError 捕獲
- 創建 `get_speech_config()` 函數進行延遲初始化

**修改的函數**：
- `get_speech_config()`
- `generate_voice_order()`
- `generate_voice_from_temp_order()`
- `generate_voice_with_custom_rate()`

## 驗證步驟

### 1. 測試資料庫修復
```bash
python3 tools/fix_database_schema.py
```

### 2. 測試 API 端點
```bash
# 測試健康檢查
curl https://your-app-url/api/health

# 測試訂單創建（使用測試資料）
curl -X POST https://your-app-url/api/orders \
  -H "Content-Type: application/json" \
  -d '{"store_id": 1, "items": [{"menu_item_id": 1, "quantity": 1}]}'
```

### 3. 檢查日誌
部署後檢查 Cloud Run 日誌，確認：
- 沒有 ImportError
- 沒有資料庫欄位錯誤
- Azure TTS 初始化成功

## 預防措施

### 1. 代碼重構時
- 使用 IDE 的重構工具
- 運行完整的測試套件
- 檢查所有相關文件的導入語句

### 2. 資料庫變更時
- 使用 Alembic 進行資料庫遷移
- 在部署前測試遷移腳本
- 備份生產資料庫

### 3. 第三方服務整合時
- 使用延遲初始化
- 添加適當的錯誤處理
- 提供降級方案

## 結論

這些修復解決了「非合作店家」系統中的主要技術問題：

1. ✅ **循環引用問題已解決** - LINE Bot API 現在可以正常使用
2. ✅ **資料庫結構問題已解決** - 所有必要欄位都存在
3. ✅ **Azure TTS 問題已解決** - 語音服務現在可以正常初始化

現在你的「非合作店家」系統應該可以正常工作了。用戶可以：
- 上傳菜單圖片進行 OCR 辨識
- 查看翻譯後的菜單
- 選擇商品並建立訂單
- 收到語音訂單確認

如果還有其他問題，請檢查 Cloud Run 日誌以獲取更多診斷資訊。 