/**
 * 前端輪詢範例 - 適用於 LIFF 環境
 * 展示如何實現「短請求 + 輪詢」的新架構
 */

// 配置
const API_BASE_URL = 'https://your-cloud-run-domain.com';
const POLLING_INTERVAL = 2000; // 2秒輪詢一次
const MAX_POLLING_ATTEMPTS = 30; // 最多輪詢30次（60秒）

/**
 * 快速建立訂單（第一步）
 */
async function createQuickOrder(orderData) {
    try {
        console.log('🚀 開始快速建立訂單...');
        
        const response = await fetch(`${API_BASE_URL}/api/orders/quick`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(orderData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('✅ 快速訂單建立成功:', result);
        
        // 開始輪詢訂單狀態
        startPollingOrderStatus(result.order_id);
        
        return result;
        
    } catch (error) {
        console.error('❌ 快速訂單建立失敗:', error);
        showError('訂單建立失敗，請重試');
        throw error;
    }
}

/**
 * 開始輪詢訂單狀態（第二步）
 */
function startPollingOrderStatus(orderId) {
    console.log(`🔄 開始輪詢訂單狀態: order_id=${orderId}`);
    
    // 顯示等待頁面
    showWaitingPage(orderId);
    
    let pollingAttempts = 0;
    
    const pollInterval = setInterval(async () => {
        pollingAttempts++;
        
        try {
            console.log(`📡 輪詢嘗試 ${pollingAttempts}/${MAX_POLLING_ATTEMPTS}`);
            
            const status = await checkOrderStatus(orderId);
            
            if (status.processing === false) {
                // 處理完成或失敗
                clearInterval(pollInterval);
                
                if (status.status === 'completed') {
                    showSuccessPage(status);
                } else if (status.status === 'failed') {
                    showErrorPage(status);
                } else {
                    showUnknownStatusPage(status);
                }
                
            } else {
                // 更新等待頁面的進度
                updateWaitingProgress(pollingAttempts, MAX_POLLING_ATTEMPTS);
            }
            
        } catch (error) {
            console.error('❌ 輪詢失敗:', error);
            
            if (pollingAttempts >= MAX_POLLING_ATTEMPTS) {
                clearInterval(pollInterval);
                showError('輪詢超時，請稍後查看訂單狀態');
            }
        }
    }, POLLING_INTERVAL);
}

/**
 * 查詢訂單狀態
 */
async function checkOrderStatus(orderId) {
    const response = await fetch(`${API_BASE_URL}/api/orders/status/${orderId}`);
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

/**
 * 顯示等待頁面
 */
function showWaitingPage(orderId) {
    const mainContent = document.getElementById('main-content');
    mainContent.innerHTML = `
        <div class="waiting-container text-center">
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">處理中...</span>
            </div>
            <h4>訂單處理中</h4>
            <p class="text-muted">訂單編號: ${orderId}</p>
            <div class="progress mb-3" style="height: 20px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 0%">
                    0%
                </div>
            </div>
            <p class="small text-muted">
                正在生成語音檔案和處理訂單，請稍候...
            </p>
        </div>
    `;
}

/**
 * 更新等待進度
 */
function updateWaitingProgress(current, total) {
    const progressBar = document.querySelector('.progress-bar');
    const percentage = Math.round((current / total) * 100);
    
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
        progressBar.textContent = `${percentage}%`;
    }
}

/**
 * 顯示成功頁面
 */
function showSuccessPage(status) {
    const mainContent = document.getElementById('main-content');
    
    let voiceSection = '';
    if (status.voice_ready && status.voice_url) {
        voiceSection = `
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">
                        <i class="fas fa-volume-up text-success"></i> 語音檔案
                    </h5>
                    <audio controls class="w-100">
                        <source src="${status.voice_url}" type="audio/mpeg">
                        您的瀏覽器不支援音訊播放。
                    </audio>
                    <div class="mt-2">
                        <button class="btn btn-outline-primary btn-sm" 
                                onclick="downloadVoice('${status.voice_url}')">
                            <i class="fas fa-download"></i> 下載語音檔
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    let summarySection = '';
    if (status.summary_ready && status.summary) {
        summarySection = `
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">
                        <i class="fas fa-file-text text-info"></i> 訂單摘要
                    </h5>
                    <div class="row">
                        <div class="col-md-6">
                            <h6>中文摘要</h6>
                            <p class="border rounded p-2 bg-light">${status.summary.chinese}</p>
                        </div>
                        <div class="col-md-6">
                            <h6>翻譯摘要</h6>
                            <p class="border rounded p-2 bg-light">${status.summary.translated}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    mainContent.innerHTML = `
        <div class="success-container text-center">
            <div class="alert alert-success" role="alert">
                <i class="fas fa-check-circle fa-2x mb-2"></i>
                <h4>訂單處理完成！</h4>
                <p>您的訂單已成功建立並處理完成。</p>
            </div>
            
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">訂單資訊</h5>
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>訂單編號:</strong> ${status.order_id}</p>
                            <p><strong>店家名稱:</strong> ${status.store_name}</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>總金額:</strong> NT$ ${status.total_amount}</p>
                            <p><strong>建立時間:</strong> ${new Date(status.order_time).toLocaleString()}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            ${voiceSection}
            ${summarySection}
            
            <div class="mt-4">
                <button class="btn btn-primary me-2" onclick="createNewOrder()">
                    <i class="fas fa-plus"></i> 建立新訂單
                </button>
                <button class="btn btn-outline-secondary" onclick="viewOrderHistory()">
                    <i class="fas fa-history"></i> 查看訂單歷史
                </button>
            </div>
        </div>
    `;
}

/**
 * 顯示錯誤頁面
 */
function showErrorPage(status) {
    const mainContent = document.getElementById('main-content');
    mainContent.innerHTML = `
        <div class="error-container text-center">
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                <h4>訂單處理失敗</h4>
                <p>很抱歉，訂單處理過程中發生錯誤。</p>
                <p class="mb-0">訂單編號: ${status.order_id}</p>
            </div>
            
            <div class="mt-4">
                <button class="btn btn-primary me-2" onclick="retryOrder(${status.order_id})">
                    <i class="fas fa-redo"></i> 重試
                </button>
                <button class="btn btn-outline-secondary" onclick="createNewOrder()">
                    <i class="fas fa-plus"></i> 建立新訂單
                </button>
            </div>
        </div>
    `;
}

/**
 * 顯示未知狀態頁面
 */
function showUnknownStatusPage(status) {
    const mainContent = document.getElementById('main-content');
    mainContent.innerHTML = `
        <div class="unknown-container text-center">
            <div class="alert alert-warning" role="alert">
                <i class="fas fa-question-circle fa-2x mb-2"></i>
                <h4>訂單狀態未知</h4>
                <p>訂單狀態: ${status.status}</p>
                <p class="mb-0">請聯繫客服確認訂單狀態。</p>
            </div>
            
            <div class="mt-4">
                <button class="btn btn-primary" onclick="createNewOrder()">
                    <i class="fas fa-plus"></i> 建立新訂單
                </button>
            </div>
        </div>
    `;
}

/**
 * 顯示錯誤訊息
 */
function showError(message) {
    const mainContent = document.getElementById('main-content');
    mainContent.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="fas fa-exclamation-triangle"></i> ${message}
        </div>
    `;
}

/**
 * 下載語音檔案
 */
function downloadVoice(voiceUrl) {
    const link = document.createElement('a');
    link.href = voiceUrl;
    link.download = `order_voice_${Date.now()}.mp3`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * 建立新訂單
 */
function createNewOrder() {
    // 重新載入頁面或跳轉到訂單建立頁面
    window.location.reload();
}

/**
 * 重試訂單
 */
function retryOrder(orderId) {
    // 重新開始輪詢
    startPollingOrderStatus(orderId);
}

/**
 * 查看訂單歷史
 */
function viewOrderHistory() {
    // 跳轉到訂單歷史頁面
    console.log('跳轉到訂單歷史頁面');
}

// 使用範例
document.addEventListener('DOMContentLoaded', function() {
    // 範例：當使用者點擊確認訂單按鈕時
    const confirmOrderBtn = document.getElementById('confirm-order-btn');
    if (confirmOrderBtn) {
        confirmOrderBtn.addEventListener('click', async function() {
            // 準備訂單資料
            const orderData = {
                store_name: '範例店家',
                store_id: 1,
                line_user_id: 'U1234567890abcdef',
                items: [
                    {
                        menu_item_id: 1,
                        item_name: '牛肉麵',
                        translated_name: 'Beef Noodle Soup',
                        price: 120,
                        quantity: 1
                    }
                ],
                total_amount: 120,
                language: 'zh'
            };
            
            try {
                await createQuickOrder(orderData);
            } catch (error) {
                console.error('訂單建立失敗:', error);
            }
        });
    }
});

console.log('✅ 前端輪詢範例已載入');
