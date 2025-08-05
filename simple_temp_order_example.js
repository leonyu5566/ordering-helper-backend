// 簡化的臨時訂單範例
// 用於非合作店家的拍照點餐功能

// 主要訂單提交函數
async function submitTempOrder() {
    try {
        // 1. 取得購物車資料（從拍照辨識結果）
        const tempItems = getTempOrderItems(); // 你的臨時訂單資料
        
        if (!tempItems || tempItems.length === 0) {
            alert('沒有選擇任何商品');
            return;
        }
        
        // 2. 準備訂單項目（簡化格式）
        const orderItems = tempItems.map(item => ({
            item_name: item.original_name || item.item_name || item.name,
            quantity: item.quantity || item.qty || 1,
            price: item.price || item.price_small || item.price_unit || 0
        })).filter(item => 
            item.item_name && 
            item.quantity > 0 && 
            item.price > 0
        );
        
        if (orderItems.length === 0) {
            alert('沒有有效的訂單項目');
            return;
        }
        
        // 3. 準備請求資料
        const tempOrderData = {
            line_user_id: getCurrentUserId(), // 可選
            language: getUserLanguage(),
            items: orderItems
        };
        
        console.log('發送臨時訂單資料:', tempOrderData);
        
        // 4. 發送請求
        const response = await fetch('/api/orders/temp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(tempOrderData)
        });
        
        // 5. 處理回應
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
        
        // 6. 處理成功回應
        const result = await response.json();
        console.log('臨時訂單建立成功:', result);
        
        // 7. 顯示成功訊息
        alert(`臨時訂單建立成功！\n訂單編號: ${result.order_id}\n總金額: $${result.total_amount}`);
        
        // 8. 清空臨時訂單
        clearTempOrder();
        
        // 9. 可選：顯示訂單摘要
        if (result.order_summary) {
            displayOrderSummary(result.order_summary);
        }
        
    } catch (error) {
        console.error('臨時訂單提交失敗:', error);
        alert(`臨時訂單送出失敗：${error.message}`);
    }
}

// 輔助函數
function getCurrentUserId() {
    // 檢查是否在 LIFF 環境中
    if (typeof liff !== 'undefined' && liff.isLoggedIn()) {
        try {
            const profile = liff.getProfile();
            return profile.userId; // LINE 使用者 ID
        } catch (error) {
            console.error('無法取得 LINE 使用者資料:', error);
        }
    }
    
    // 非 LIFF 環境或取得失敗時，使用訪客 ID
    return `guest_${crypto.randomUUID().slice(0, 8)}`;
}

function getUserLanguage() {
    // 從 URL 參數或瀏覽器語言取得
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('lang') || navigator.language.split('-')[0] || 'zh';
}

function getTempOrderItems() {
    // 實作你的臨時訂單資料取得邏輯
    // 這通常是從拍照辨識結果中取得的
    return window.tempOrderItems || [];
}

function clearTempOrder() {
    // 實作你的臨時訂單清空邏輯
    window.tempOrderItems = [];
    updateTempOrderUI();
}

function updateTempOrderUI() {
    // 實作你的臨時訂單UI更新邏輯
    console.log('更新臨時訂單UI');
}

function displayOrderSummary(orderSummary) {
    // 顯示訂單摘要
    console.log('訂單摘要:', orderSummary);
    
    // 可以在這裡實作訂單摘要的顯示邏輯
    // 例如：顯示在彈出視窗中，或導向到訂單確認頁面
}

// 使用範例
// 假設你有一個拍照辨識的結果
function handleMenuPhotoRecognition(recognizedItems) {
    // 將辨識結果轉換為訂單項目
    window.tempOrderItems = recognizedItems.map(item => ({
        original_name: item.name,
        quantity: 1, // 預設數量
        price: item.price
    }));
    
    // 更新UI
    updateTempOrderUI();
}

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('臨時訂單系統已載入');
    
    // 如果有拍照辨識結果，可以自動處理
    if (window.recognizedMenuItems) {
        handleMenuPhotoRecognition(window.recognizedMenuItems);
    }
}); 