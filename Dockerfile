# 使用 Ubuntu 20.04 作為基礎映像（支援 OpenSSL 1.1.1）
FROM ubuntu:20.04

# 設定環境變數避免互動式安裝
ENV DEBIAN_FRONTEND=noninteractive

# 安裝 Python 3.11 和必要系統庫
RUN apt-get update && \
    apt-get install -y \
        software-properties-common \
        ca-certificates \
        curl \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update && \
    apt-get install -y \
        python3.11 \
        python3.11-dev \
        python3-pip \
        libssl1.1 \
        libasound2 \
        libpthread-stubs0-dev \
        gunicorn \
    && rm -rf /var/lib/apt/lists/*

# 設定 Python 3.11 為預設版本
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3 1

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt
COPY requirements.txt .

# 安裝 Python 依賴套件
RUN pip3 install --no-cache-dir -r requirements.txt

# 複製應用程式程式碼
COPY . .

# 建立語音檔案目錄
RUN mkdir -p /tmp/voices && chmod 755 /tmp/voices

# 設定環境變數
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8080

# 啟動命令 - 調整記憶體和超時設定
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "120", "--graceful-timeout", "30", "--max-requests", "1000", "--max-requests-jitter", "100", "run:app"] 