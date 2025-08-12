#!/bin/bash

# Cloud Run 啟動腳本
echo "=== Cloud Run 啟動腳本 ==="
echo "當前目錄: $(pwd)"
echo "環境變數 PORT: $PORT"
echo "環境變數 FLASK_APP: $FLASK_APP"
echo "Python 版本: $(python3 --version)"
echo "Gunicorn 版本: $(gunicorn --version)"

# 檢查必要檔案
echo "檢查必要檔案..."
ls -la

# 啟動應用程式
echo "啟動 Flask 應用程式..."
exec gunicorn \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 1 \
    --timeout 300 \
    --graceful-timeout 60 \
    --max-requests 500 \
    --max-requests-jitter 50 \
    --preload \
    --worker-class sync \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    run:app
