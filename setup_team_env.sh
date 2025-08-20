#!/bin/bash

# =============================================================================
# 點餐小幫手後端 - 組員環境快速設定腳本
# 功能：自動化環境配置，減少手動設定錯誤
# =============================================================================

echo "🚀 點餐小幫手後端 - 組員環境設定"
echo "=================================="

# 檢查是否已存在 .env 檔案
if [ -f ".env" ]; then
    echo "⚠️  發現已存在的 .env 檔案"
    read -p "是否要備份並重新創建？(y/n): " backup_choice
    if [ "$backup_choice" = "y" ]; then
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
        echo "✅ 已備份為 .env.backup.$(date +%Y%m%d_%H%M%S)"
    else
        echo "❌ 設定已取消"
        exit 1
    fi
fi

# 複製模板檔案
echo "📋 複製環境配置模板..."
cp env_template.txt .env

# 檢查是否成功複製
if [ ! -f ".env" ]; then
    echo "❌ 無法創建 .env 檔案"
    exit 1
fi

echo "✅ 環境配置模板已創建"

# 提示組員設定關鍵配置
echo ""
echo "🔧 請設定以下關鍵配置："
echo ""

# 檢查是否有 gcloud CLI
if command -v gcloud &> /dev/null; then
    echo "✅ 檢測到 gcloud CLI"
    
    # 自動取得專案 ID
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ ! -z "$PROJECT_ID" ]; then
        echo "📋 檢測到 Google Cloud 專案: $PROJECT_ID"
        read -p "是否使用此專案 ID？(y/n): " use_project
        if [ "$use_project" = "y" ]; then
            # 更新 .env 檔案中的專案 ID
            sed -i.bak "s/GCP_PROJECT_ID=your_gcp_project_id_here/GCP_PROJECT_ID=$PROJECT_ID/g" .env
            sed -i.bak "s/CLOUD_RUN_SERVICE_URL=https:\/\/ordering-helper-backend-your-project-id.asia-east1.run.app/CLOUD_RUN_SERVICE_URL=https:\/\/ordering-helper-backend-$PROJECT_ID.asia-east1.run.app/g" .env
            sed -i.bak "s/TASKS_INVOKER_SERVICE_ACCOUNT=tasks-invoker@your-project-id.iam.gserviceaccount.com/TASKS_INVOKER_SERVICE_ACCOUNT=tasks-invoker@$PROJECT_ID.iam.gserviceaccount.com/g" .env
            echo "✅ 已自動設定專案相關配置"
        fi
    fi
else
    echo "⚠️  未檢測到 gcloud CLI，請手動設定專案配置"
fi

echo ""
echo "📝 接下來請手動編輯 .env 檔案，設定以下項目："
echo ""
echo "🔑 必須設定的項目："
echo "   1. GCP_PROJECT_ID - 您的 Google Cloud 專案 ID"
echo "   2. CLOUD_RUN_SERVICE_URL - 您的 Cloud Run 服務 URL"
echo "   3. TASKS_INVOKER_SERVICE_ACCOUNT - 您的服務帳戶"
echo "   4. LINE_CHANNEL_ACCESS_TOKEN - 您的 LINE Bot 存取權杖"
echo "   5. LINE_CHANNEL_SECRET - 您的 LINE Bot 密鑰"
echo "   6. GEMINI_API_KEY - 您的 Google Gemini API 金鑰"
echo ""
echo "💾 資料庫配置（共用，通常不需要修改）："
echo "   - DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE"
echo ""

# 詢問是否要開啟編輯器
read -p "是否要現在編輯 .env 檔案？(y/n): " edit_choice
if [ "$edit_choice" = "y" ]; then
    # 檢查可用的編輯器
    if command -v nano &> /dev/null; then
        nano .env
    elif command -v vim &> /dev/null; then
        vim .env
    elif command -v vi &> /dev/null; then
        vi .env
    else
        echo "⚠️  未找到文字編輯器，請手動編輯 .env 檔案"
    fi
fi

echo ""
echo "🔍 配置驗證..."
echo ""

# 檢查關鍵配置是否已設定
MISSING_CONFIGS=()

# 檢查專案 ID
if grep -q "GCP_PROJECT_ID=your_gcp_project_id_here" .env; then
    MISSING_CONFIGS+=("GCP_PROJECT_ID")
fi

# 檢查服務 URL
if grep -q "CLOUD_RUN_SERVICE_URL=https://ordering-helper-backend-your-project-id.asia-east1.run.app" .env; then
    MISSING_CONFIGS+=("CLOUD_RUN_SERVICE_URL")
fi

# 檢查服務帳戶
if grep -q "TASKS_INVOKER_SERVICE_ACCOUNT=tasks-invoker@your-project-id.iam.gserviceaccount.com" .env; then
    MISSING_CONFIGS+=("TASKS_INVOKER_SERVICE_ACCOUNT")
fi

# 檢查 LINE Bot 配置
if grep -q "LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token_here" .env; then
    MISSING_CONFIGS+=("LINE_CHANNEL_ACCESS_TOKEN")
fi

if grep -q "LINE_CHANNEL_SECRET=your_line_channel_secret_here" .env; then
    MISSING_CONFIGS+=("LINE_CHANNEL_SECRET")
fi

# 檢查 Gemini API
if grep -q "GEMINI_API_KEY=your_gemini_api_key_here" .env; then
    MISSING_CONFIGS+=("GEMINI_API_KEY")
fi

# 顯示驗證結果
if [ ${#MISSING_CONFIGS[@]} -eq 0 ]; then
    echo "✅ 所有關鍵配置都已設定"
else
    echo "⚠️  以下配置尚未設定："
    for config in "${MISSING_CONFIGS[@]}"; do
        echo "   - $config"
    done
    echo ""
    echo "請編輯 .env 檔案完成設定"
fi

echo ""
echo "📚 下一步："
echo "1. 完成 .env 檔案設定"
echo "2. 執行 'python3 run.py' 啟動應用程式"
echo "3. 檢查配置驗證訊息"
echo "4. 參考 TEAM_SETUP_GUIDE.md 進行詳細設定"
echo ""
echo "🎯 設定完成後，您應該能看到："
echo "   ✅ Cloud Tasks 配置驗證通過"
echo "   ✅ 應用程式正常啟動"
echo "   ✅ API 端點正常回應"
echo ""
echo "祝您設定順利！🚀"
