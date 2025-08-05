// 前端訂單建立範例程式碼
// 展示最佳的實作方式，與後端完全相容

async function submitOrder() {
    try {
        // 1. 準備購物車資料
        const cartItems = getCartItems(); // 你的購物車資料
        
        // 2. 驗證購物車資料
        if (!cartItems || cartItems.length === 0) {
            alert('購物車是空的，請先選擇商品');
            return;
        }
        
        // 3. 建立訂單項目（支援多種格式）
        const orderItems = cartItems.map(item => {
            // 找到對應的菜單項目
            const menuItem = currentMenuItems.find(i => 
                (i.id == item.menu_item_id) || 
                (i.menu_item_id == item.menu_item_id) || 
                (i.temp_id == item.menu_item_id)
            );
            
            if (!menuItem) {
                console.warn('找不到菜單項目:', item);
                return null;
            }
            
            // 驗證價格
            const price = menuItem.price_small || menuItem.price || 0;
            if (!price || isNaN(price) || price <= 0) {
                console.warn('商品價格無效:', menuItem);
                return null;
            }
            
            // 驗證數量
            const quantity = item.quantity || item.qty || 0;
            if (!quantity || quantity <= 0) {
                console.warn('商品數量無效:', item);
                return null;
            }
            
            return {
                // 支援多種欄位名稱（後端會自動處理）
                menu_item_id: menuItem.menu_item_id || menuItem.id || menuItem.temp_id,
                quantity: quantity,  // 後端也支援 qty
                price_unit: price,   // 後端也支援 price 或 price_small
                
                // 額外資訊（可選）
                item_name: menuItem.item_name || menuItem.original_name,
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
            line_user_id: getCurrentUserId(), // 你的使用者ID取得方式
            store_id: getCurrentStoreId(),    // 你的店家ID取得方式
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
            if (errorData.validation_errors) {
                const errorMessage = errorData.validation_errors.join('\n');
                alert(`訂單資料驗證失敗：\n${errorMessage}`);
            } else if (errorData.missing_fields) {
                const missingFields = errorData.missing_fields.join(', ');
                alert(`缺少必要欄位：${missingFields}`);
            } else {
                alert(`訂單建立失敗：${errorData.error}`);
            }
            return;
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
        alert('訂單提交失敗，請稍後再試');
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
            
            if (errorData.validation_errors) {
                const errorMessage = errorData.validation_errors.join('\n');
                alert(`臨時訂單驗證失敗：\n${errorMessage}`);
            } else {
                alert(`臨時訂單建立失敗：${errorData.error}`);
            }
            return;
        }
        
        const result = await response.json();
        console.log('臨時訂單建立成功:', result);
        
        alert(`臨時訂單建立成功！\n總金額: $${result.total_amount}`);
        
    } catch (error) {
        console.error('臨時訂單提交失敗:', error);
        alert('臨時訂單提交失敗，請稍後再試');
    }
}

// 除錯函數：檢查資料格式
async function debugOrderData(orderData) {
    try {
        const response = await fetch('/api/debug/order-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        
        const result = await response.json();
        console.log('資料格式分析:', result);
        
        if (result.analysis) {
            console.log('驗證結果:', result.analysis.validation_results);
        }
        
        return result;
        
    } catch (error) {
        console.error('除錯請求失敗:', error);
    }
}

// 使用範例
// debugOrderData({
//     line_user_id: "test_user",
//     store_id: 1,
//     items: [
//         {
//             id: 1,
//             qty: 2,
//             price: 100
//         }
//     ]
// }); 