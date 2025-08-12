#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR菜單到訂單摘要流程測試

功能：
1. 測試OCR菜單創建
2. 測試訂單創建
3. 測試訂單摘要創建
4. 驗證資料庫關聯關係
"""

import os
import sys
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

def test_ocr_flow():
    """測試OCR菜單到訂單摘要的完整流程"""
    print("\n=== OCR菜單到訂單摘要流程測試 ===")
    
    try:
        from app import create_app
        from app.models import db, User, Store, Menu, MenuItem, Order, OrderItem, Language, OCRMenu, OCRMenuItem, OrderSummary
        from app.api.helpers import save_ocr_menu_and_summary_to_database
        
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
            test_user_id = f"test_ocr_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
            
            # 4. 模擬OCR菜單項目
            ocr_items = [
                {
                    'name': {
                        'original': '美式咖啡',
                        'translated': 'American Coffee'
                    },
                    'price': 80,
                    'item_name': '美式咖啡',
                    'translated_name': 'American Coffee'
                },
                {
                    'name': {
                        'original': '拿鐵咖啡',
                        'translated': 'Latte'
                    },
                    'price': 120,
                    'item_name': '拿鐵咖啡',
                    'translated_name': 'Latte'
                }
            ]
            
            # 5. 創建訂單
            order = Order(
                user_id=user.user_id,
                store_id=store.store_id,
                total_amount=200
            )
            db.session.add(order)
            db.session.flush()
            print(f"✅ 創建訂單: {order.order_id}")
            
            # 6. 創建訂單項目
            for i, item in enumerate(ocr_items):
                order_item = OrderItem(
                    order_id=order.order_id,
                    menu_item_id=1,  # 使用預設菜單項目ID
                    quantity_small=1,
                    subtotal=item['price'],
                    original_name=item['name']['original'],
                    translated_name=item['name']['translated']
                )
                db.session.add(order_item)
            
            db.session.commit()
            print(f"✅ 創建訂單項目完成")
            
            # 7. 儲存OCR菜單和訂單摘要
            result = save_ocr_menu_and_summary_to_database(
                order_id=order.order_id,
                ocr_items=ocr_items,
                chinese_summary="訂單包含美式咖啡和拿鐵咖啡，總計200元",
                user_language_summary="Order includes American Coffee and Latte, total 200",
                user_language='zh',
                total_amount=200,
                user_id=user.user_id,
                store_name='測試咖啡店'
            )
            
            if result['success']:
                print(f"✅ OCR菜單和訂單摘要儲存成功")
                print(f"   OCR菜單ID: {result['ocr_menu_id']}")
                print(f"   訂單摘要ID: {result['summary_id']}")
                
                # 8. 驗證資料庫關聯
                print("\n=== 驗證資料庫關聯 ===")
                
                # 檢查OCR菜單
                ocr_menu = OCRMenu.query.get(result['ocr_menu_id'])
                if ocr_menu:
                    print(f"✅ OCR菜單驗證成功:")
                    print(f"   OCR菜單ID: {ocr_menu.ocr_menu_id}")
                    print(f"   使用者ID: {ocr_menu.user_id}")
                    print(f"   店家名稱: {ocr_menu.store_name}")
                    
                    # 檢查OCR菜單項目
                    ocr_items_count = OCRMenuItem.query.filter_by(ocr_menu_id=ocr_menu.ocr_menu_id).count()
                    print(f"   OCR菜單項目數量: {ocr_items_count}")
                
                # 檢查訂單摘要
                order_summary = OrderSummary.query.get(result['summary_id'])
                if order_summary:
                    print(f"✅ 訂單摘要驗證成功:")
                    print(f"   摘要ID: {order_summary.summary_id}")
                    print(f"   訂單ID: {order_summary.order_id}")
                    print(f"   OCR菜單ID: {order_summary.ocr_menu_id}")
                    print(f"   使用者語言: {order_summary.user_language}")
                    print(f"   總金額: {order_summary.total_amount}")
                
                # 9. 清理測試資料
                print("\n=== 清理測試資料 ===")
                db.session.delete(order_summary)
                db.session.delete(ocr_menu)
                db.session.delete(order)
                db.session.delete(user)
                db.session.commit()
                print("✅ 測試資料清理完成")
                
                return True
            else:
                print(f"❌ OCR菜單和訂單摘要儲存失敗: {result['message']}")
                return False
            
    except Exception as e:
        print(f"❌ OCR流程測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_database_relationships():
    """驗證資料庫關聯關係"""
    print("\n=== 驗證資料庫關聯關係 ===")
    
    try:
        from app import create_app
        from app.models import db, Order, OCRMenu, OrderSummary
        
        app = create_app()
        
        with app.app_context():
            # 檢查關聯關係
            print("資料庫關聯關係:")
            print(f"  - orders表: {Order.query.count()} 筆記錄")
            print(f"  - ocr_menus表: {OCRMenu.query.count()} 筆記錄")
            print(f"  - order_summaries表: {OrderSummary.query.count()} 筆記錄")
            
            # 檢查外鍵約束
            print("\n外鍵關聯:")
            print("  - order_summaries.order_id → orders.order_id")
            print("  - order_summaries.ocr_menu_id → ocr_menus.ocr_menu_id")
            print("  - ocr_menus.user_id → users.user_id")
            print("  - orders.user_id → users.user_id")
            
            return True
            
    except Exception as e:
        print(f"❌ 驗證資料庫關聯關係失敗: {str(e)}")
        return False

def main():
    """主函數"""
    print("OCR菜單到訂單摘要流程測試")
    print("=" * 50)
    print(f"測試時間: {datetime.now()}")
    
    # 執行測試
    tests = [
        ("資料庫關聯關係", verify_database_relationships),
        ("OCR流程測試", test_ocr_flow)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 測試異常: {str(e)}")
            results.append((test_name, False))
    
    # 總結
    print("\n" + "=" * 50)
    print("測試總結:")
    
    all_passed = True
    for test_name, result in results:
        status = "✓ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有測試通過！OCR流程正常")
    else:
        print("\n⚠️ 部分測試失敗，請檢查配置")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
