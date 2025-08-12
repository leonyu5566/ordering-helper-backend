#!/bin/bash

# Cloud Run 部署腳本
echo "=== Cloud Run 部署腳本 ==="

# 設定變數
PROJECT_ID="solid-heaven-466011-d1"
SERVICE_NAME="ordering-helper-backend"
REGION="asia-east1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "專案 ID: $PROJECT_ID"
echo "服務名稱: $SERVICE_NAME"
echo "地區: $REGION"
echo "映像名稱: $IMAGE_NAME"

# 檢查 gcloud 是否已登入
echo "檢查 gcloud 登入狀態..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "錯誤: 請先登入 gcloud"
    echo "執行: gcloud auth login"
    exit 1
fi

# 設定專案
echo "設定專案..."
gcloud config set project $PROJECT_ID

# 建置 Docker 映像
echo "建置 Docker 映像..."
echo "使用 Dockerfile.cloudrun 進行建置..."

# 選擇 Dockerfile
if [ "$1" = "simple" ]; then
    DOCKERFILE="Dockerfile.cloudrun"
    echo "使用簡化 Dockerfile: $DOCKERFILE"
else
    DOCKERFILE="Dockerfile"
    echo "使用標準 Dockerfile: $DOCKERFILE"
fi

# 建置映像
docker build -f $DOCKERFILE -t $IMAGE_NAME .

if [ $? -ne 0 ]; then
    echo "錯誤: Docker 建置失敗"
    exit 1
fi

echo "✅ Docker 映像建置成功"

# 推送映像到 Google Container Registry
echo "推送映像到 GCR..."
docker push $IMAGE_NAME

if [ $? -ne 0 ]; then
    echo "錯誤: 映像推送失敗"
    exit 1
fi

echo "✅ 映像推送成功"

# 部署到 Cloud Run
echo "部署到 Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --concurrency 80 \
    --set-env-vars "PORT=8080"

if [ $? -ne 0 ]; then
    echo "錯誤: Cloud Run 部署失敗"
    exit 1
fi

echo "✅ Cloud Run 部署成功"

# 獲取服務 URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo "服務 URL: $SERVICE_URL"

# 測試服務
echo "測試服務..."
sleep 10

echo "測試健康檢查端點..."
curl -f "$SERVICE_URL/health" || echo "健康檢查失敗"

echo "測試 API 端點..."
curl -f "$SERVICE_URL/api/test" || echo "API 測試失敗"

echo "=== 部署完成 ==="
echo "服務 URL: $SERVICE_URL"
echo "管理控制台: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
