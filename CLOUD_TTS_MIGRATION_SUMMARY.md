# Cloud Text-to-Speech 遷移總結

## 概述
已成功將語音生成功能從 gTTS 遷移到 Google Cloud Text-to-Speech API，以提升語音品質和功能完整性。

## 主要變更

### 1. 依賴套件更新
- **移除**: `gTTS==2.4.0`
- **新增**: `google-cloud-texttospeech==2.16.3`

### 2. 核心函數更新
- `get_speech_config()` - 改為返回 Cloud TTS 配置對象
- 新增 `generate_cloud_tts_audio()` - 核心 Cloud TTS 語音生成函數

### 3. 語音生成函數遷移
以下函數已從 gTTS 遷移到 Cloud TTS：
- `generate_voice_order()` - 訂單語音生成
- `generate_voice_from_temp_order()` - 臨時訂單語音生成
- `generate_voice_with_custom_rate()` - 自定義語速語音生成
- `generate_chinese_voice_with_azure()` - 中文語音生成
- `synthesize_azure_tts()` - 語音合成
- `generate_voice_order_enhanced()` - 增強版訂單語音生成
- `generate_voice_with_custom_rate_enhanced()` - 增強版自訂語音生成

## 技術改進

### 1. 語音品質提升
- **語音類型**: 從 gTTS 的基礎語音升級到 Cloud TTS 的 WaveNet 高品質語音
- **預設語音**: `cmn-TW-Wavenet-A` (台灣中文高品質女聲)
- **音訊格式**: 直接輸出 MP3 格式，無需轉檔

### 2. 功能增強
- **語速控制**: 支援精確的語速倍率調整 (0.5-2.0)
- **語音選擇**: 可選擇不同的語音類型 (WaveNet, Standard, Neural)
- **語言支援**: 支援多種語言和方言

### 3. 部署優勢
- **自動認證**: 在 Google Cloud 環境中自動使用服務帳號認證
- **無需 API 金鑰管理**: 在 Cloud Run 等環境中自動處理認證
- **穩定可靠**: Google Cloud 企業級服務的穩定性和可靠性

## 配置要求

### 1. Google Cloud 設定
- 啟用 `Text-to-Speech API` (`texttospeech.googleapis.com`)
- 確保服務帳號擁有 `Cloud AI Service Agent` 或 `Vertex AI User` 角色

### 2. 環境變數
無需額外的環境變數設定，在 Google Cloud 環境中會自動認證。

## 相容性說明

### 1. 向後相容
- 所有函數的參數和返回值保持不變
- 語音檔案格式仍為 MP3
- 檔案路徑和命名規則保持一致

### 2. 功能差異
- **語速控制**: 從 gTTS 的 `slow` 布林值升級到精確的倍率控制
- **語音品質**: 從基礎語音升級到高品質 WaveNet 語音
- **網路依賴**: 仍需要網路連接，但使用 Google Cloud 的穩定服務

## 測試建議

### 1. 功能測試
- 測試各種語速設定 (0.5x, 1.0x, 1.5x, 2.0x)
- 驗證語音檔案生成和儲存
- 確認語音品質提升

### 2. 部署測試
- 在本地環境測試（需要 Google Cloud 認證）
- 在 Cloud Run 環境測試（自動認證）
- 驗證語音檔案傳送到 LINE Bot

## 注意事項

### 1. 成本考量
- Cloud TTS 是付費服務，按使用量計費
- 建議監控 API 使用量和成本

### 2. 網路延遲
- 首次呼叫可能會有網路延遲
- 建議實作快取機制減少重複呼叫

### 3. 錯誤處理
- 已實作完整的錯誤處理和備用方案
- 在 API 失敗時會回退到備用語音生成

## 總結
這次遷移成功將語音生成功能從 gTTS 升級到 Cloud TTS，大幅提升了語音品質和功能完整性。雖然需要 Google Cloud 環境支援，但提供了更穩定、高品質的語音服務，特別適合生產環境使用。
