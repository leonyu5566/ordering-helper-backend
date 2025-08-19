# 路由衝突修復總結

## 問題描述

Cloud Run 部署後出現 503 錯誤，前端卡在 "Preparing ordering environment" 狀態。

## 根本原因

在 `app/api/routes.py` 中存在重複的路由定義：

```python
# 第387行
@api_bp.route('/stores/status-and-menu', methods=['GET'])
def get_store_status_and_menu():
    """取得店家狀態和菜單（一次性 API，支援多語言翻譯）"""
    # ... 第一個函數實現

# 第635行  
@api_bp.route('/stores/status-and-menu', methods=['GET'])
def get_store_status_and_menu():
    """優化端點：一次性取得店家狀態和菜單資料（如果有的話）"""
    # ... 第二個函數實現
```

這導致了 Flask 的路由衝突錯誤：
```
AssertionError: View function mapping is overwriting an existing endpoint function: api.get_store_status_and_menu
```

## 修復方案

1. **刪除重複函數**：移除了第一個重複的 `get_store_status_and_menu` 函數（第387-434行）

2. **保留優化版本**：保留了第二個更完整的實現，包含：
   - 更好的錯誤處理
   - 語言碼正規化
   - 翻譯統計
   - 更完整的回應資料結構

3. **更新啟動腳本**：
   - 創建了 `startup_fixed.sh` 使用更安全的 Gunicorn 配置
   - 修改 `Dockerfile` 使用修復版本的啟動腳本

4. **修復部署腳本**：
   - 移除了 `PORT` 環境變數（Cloud Run 自動設定）
   - 使用正確的環境變數配置

## 修復結果

✅ **本地測試通過**：應用程式可以正常啟動和運行
✅ **Cloud Run 部署成功**：服務正常運行在 `https://ordering-helper-backend-1095766716155.asia-east1.run.app`
✅ **健康檢查正常**：`/health` 端點返回 200 狀態
✅ **API 端點正常**：`/api/test` 端點正常回應

## 測試命令

```bash
# 本地測試
python3 test_app.py

# 健康檢查
curl -i "https://ordering-helper-backend-1095766716155.asia-east1.run.app/health"

# API 測試
curl -i "https://ordering-helper-backend-1095766716155.asia-east1.run.app/api/test"
```

## 後續建議

1. **前端測試**：現在可以測試前端是否能正常獲取店家資訊
2. **監控日誌**：持續監控 Cloud Run 日誌確保服務穩定
3. **代碼審查**：檢查是否還有其他重複的路由定義

## 相關檔案

- `app/api/routes.py` - 修復了路由衝突
- `startup_fixed.sh` - 新的啟動腳本
- `deploy_fixed.sh` - 修復的部署腳本
- `test_app.py` - 診斷腳本
- `Dockerfile` - 更新使用修復版本啟動腳本
