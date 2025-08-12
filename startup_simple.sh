#!/bin/bash

# Cloud Run 簡化啟動腳本
echo "=== Cloud Run 啟動腳本 ==="
echo "當前目錄: $(pwd)"
echo "環境變數 PORT: $PORT"

# 設定預設端口
if [ -z "$PORT" ]; then
    export PORT=8080
    echo "使用預設端口: $PORT"
else
    echo "使用環境變數端口: $PORT"
fi

# 檢查必要檔案
echo "檢查必要檔案..."
ls -la run.py app/__init__.py

# 啟動應用程式
echo "啟動 Flask 應用程式在端口 $PORT..."
exec gunicorn \
    --bind "0.0.0.0:$PORT" \
    --workers 1 \
    --timeout 300 \
    --graceful-timeout 60 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --worker-class sync \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    run:app
