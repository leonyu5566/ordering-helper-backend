# =============================================================================
# Cloud Tasks 配置檔案
# 功能：集中管理 Cloud Tasks 相關設定，方便組員修改
# =============================================================================

import os

# =============================================================================
# 基本設定
# =============================================================================

# Google Cloud 專案設定
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'solid-heaven-466011-d1')
GCP_LOCATION = os.environ.get('GCP_LOCATION', 'asia-east1')

# Cloud Tasks 佇列設定
CLOUD_TASKS_QUEUE_NAME = os.environ.get('CLOUD_TASKS_QUEUE_NAME', 'order-processing-queue')

# Cloud Run 服務設定
CLOUD_RUN_SERVICE_NAME = os.environ.get('CLOUD_RUN_SERVICE_NAME', 'ordering-helper-backend')
CLOUD_RUN_SERVICE_URL = os.environ.get(
    'CLOUD_RUN_SERVICE_URL', 
    'https://ordering-helper-backend-00690-mh5-asia-east1.run.app'
)

# 服務帳戶設定
TASKS_INVOKER_SERVICE_ACCOUNT = os.environ.get(
    'TASKS_INVOKER_SERVICE_ACCOUNT', 
    'tasks-invoker@solid-heaven-466011-d1.iam.gserviceaccount.com'
)

# =============================================================================
# 任務處理端點設定
# =============================================================================

# 背景任務處理端點
ORDER_PROCESSING_ENDPOINT = '/api/orders/process-task'

# =============================================================================
# 佇列配置設定
# =============================================================================

# 佇列配置（用於創建佇列時的設定）
QUEUE_CONFIG = {
    'max_concurrent_dispatches': 10,  # 最大並發數
    'max_dispatches_per_second': 500,  # 每秒最大調度數
    'max_attempts': 5,  # 最大重試次數
    'max_retry_duration': '10s',  # 最大重試時間
    'min_backoff': '5s',  # 最小重試間隔
    'max_backoff': '60s',  # 最大重試間隔
    'max_doublings': 3,  # 最大重試倍數
}

# =============================================================================
# 任務配置設定
# =============================================================================

# 任務配置（用於創建任務時的設定）
TASK_CONFIG = {
    'dispatch_deadline': '30m',  # 任務執行超時時間
    'schedule_time': None,  # 排程時間（None 表示立即執行）
}

# =============================================================================
# 獲取完整 URL 的輔助函數
# =============================================================================

def get_order_processing_url():
    """獲取訂單處理端點的完整 URL"""
    # 確保 URL 格式正確，避免重複斜線
    base_url = CLOUD_RUN_SERVICE_URL.rstrip('/')
    endpoint = ORDER_PROCESSING_ENDPOINT.lstrip('/')
    return f"{base_url}/{endpoint}"

def get_queue_path():
    """獲取佇列路徑"""
    return f"projects/{GCP_PROJECT_ID}/locations/{GCP_LOCATION}/queues/{CLOUD_TASKS_QUEUE_NAME}"

# =============================================================================
# 配置驗證函數
# =============================================================================

def validate_config():
    """驗證配置是否正確"""
    required_vars = [
        'GCP_PROJECT_ID',
        'GCP_LOCATION', 
        'CLOUD_TASKS_QUEUE_NAME',
        'CLOUD_RUN_SERVICE_URL',
        'TASKS_INVOKER_SERVICE_ACCOUNT'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not globals().get(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"缺少必要的配置變數: {missing_vars}")
    
    # 驗證 URL 格式
    if not CLOUD_RUN_SERVICE_URL.startswith(('http://', 'https://')):
        raise ValueError(f"無效的服務 URL 格式: {CLOUD_RUN_SERVICE_URL}")
    
    # 驗證服務帳戶格式
    if '@' not in TASKS_INVOKER_SERVICE_ACCOUNT or '.iam.gserviceaccount.com' not in TASKS_INVOKER_SERVICE_ACCOUNT:
        raise ValueError(f"無效的服務帳戶格式: {TASKS_INVOKER_SERVICE_ACCOUNT}")
    
    # 測試 URL 構建
    test_url = get_order_processing_url()
    print(f"🔧 測試 URL 構建: {test_url}")
    
    print("✅ Cloud Tasks 配置驗證通過")
    print(f"   - 專案 ID: {GCP_PROJECT_ID}")
    print(f"   - 位置: {GCP_LOCATION}")
    print(f"   - 佇列名稱: {CLOUD_TASKS_QUEUE_NAME}")
    print(f"   - 服務 URL: {CLOUD_RUN_SERVICE_URL}")
    print(f"   - 服務帳戶: {TASKS_INVOKER_SERVICE_ACCOUNT}")
    print(f"   - 處理端點 URL: {test_url}")

# =============================================================================
# 配置說明
# =============================================================================

"""
配置說明：

1. 環境變數設定（可選）：
   - GCP_PROJECT_ID: Google Cloud 專案 ID
   - GCP_LOCATION: 服務位置
   - CLOUD_TASKS_QUEUE_NAME: Cloud Tasks 佇列名稱
   - CLOUD_RUN_SERVICE_URL: Cloud Run 服務 URL
   - TASKS_INVOKER_SERVICE_ACCOUNT: 服務帳戶郵箱

2. 修改方式：
   - 直接修改此檔案中的預設值
   - 或在環境變數中設定對應的值
   - 環境變數優先級高於檔案中的預設值

3. 重要提醒：
   - 確保 TASKS_INVOKER_SERVICE_ACCOUNT 有適當的權限
   - 確保 CLOUD_RUN_SERVICE_URL 是正確的服務 URL
   - 確保佇列已在 Google Cloud Console 中創建
"""
