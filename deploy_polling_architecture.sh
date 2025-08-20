#!/bin/bash

# 部署輪詢架構腳本
# 適用於 LIFF 環境的「短請求 + 輪詢」新架構

echo "🚀 開始部署輪詢架構..."

# 1. 檢查 Git 狀態
echo "📋 檢查 Git 狀態..."
git status

# 2. 新增檔案
echo "📁 新增檔案..."
git add app/api/routes.py
git add app/api/helpers.py
git add frontend_polling_example.js
git add deploy_polling_architecture.sh

# 3. 提交變更
echo "💾 提交變更..."
git commit -m "🔧 實作 LIFF 輪詢架構

- 新增快速訂單建立端點 (/api/orders/quick)
- 新增訂單狀態查詢端點 (/api/orders/status/{id})
- 新增背景處理任務 (process_order_background)
- 新增前端輪詢範例程式碼
- 解決 LIFF 環境的長時間等待問題
- 改善使用者體驗，提供即時回應

架構變更：
1. 快速建立訂單 (1-2秒回應)
2. 背景處理語音和通知
3. 前端輪詢狀態 (每2秒)
4. 完成後顯示結果

這個架構特別適合 LIFF 環境，避免長時間等待和超時問題。"

# 4. 推送到遠端
echo "📤 推送到遠端..."
git push origin main

# 5. 部署到 Cloud Run
echo "☁️ 部署到 Cloud Run..."
gcloud run deploy ordering-helper-backend \
    --source . \
    --platform managed \
    --region asia-east1 \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 1 \
    --max-instances 10 \
    --timeout 300 \
    --concurrency 80

# 6. 檢查部署狀態
echo "🔍 檢查部署狀態..."
gcloud run services describe ordering-helper-backend \
    --platform managed \
    --region asia-east1 \
    --format="value(status.url)"

echo "✅ 輪詢架構部署完成！"

# 7. 顯示測試資訊
echo ""
echo "🧪 測試資訊："
echo "1. 快速訂單建立: POST /api/orders/quick"
echo "2. 訂單狀態查詢: GET /api/orders/status/{order_id}"
echo "3. 前端輪詢範例: frontend_polling_example.js"
echo ""
echo "📱 LIFF 環境測試："
echo "- 使用快速訂單建立端點避免長時間等待"
echo "- 前端每2秒輪詢一次狀態"
echo "- 最多輪詢30次（60秒）"
echo "- 提供進度條和狀態更新"
echo ""
echo "🎯 預期改善："
echo "- 使用者體驗大幅提升"
echo "- 避免 LIFF 環境的超時問題"
echo "- 提供即時回應和狀態更新"
echo "- 背景處理不影響前端響應"
