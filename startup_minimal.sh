#!/bin/bash

# 最簡化的 Cloud Run 啟動腳本
echo "=== 最簡化 Cloud Run 啟動腳本 ==="

# 設定預設端口
export PORT=${PORT:-8080}
echo "使用端口: $PORT"

# 檢查 Python 環境
echo "Python 版本:"
python3 --version

# 檢查必要檔案
echo "檢查 run.py..."
ls -la run.py

echo "檢查 app 目錄..."
ls -la app/

# 啟動應用程式
echo "啟動 Flask 應用程式..."
echo "使用 gunicorn 在端口 $PORT 啟動..."

exec gunicorn \
    --bind "0.0.0.0:$PORT" \
    --workers 1 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    run:app
