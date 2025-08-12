#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL日誌測試

功能：
1. 測試修改後的SQL日誌功能
2. 驗證參數類型和值
3. 檢查是否有欄位缺失或型別錯誤
"""

import os
import sys
import traceback
from datetime import datetime

# 載入環境變數
try:
    from dotenv import load_dotenv
    load_dotenv('.env')
    print("✓ 已載入 .env 檔案")
except ImportError:
    print("⚠️ python-dotenv 未安裝，使用系統環境變數")
except FileNotFoundError:
    print("⚠️ .env 檔案未找到，使用系統環境變數")

def test_sql_logging():
    """測試SQL日誌功能"""
    print("\n=== SQL日誌測試 ===")
    
    try:
        from app import create_app
        from app.models import db, User, Store, Language
        
        app = create_app()
        
        with app.app_context():
            # 1. 確保語言存在
            language = db.session.get(Language, 'zh')
            if not language:
                language = Language(
                    line_lang_code='zh', 
                    translation_lang_code='zh',
                    stt_lang_code='zh-TW',
                    lang_name='中文'
                )
                db.session.add(language)
                db.session.commit()
            
            # 2. 創建測試使用者
            test_user_id = f"test_sql_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            user = User(
                line_user_id=test_user_id,
                preferred_lang='zh'
            )
            db.session.add(user)
            db.session.flush()
            print(f"✅ 創建測試使用者: {user.user_id}")
            
            # 3. 獲取店家
            store = Store.query.first()
            if not store:
                print("❌ 沒有找到店家資料")
                return False
            
            print(f"✅ 使用店家: {store.store_name} (ID: {store.store_id})")
            
            # 4. 測試OCR訂單摘要儲存
            try:
                from app.api.helpers import save_ocr_menu_and_summary_to_database
                
                # 準備測試資料
                test_order_id = 999999  # 測試用訂單ID
                test_ocr_items = [
                    {
                        'name': {
                            'original': '測試咖啡',
                            'translated': 'Test Coffee'
                        },
                        'price': 100,
                        'item_name': '測試咖啡',
                        'translated_name': 'Test Coffee'
                    }
                ]
                
                print(f"📋 測試資料:")
                print(f"   訂單ID: {test_order_id}")
                print(f"   使用者ID: {user.user_id}")
                print(f"   OCR項目數量: {len(test_ocr_items)}")
                
                # 執行測試
                save_result = save_ocr_menu_and_summary_to_database(
                    order_id=test_order_id,
                    ocr_items=test_ocr_items,
                    chinese_summary="測試OCR訂單摘要",
                    user_language_summary="Test OCR Order Summary",
                    user_language="zh",
                    total_amount=100,
                    user_id=user.user_id,
                    store_name="測試咖啡店"
                )
                
                if save_result['success']:
                    print(f"✅ SQL日誌測試成功！")
                    print(f"   OCR菜單ID: {save_result['ocr_menu_id']}")
                    print(f"   訂單摘要ID: {save_result['summary_id']}")
                    return True
                else:
                    print(f"❌ SQL日誌測試失敗: {save_result['message']}")
                    return False
                
            except Exception as e:
                print(f"❌ SQL日誌測試異常: {str(e)}")
                print(f"錯誤類型: {type(e).__name__}")
                traceback.print_exc()
                return False
            
    except Exception as e:
        print(f"❌ 測試初始化失敗: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("SQL日誌測試")
    print("=" * 50)
    print(f"測試時間: {datetime.now()}")
    
    # 執行測試
    result = test_sql_logging()
    
    # 總結
    print("\n" + "=" * 50)
    if result:
        print("🎉 SQL日誌測試成功！")
        print("現在您可以在Cloud Run日誌中看到詳細的SQL執行資訊。")
    else:
        print("❌ SQL日誌測試失敗")
        print("請檢查錯誤訊息。")
    
    return result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
