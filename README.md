# 點餐傳聲筒後端 (Ordering Helper Backend)

一個基於 Flask 的 LINE Bot 後端系統，提供多語言點餐服務。

## 功能特色

- 🌐 多語言支援（中文、英文、日文等）
- 🤖 LINE Bot 整合
- 🗣️ 語音合成功能（Azure Speech Service）
- 🧠 AI 菜單處理（Google Gemini）
- 📊 後台管理系統
- 🗄️ MySQL 資料庫整合

## 技術架構

- **後端框架**: Flask
- **資料庫**: MySQL (Google Cloud SQL)
- **AI 服務**: Google Gemini
- **語音服務**: Azure Speech Service
- **部署平台**: Google Cloud Run

## 本地開發

### 環境需求
- Python 3.11+
- MySQL 8.0+

### 安裝步驟

1. **克隆專案**
```bash
git clone <your-repo-url>
cd ordering-helper-backend
```

2. **安裝依賴**
```bash
pip install -r requirements.txt
```

3. **設定環境變數**
複製 `notebook.env.example` 為 `notebook.env` 並填入你的設定：
```bash
cp notebook.env.example notebook.env
# 編輯 notebook.env 檔案
```

4. **啟動應用程式**
```bash
python run.py
```

應用程式會在 `http://127.0.0.1:5001` 啟動

## 部署到 Google Cloud Run

### 方法一：透過 GitHub Actions（推薦）

1. **設定 GitHub Secrets**
在 GitHub 專案設定中新增以下 secrets：
- `GCP_SA_KEY`: Google Cloud 服務帳號金鑰
- `DB_USERNAME`: 資料庫使用者名稱
- `DB_PASSWORD`: 資料庫密碼
- `DB_HOST`: 資料庫主機
- `DB_NAME`: 資料庫名稱
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Bot 存取權杖
- `LINE_CHANNEL_SECRET`: LINE Bot 密鑰
- `GEMINI_API_KEY`: Google Gemini API 金鑰
- `AZURE_SPEECH_KEY`: Azure Speech Service 金鑰
- `AZURE_SPEECH_REGION`: Azure Speech Service 區域

2. **修改 GitHub Actions 設定**
編輯 `.github/workflows/deploy.yml` 中的 `PROJECT_ID`

3. **推送程式碼**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 方法二：手動部署

1. **建立 Docker 映像**
```bash
docker build -t gcr.io/YOUR_PROJECT_ID/ordering-helper-backend .
```

2. **推送到 Container Registry**
```bash
docker push gcr.io/YOUR_PROJECT_ID/ordering-helper-backend
```

3. **部署到 Cloud Run**
```bash
gcloud run deploy ordering-helper-backend \
  --image gcr.io/YOUR_PROJECT_ID/ordering-helper-backend \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated
```

## 專案結構

```
ordering-helper-backend/
├── app/                    # Flask 應用程式
│   ├── __init__.py        # 應用程式工廠
│   ├── models.py          # 資料庫模型
│   ├── api/               # API 路由
│   ├── admin/             # 後台管理
│   └── webhook/           # LINE Bot webhook
├── static/                # 靜態檔案
├── templates/             # HTML 模板
├── tools/                 # 工具腳本
├── Dockerfile             # Docker 設定
├── requirements.txt       # Python 依賴
└── run.py                # 應用程式入口
```

## API 端點

- `GET /` - 重定向到後台管理
- `GET /admin/dashboard` - 後台管理首頁
- `POST /webhook/line` - LINE Bot webhook
- `POST /api/process-menu` - 處理菜單
- `POST /api/generate-voice` - 生成語音

## 環境變數

| 變數名稱 | 說明 | 範例 |
|---------|------|------|
| `DB_USERNAME` | 資料庫使用者名稱 | `gae252g1usr` |
| `DB_PASSWORD` | 資料庫密碼 | `your_password` |
| `DB_HOST` | 資料庫主機 | `35.201.153.17` |
| `DB_NAME` | 資料庫名稱 | `gae252g1_db` |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot 存取權杖 | `your_token` |
| `LINE_CHANNEL_SECRET` | LINE Bot 密鑰 | `your_secret` |
| `GEMINI_API_KEY` | Google Gemini API 金鑰 | `your_gemini_key` |
| `AZURE_SPEECH_KEY` | Azure Speech Service 金鑰 | `your_azure_key` |
| `AZURE_SPEECH_REGION` | Azure Speech Service 區域 | `australiaeast` |

## 貢獻

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 授權

此專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 檔案

## 聯絡資訊

如有問題或建議，請聯絡專案維護者。 # 測試自動部署
# 觸發自動部署 - 2025年 8月 3日 週日 02時29分39秒 CST
