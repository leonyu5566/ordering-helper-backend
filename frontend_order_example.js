// 前端訂單建立範例程式碼
// 展示最佳的實作方式，與後端完全相容

// 取得使用者 ID 的函數
async function getCurrentUserId() {
    // 檢查是否在 LIFF 環境中
    if (typeof liff !== 'undefined' && liff.isLoggedIn()) {
        try {
            const profile = await liff.getProfile();
            return profile.userId; // LINE 使用者 ID
        } catch (error) {
            console.error('無法取得 LINE 使用者資料:', error);
        }
    }
    
    // 非 LIFF 環境或取得失敗時，使用訪客 ID
    return `guest_${crypto.randomUUID().slice(0, 8)}`;
}

// 取得當前店家 ID
function getCurrentStoreId() {
    // 從 URL 參數或全域變數取得
    const urlParams = new URLSearchParams(window.location.search);
    return parseInt(urlParams.get('store_id')) || 1; // 預設店家 ID
}

// 取得使用者語言偏好
function getUserLanguage() {
    // 從 URL 參數或瀏覽器語言取得
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('lang') || navigator.language.split('-')[0] || 'zh';
}

// 主要訂單提交函數
async function submitOrder() {
    try {
        // 1. 取得購物車資料
        const cartItems = getCartItems(); // 你的購物車資料取得方式
        
        if (!cartItems || cartItems.length === 0) {
            alert('購物車是空的');
            return;
        }
        
        // 2. 取得使用者 ID
        const lineUserId = await getCurrentUserId();
        console.log('使用者 ID:', lineUserId);
        
        // 3. 準備訂單項目
        const orderItems = cartItems.map(item => {
            const price = item.price_small || item.price || 0;
            const quantity = item.quantity || item.qty || 0;
            
            if (!item.menu_item_id && !item.id) {
                console.warn('項目缺少 ID:', item);
                return null;
            }
            
            return {
                menu_item_id: item.menu_item_id || item.id,
                quantity: quantity,
                price_unit: price,
                subtotal: price * quantity
            };
        }).filter(Boolean); // 過濾掉無效項目
        
        if (orderItems.length === 0) {
            alert('沒有有效的訂單項目');
            return;
        }
        
        // 4. 計算總金額
        const total = orderItems.reduce((sum, item) => sum + item.subtotal, 0);
        
        // 5. 準備請求資料
        const orderData = {
            line_user_id: lineUserId, // 現在是可選的
            store_id: getCurrentStoreId(),
            language: getUserLanguage(),
            items: orderItems,
            total: total  // 可選，後端會重新計算
        };
        
        console.log('發送訂單資料:', orderData);
        
        // 6. 發送請求
        const response = await fetch('/api/orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        
        // 7. 處理回應
        if (!response.ok) {
            const errorData = await response.json();
            console.error('後端錯誤:', errorData);
            
            // 顯示詳細的錯誤訊息
            let errorMessage = '訂單建立失敗';
            if (errorData.validation_errors) {
                errorMessage = `資料驗證失敗：\n${errorData.validation_errors.join('\n')}`;
            } else if (errorData.missing_fields) {
                errorMessage = `缺少必要欄位：${errorData.missing_fields.join(', ')}`;
            } else if (errorData.detail) {
                errorMessage = errorData.detail;
            } else if (errorData.message) {
                errorMessage = errorData.message;
            } else if (errorData.error) {
                errorMessage = errorData.error;
            } else {
                errorMessage = `${response.statusText} (${response.status})`;
            }
            
            throw new Error(errorMessage);
        }
        
        // 8. 處理成功回應
        const result = await response.json();
        console.log('訂單建立成功:', result);
        
        // 9. 更新UI
        alert(`訂單建立成功！\n訂單編號: ${result.order_id}\n總金額: $${result.total_amount}`);
        
        // 10. 清空購物車
        clearCart();
        
    } catch (error) {
        console.error('訂單提交失敗:', error);
        alert(`訂單送出失敗：${error.message}`);
    }
}

// 臨時訂單建立（非合作店家）
async function submitTempOrder() {
    try {
        const tempItems = getTempOrderItems(); // 你的臨時訂單資料
        
        if (!tempItems || tempItems.length === 0) {
            alert('沒有選擇任何商品');
            return;
        }
        
        // 建立臨時訂單項目
        const orderItems = tempItems.map(item => ({
            // 支援多種欄位名稱
            original_name: item.original_name || item.item_name || item.name,
            translated_name: item.translated_name || item.original_name,
            quantity: item.quantity || item.qty || 1,
            price: item.price || item.price_small || item.price_unit || 0,
            temp_id: item.temp_id || item.id
        })).filter(item => 
            item.original_name && 
            item.quantity > 0 && 
            item.price > 0
        );
        
        if (orderItems.length === 0) {
            alert('沒有有效的訂單項目');
            return;
        }
        
        const total = orderItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        
        const tempOrderData = {
            processing_id: getCurrentProcessingId(), // 你的處理ID取得方式
            items: orderItems,
            total: total
        };
        
        console.log('發送臨時訂單資料:', tempOrderData);
        
        const response = await fetch('/api/orders/temp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(tempOrderData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('臨時訂單錯誤:', errorData);
            
            let errorMessage = '臨時訂單建立失敗';
            if (errorData.validation_errors) {
                errorMessage = `資料驗證失敗：\n${errorData.validation_errors.join('\n')}`;
            } else if (errorData.missing_fields) {
                errorMessage = `缺少必要欄位：${errorData.missing_fields.join(', ')}`;
            } else if (errorData.error) {
                errorMessage = errorData.error;
            }
            
            throw new Error(errorMessage);
        }
        
        const result = await response.json();
        console.log('臨時訂單建立成功:', result);
        
        alert(`臨時訂單建立成功！\n處理編號: ${result.processing_id}`);
        
        // 清空臨時訂單
        clearTempOrder();
        
    } catch (error) {
        console.error('臨時訂單提交失敗:', error);
        alert(`臨時訂單送出失敗：${error.message}`);
    }
}

// 輔助函數
function getCartItems() {
    // 實作你的購物車資料取得邏輯
    return window.cart || [];
}

function clearCart() {
    // 實作你的購物車清空邏輯
    window.cart = [];
    updateCartUI();
}

function getTempOrderItems() {
    // 實作你的臨時訂單資料取得邏輯
    return window.tempOrderItems || [];
}

function clearTempOrder() {
    // 實作你的臨時訂單清空邏輯
    window.tempOrderItems = [];
    updateTempOrderUI();
}

function getCurrentProcessingId() {
    // 實作你的處理ID取得邏輯
    return window.processingId || Date.now();
}

function updateCartUI() {
    // 實作你的購物車UI更新邏輯
    console.log('更新購物車UI');
}

function updateTempOrderUI() {
    // 實作你的臨時訂單UI更新邏輯
    console.log('更新臨時訂單UI');
}

// LIFF 初始化（如果需要的話）
async function initializeLiff() {
    if (typeof liff !== 'undefined') {
        try {
            await liff.init({ liffId: 'YOUR_LIFF_ID' });
            console.log('LIFF 初始化成功');
        } catch (error) {
            console.error('LIFF 初始化失敗:', error);
        }
    }
}

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeLiff();
}); 