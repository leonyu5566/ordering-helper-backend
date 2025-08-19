# gTTS 遷移總結

## 修改概述

已成功將語音生成功能從 Azure Speech 遷移到 gTTS（Google Text-to-Speech），以簡化部署和減少依賴。

## 主要修改內容

### 1. 依賴項更新
- **移除**: `azure-cognitiveservices-speech==1.34.0`
- **新增**: `gTTS==2.4.0`

### 2. 語音生成函數修改

#### 主要函數
- `generate_voice_order()` - 主要語音生成函數
- `generate_voice_from_temp_order()` - 臨時訂單語音生成
- `generate_voice_with_custom_rate()` - 自定義語速語音生成
- `generate_chinese_voice_with_azure()` - 中文語音生成（函數名保持不變，但內部實現已更改）
- `synthesize_azure_tts()` - 異步語音合成（函數名保持不變，但內部實現已更改）
- `generate_voice_order_enhanced()` - 增強版語音生成
- `generate_voice_with_custom_rate_enhanced()` - 增強版自定義語音生成

#### 配置函數
- `get_speech_config()` - 改為返回模擬配置對象，實際使用 gTTS
- `cleanup_old_voice_files()` - 改為清理 .mp3 檔案而不是 .wav 檔案

### 3. 技術變更

#### 檔案格式
- **之前**: `.wav` 檔案
- **現在**: `.mp3` 檔案

#### 語音參數
- **語速控制**: gTTS 只支援 `slow` 參數（布林值），不支援精確的語速倍率
- **情感風格**: gTTS 不支援情感風格設定
- **HD 聲音**: gTTS 不支援 HD 聲音選項

#### 持續時間計算
- **之前**: 使用 Azure Speech 提供的精確持續時間
- **現在**: 根據文字長度估算（每個中文字符約 0.5 秒）

### 4. 相容性保持

為了保持向後相容性：
- 所有函數名稱保持不變
- 函數參數保持不變
- 返回值格式保持不變
- 錯誤處理邏輯保持不變

## 優勢

### 1. 簡化部署
- 不需要 Azure Speech 服務配置
- 不需要 Azure 訂閱和金鑰
- 減少環境變數依賴

### 2. 降低成本
- gTTS 是免費的 Google 服務
- 不需要 Azure Speech 的付費訂閱

### 3. 提高穩定性
- 減少外部服務依賴
- 降低服務中斷風險

## 限制

### 1. 功能限制
- 不支援精確的語速控制
- 不支援情感風格設定
- 不支援 HD 聲音品質

### 2. 品質差異
- gTTS 的語音品質可能不如 Azure Speech
- 語音自然度可能有所降低

## 部署注意事項

### 1. 環境變數
不再需要以下環境變數：
- `AZURE_SPEECH_KEY`
- `AZURE_SPEECH_REGION`

### 2. 網路要求
- gTTS 需要網路連接來生成語音
- 確保容器有網路訪問權限

### 3. 檔案格式
- 前端需要支援播放 .mp3 檔案
- 確保音訊播放器相容性

## 測試建議

### 1. 功能測試
- 測試所有語音生成端點
- 驗證語音檔案格式和品質
- 檢查語音播放功能

### 2. 效能測試
- 測試語音生成速度
- 檢查記憶體使用情況
- 驗證檔案清理功能

### 3. 錯誤處理
- 測試網路中斷情況
- 驗證錯誤回退機制
- 檢查日誌輸出

## 回滾方案

如果需要回滾到 Azure Speech：
1. 恢復 `azure-cognitiveservices-speech==1.34.0` 依賴
2. 恢復所有語音生成函數的原始實現
3. 重新配置 Azure Speech 環境變數
4. 更新檔案格式處理邏輯

## 總結

這次遷移成功將語音生成功能從 Azure Speech 遷移到 gTTS，簡化了部署流程，降低了成本，並保持了向後相容性。雖然在功能上有一些限制，但對於基本的語音生成需求來說已經足夠。
