# OCR 資料庫相容性修改

## 🔍 **問題分析**

你說得非常對！既然 gae252 專案是 GCP Cloud MySQL 資料庫的程式碼，我們必須讓我們的後端能夠與他們的資料庫結構相容。

### **原始問題**
```
(pymysql.err.ProgrammingError) (1146, "Table 'gae252g1_db.gemini_processing' doesn't exist")
```

### **根本原因**
我們的後端使用了 `gemini_processing` 表，但 gae252 專案的資料庫使用的是 `ocr_menus` 和 `ocr_menu_items` 表。

## 🛠️ **修改方案**

### **1. 新增 OCR 模型**

在 `app/models.py` 中新增了符合同事資料庫結構的模型：

```python
class OCRMenu(db.Model):
    """OCR 菜單主檔（符合同事的資料庫結構）"""
    __tablename__ = 'ocr_menus'
    
    ocr_menu_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    store_name = db.Column(db.String(100))  # 非合作店家名稱
    upload_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # 關聯到菜單項目
    items = db.relationship('OCRMenuItem', backref='ocr_menu', lazy=True, cascade="all, delete-orphan")

class OCRMenuItem(db.Model):
    """OCR 菜單品項（符合同事的資料庫結構）"""
    __tablename__ = 'ocr_menu_items'
    
    ocr_menu_item_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    ocr_menu_id = db.Column(db.BigInteger, db.ForeignKey('ocr_menus.ocr_menu_id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)  # 品項名稱
    price_big = db.Column(db.Integer)  # 大份量價格
    price_small = db.Column(db.Integer, nullable=False)  # 小份量價格
    translated_desc = db.Column(db.Text)  # 翻譯後介紹
```

### **2. 修改 OCR 處理流程**

修改了 `process_menu_ocr` 端點，使用 `ocr_menus` 和 `ocr_menu_items` 表：

```python
# 建立 OCR 菜單記錄（符合同事的資料庫結構）
from app.models import OCRMenu, OCRMenuItem

# 先處理圖片獲取店家資訊
result = process_menu_with_gemini(filepath, target_lang)

if result and result.get('success', False):
    # 建立 OCR 菜單記錄
    ocr_menu = OCRMenu(
        user_id=user_id or 1,
        store_name=result.get('store_info', {}).get('name', '臨時店家')
    )
    db.session.add(ocr_menu)
    db.session.flush()  # 獲取 ocr_menu_id
    
    # 儲存菜單項目到資料庫
    menu_items = result.get('menu_items', [])
    for item in menu_items:
        ocr_menu_item = OCRMenuItem(
            ocr_menu_id=ocr_menu.ocr_menu_id,
            item_name=str(item.get('original_name', '') or ''),
            price_small=item.get('price', 0),
            price_big=item.get('price', 0),
            translated_desc=str(item.get('translated_name', '') or '')
        )
        db.session.add(ocr_menu_item)
    
    # 提交資料庫變更
    db.session.commit()
```

### **3. 資料庫表結構對比**

| 功能 | gae252 專案 | 我們的修改後 |
|------|-------------|-------------|
| OCR 菜單主檔 | `ocr_menus` | `ocr_menus` ✅ |
| OCR 菜單項目 | `ocr_menu_items` | `ocr_menu_items` ✅ |
| 欄位結構 | 完全一致 | 完全一致 ✅ |

### **4. 創建資料庫表腳本**

新增了 `tools/create_ocr_tables.py` 腳本：

```bash
python3 tools/create_ocr_tables.py
```

這個腳本會：
- 檢查並創建 `ocr_menus` 表
- 檢查並創建 `ocr_menu_items` 表
- 驗證表結構是否正確
- 測試表功能

## ✅ **優勢**

### **1. 完全相容**
- 使用與 gae252 專案相同的表名稱
- 使用相同的欄位結構
- 使用相同的外鍵關係

### **2. 保持功能**
- 前端 API 回應格式不變
- 處理流程保持不變
- 錯誤處理保持不變

### **3. 向後相容**
- 保留原有的 `GeminiProcessing` 模型（可選）
- 可以同時支援兩種表結構
- 平滑遷移

## 🚀 **部署步驟**

### **1. 本地測試**
```bash
# 創建 OCR 表
python3 tools/create_ocr_tables.py

# 測試應用程式
python3 -c "from app import create_app; app = create_app(); print('✅ 應用程式啟動成功')"
```

### **2. Cloud Run 部署**
```bash
# 部署到 Cloud Run
python3 deploy_simplified_version.py
```

### **3. 驗證功能**
- 測試 OCR 處理功能
- 確認資料正確儲存到 `ocr_menus` 和 `ocr_menu_items` 表
- 確認前端顯示正常

## 🎯 **結論**

這次修改解決了根本問題：

1. **資料庫相容性**：使用與 gae252 專案相同的表結構
2. **功能完整性**：保持所有原有功能
3. **部署可靠性**：不再依賴不存在的 `gemini_processing` 表

現在我們的後端可以正確地與 gae252 專案的 GCP Cloud MySQL 資料庫配合工作！ 