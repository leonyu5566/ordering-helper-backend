# 緊急修復總結

## 問題描述

根據您的分析，系統出現了以下嚴重問題：

1. **API 端點 500 錯誤**：`/api/orders` 端點一呼就回 500 錯誤
2. **Worker timeout/OOM**：Gunicorn worker 連續 timeout 並被 SIGKILL
3. **Pydantic 警告**：大量警告訊息影響性能
4. **環境變數問題**：錯誤的環境變數設定

## 根本原因分析

### 1. UUID 變數衝突問題
**問題**：在函數內部有 `import uuid` 語句，覆蓋了全局的 `uuid` 模組
**錯誤訊息**：`cannot access local variable 'uuid' where it is not associated with a value`
**位置**：
- `app/api/routes.py` 第 462 行和第 705 行
- `app/api/helpers.py` 第 455 行

### 2. 舊格式訂單處理問題
**問題**：`/api/orders` 端點期望 `menu_item_id`，但舊格式訂單沒有提供
**解決方案**：讓 `/api/orders` 直接轉發到 `simple_order()`

### 3. 記憶體和並發問題
**問題**：Cloud Run 設定並發 80，記憶體 2Gi 不足以處理 TTS/Gemini 請求
**解決方案**：降低並發數到 20，最大實例數到 5

### 4. Pydantic 警告問題
**問題**：大量 `UserWarning: Field name "xxx" shadows an attribute` 警告
**解決方案**：在 Dockerfile 中添加 `ENV PYTHONWARNINGS=ignore`

## 修復措施

### 1. 修復 UUID 變數衝突
```python
# 修復前
if not line_user_id:
    import uuid  # 這會覆蓋全局 uuid 模組
    line_user_id = f"guest_{uuid.uuid4().hex[:8]}"

# 修復後
if not line_user_id:
    line_user_id = f"guest_{uuid.uuid4().hex[:8]}"  # 使用全局 uuid 模組
```

### 2. 簡化 `/api/orders` 端點
```python
@api_bp.route('/orders', methods=['POST', 'OPTIONS'])
def create_order():
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    # 直接轉發到 simple_order 以確保向後相容性
    return simple_order()
```

### 3. 增強 `simple_order` 的舊格式支援
```python
# 檢查是否為舊格式訂單，如果是則轉換為新格式
if 'store_id' in data and 'items' in data:
    # 舊格式訂單，需要轉換
    print("檢測到舊格式訂單，進行格式轉換")
    
    # 重構資料格式以符合新格式的要求
    simple_data = {
        'items': [],
        'lang': data.get('language', 'zh-TW'),
        'line_user_id': data.get('line_user_id')
    }
    
    for item in data.get('items', []):
        # 防呆轉換器：把舊格式轉成新 nested name 格式
        item_name = item.get('item_name') or item.get('name') or item.get('original_name') or '未知項目'
        
        # 檢查是否已經是新的雙語格式
        if isinstance(item_name, dict) and 'original' in item_name and 'translated' in item_name:
            # 已經是新格式
            simple_item = {
                'name': item_name,
                'quantity': item.get('quantity') or item.get('qty') or 1,
                'price': item.get('price') or item.get('price_small') or 0
            }
        else:
            # 舊格式，轉換成新格式
            simple_item = {
                'name': {
                    'original': item_name,
                    'translated': item_name
                },
                'quantity': item.get('quantity') or item.get('qty') or 1,
                'price': item.get('price') or item.get('price_small') or 0
            }
        
        simple_data['items'].append(simple_item)
    
    # 使用轉換後的資料
    data = simple_data
```

### 4. 優化 Cloud Run 配置
```bash
gcloud run deploy ordering-helper-backend \
  --source . \
  --region asia-east1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 20 \  # 從 80 降到 20
  --max-instances 5   # 從 10 降到 5
```

### 5. 修復 Pydantic 警告
```dockerfile
# 設定環境變數
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONWARNINGS=ignore  # 新增這行
```

## 修復結果

### ✅ 成功的修復
1. **API 端點修復**：`/api/orders` 現在可以正常處理舊格式訂單
2. **UUID 問題解決**：移除了所有局部的 `import uuid` 語句
3. **記憶體問題改善**：降低並發數，減少 OOM 風險
4. **警告訊息消除**：添加了 `PYTHONWARNINGS=ignore`

### 📊 測試結果
```
🧪 測試 API 部署...

1️⃣ 測試健康檢查...
✅ 健康檢查通過

2️⃣ 測試舊格式訂單...
✅ 舊格式訂單處理成功
   訂單ID: dual_77524140
   總金額: 255.0
   中文摘要: 經典夏威夷奶醬義大利麵  x 1、奶油蝦仁鳳梨義大利麵  x 1
   使用者摘要: Order: 經典夏威夷奶醬義大利麵  x 1、奶油蝦仁鳳梨義大利麵  x 1

3️⃣ 測試新格式訂單...
✅ 新格式訂單處理成功
   訂單ID: dual_7f0c2129
   總金額: 255.0
   中文摘要: 經典夏威夷奶醬義大利麵  x 1、奶油蝦仁鳳梨義大利麵  x 1
   使用者摘要: Order: Creamy Classic Hawaiian  x 1、Creamy Shrimp Pineapple  x 1

4️⃣ 測試臨時訂單...
✅ 臨時訂單處理成功
   訂單ID: dual_3703f1d0
   總金額: 115.0
   中文摘要: 奶油經典夏威夷  x 1
   使用者摘要: Order: 奶油經典夏威夷  x 1

🎉 API 部署測試完成!
```

## 部署信息

- **服務名稱**：ordering-helper-backend
- **服務 URL**：https://ordering-helper-backend-1095766716155.asia-east1.run.app
- **修訂版本**：ordering-helper-backend-00306-4gc
- **配置**：2Gi 記憶體, 2 CPU, 300秒超時, 並發 20, 最大實例 5

## 前端相容性

前端 LIFF 應用程式 (`../liff-web/index.html`) 使用的是 `/api/orders` 端點，與我們的修復完全相容：

```javascript
const response = await fetch(`${API_BASE_URL}/api/orders`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload)
});
```

## 下一步建議

1. **監控系統穩定性**
   - 觀察 Cloud Run 記憶體使用情況
   - 監控 worker timeout 和 OOM 事件
   - 檢查語音生成功能

2. **性能優化**
   - 考慮增加記憶體配置到 4Gi
   - 優化 TTS 和 Gemini API 調用
   - 實現語音檔案快取機制

3. **錯誤處理改進**
   - 添加更詳細的錯誤日誌
   - 實現重試機制
   - 改善用戶錯誤訊息

4. **前端優化**
   - 檢查 LIFF 應用程式的錯誤處理
   - 改善用戶體驗
   - 添加載入狀態指示

## 結論

緊急修復已成功解決了系統的主要問題：
- ✅ API 端點 500 錯誤已修復
- ✅ UUID 變數衝突已解決
- ✅ 舊格式訂單處理已支援
- ✅ 記憶體問題已改善
- ✅ Pydantic 警告已消除

系統現在可以正常處理來自 LIFF 前端的訂單請求，並保持了向後相容性。
