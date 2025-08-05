// 簡化的菜單處理示例
// 這個示例展示了如何使用簡化的API來處理拍照辨識菜單和訂單

class SimpleMenuProcessor {
    constructor() {
        this.menuItems = [];
        this.userLanguage = 'en'; // 預設英語
    }

    // 設置使用者語言
    setLanguage(lang) {
        this.userLanguage = lang;
        console.log(`語言已設置為: ${lang}`);
    }

    // 拍照辨識菜單
    async processMenuPhoto(imageFile) {
        try {
            console.log('開始處理菜單照片...');
            
            const formData = new FormData();
            formData.append('image', imageFile);
            formData.append('target_lang', this.userLanguage);
            
            const response = await fetch('/api/menu/simple-ocr', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.menuItems = result.menu_items;
                console.log('菜單辨識成功:', this.menuItems);
                this.displayMenu();
                return result;
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('菜單辨識失敗:', error);
            alert(`菜單辨識失敗: ${error.message}`);
            throw error;
        }
    }

    // 顯示菜單
    displayMenu() {
        const menuContainer = document.getElementById('menu-container');
        if (!menuContainer) {
            console.error('找不到菜單容器');
            return;
        }

        menuContainer.innerHTML = '';
        
        this.menuItems.forEach((item, index) => {
            const itemElement = document.createElement('div');
            itemElement.className = 'menu-item';
            itemElement.innerHTML = `
                <div class="item-info">
                    <h3>${item.translated_name || item.name}</h3>
                    <p class="description">${item.description || ''}</p>
                    <p class="price">$${item.price}</p>
                </div>
                <div class="item-controls">
                    <button onclick="menuProcessor.decreaseQuantity(${index})">-</button>
                    <span id="quantity-${index}">0</span>
                    <button onclick="menuProcessor.increaseQuantity(${index})">+</button>
                </div>
            `;
            menuContainer.appendChild(itemElement);
        });
    }

    // 增加數量
    increaseQuantity(index) {
        const quantityElement = document.getElementById(`quantity-${index}`);
        let quantity = parseInt(quantityElement.textContent) || 0;
        quantity++;
        quantityElement.textContent = quantity;
        this.updateTotal();
    }

    // 減少數量
    decreaseQuantity(index) {
        const quantityElement = document.getElementById(`quantity-${index}`);
        let quantity = parseInt(quantityElement.textContent) || 0;
        if (quantity > 0) {
            quantity--;
            quantityElement.textContent = quantity;
            this.updateTotal();
        }
    }

    // 更新總金額
    updateTotal() {
        let total = 0;
        this.menuItems.forEach((item, index) => {
            const quantity = parseInt(document.getElementById(`quantity-${index}`).textContent) || 0;
            total += item.price * quantity;
        });
        
        const totalElement = document.getElementById('total-amount');
        if (totalElement) {
            totalElement.textContent = `$${total}`;
        }
    }

    // 獲取選中的項目
    getSelectedItems() {
        const selectedItems = [];
        this.menuItems.forEach((item, index) => {
            const quantity = parseInt(document.getElementById(`quantity-${index}`).textContent) || 0;
            if (quantity > 0) {
                selectedItems.push({
                    name: item.translated_name || item.name,
                    quantity: quantity,
                    price: item.price
                });
            }
        });
        return selectedItems;
    }

    // 提交訂單
    async submitOrder() {
        try {
            const selectedItems = this.getSelectedItems();
            
            if (selectedItems.length === 0) {
                alert('請選擇至少一個商品');
                return;
            }

            console.log('提交訂單:', selectedItems);
            
            const orderData = {
                items: selectedItems,
                user_language: this.userLanguage
            };
            
            const response = await fetch('/api/orders/simple', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(orderData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('訂單提交成功:', result);
                this.displayOrderSummary(result);
                return result;
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('訂單提交失敗:', error);
            alert(`訂單提交失敗: ${error.message}`);
            throw error;
        }
    }

    // 顯示訂單摘要
    displayOrderSummary(orderResult) {
        const summaryContainer = document.getElementById('order-summary');
        if (!summaryContainer) {
            console.error('找不到訂單摘要容器');
            return;
        }

        summaryContainer.innerHTML = `
            <div class="order-success">
                <h2>✅ 訂單提交成功！</h2>
                <p><strong>訂單編號:</strong> ${orderResult.order_id}</p>
                <p><strong>總金額:</strong> $${orderResult.total_amount}</p>
                ${orderResult.voice_url ? `<p><strong>語音檔:</strong> <a href="${orderResult.voice_url}" target="_blank">播放語音</a></p>` : ''}
                <div class="order-details">
                    <h3>訂單詳情:</h3>
                    <pre>${orderResult.summary}</pre>
                </div>
            </div>
        `;
    }
}

// 全域變數
let menuProcessor;

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', function() {
    menuProcessor = new SimpleMenuProcessor();
    
    // 設置語言選擇器
    const languageSelect = document.getElementById('language-select');
    if (languageSelect) {
        languageSelect.addEventListener('change', function() {
            menuProcessor.setLanguage(this.value);
        });
    }
    
    console.log('簡化菜單處理器已初始化');
});

// 拍照上傳處理
async function handlePhotoUpload() {
    const fileInput = document.getElementById('photo-input');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('請選擇照片');
        return;
    }
    
    try {
        await menuProcessor.processMenuPhoto(file);
    } catch (error) {
        console.error('照片處理失敗:', error);
    }
}

// 提交訂單
async function handleSubmitOrder() {
    try {
        await menuProcessor.submitOrder();
    } catch (error) {
        console.error('訂單提交失敗:', error);
    }
} 