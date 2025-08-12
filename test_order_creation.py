#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
訂單創建測試腳本

功能：
1. 測試訂單創建過程中的資料庫操作
2. 模擬實際的訂單資料
3. 檢查可能的錯誤點
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

def test_database_models():
    """測試資料庫模型"""
    print("\n=== 資料庫模型測試 ===")
    
    try:
        # 導入必要的模組
        from app import create_app
        from app.models import db, User, Store, Menu, MenuItem, Order, OrderItem, Language
        
        # 創建應用程式
        app = create_app()
        
        with app.app_context():
            # 測試資料庫連線
            print("✓ 資料庫連線正常")
            
            # 檢查使用者表
            users = User.query.all()
            print(f"✓ 使用者數量: {len(users)}")
            
            # 檢查店家表
            stores = Store.query.all()
            print(f"✓ 店家數量: {len(stores)}")
            
            # 檢查菜單表
            menus = Menu.query.all()
            print(f"✓ 菜單數量: {len(menus)}")
            
            # 檢查菜單項目表
            menu_items = MenuItem.query.all()
            print(f"✓ 菜單項目數量: {len(menu_items)}")
            
            # 檢查訂單表
            orders = Order.query.all()
            print(f"✓ 訂單數量: {len(orders)}")
            
            # 檢查語言表
            languages = Language.query.all()
            print(f"✓ 語言數量: {len(languages)}")
            
            return True
            
    except Exception as e:
        print(f"❌ 資料庫模型測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_user_creation():
    """測試使用者創建"""
    print("\n=== 使用者創建測試 ===")
    
    try:
        from app import create_app
        from app.models import db, User, Language
        
        app = create_app()
        
        with app.app_context():
            # 檢查語言是否存在
            language = db.session.get(Language, 'zh')
            if not language:
                print("⚠️ 中文語言不存在，創建中...")
                language = Language(
                    line_lang_code='zh', 
                    translation_lang_code='zh',
                    stt_lang_code='zh-TW',
                    lang_name='中文'
                )
                db.session.add(language)
                db.session.commit()
            
            # 創建測試使用者
            test_user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            user = User(
                line_user_id=test_user_id,
                preferred_lang='zh'
            )
            
            db.session.add(user)
            db.session.flush()  # 獲取 user_id
            
            print(f"✓ 測試使用者創建成功，ID: {user.user_id}")
            
            # 清理測試資料
            db.session.delete(user)
            db.session.commit()
            
            return True
            
    except Exception as e:
        print(f"❌ 使用者創建測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_order_creation():
    """測試訂單創建"""
    print("\n=== 訂單創建測試 ===")
    
    try:
        from app import create_app
        from app.models import db, User, Store, Menu, MenuItem, Order, OrderItem, Language
        
        app = create_app()
        
        with app.app_context():
            # 確保語言存在
            language = Language.query.get('zh')
            if not language:
                language = Language(language_code='zh', language_name='中文')
                db.session.add(language)
                db.session.commit()
            
            # 創建測試使用者
            test_user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            user = User(
                line_user_id=test_user_id,
                preferred_lang='zh'
            )
            db.session.add(user)
            db.session.flush()
            
            # 獲取第一個店家
            store = Store.query.first()
            if not store:
                print("❌ 沒有找到店家資料")
                return False
            
            print(f"✓ 使用店家: {store.store_name} (ID: {store.store_id})")
            
            # 獲取或創建菜單
            menu = Menu.query.filter_by(store_id=store.store_id).first()
            if not menu:
                menu = Menu(
                    store_id=store.store_id,
                    version=1,
                    effective_date=datetime.now()
                )
                db.session.add(menu)
                db.session.flush()
            
            # 創建測試菜單項目
            menu_item = MenuItem(
                menu_id=menu.menu_id,
                item_name="測試商品",
                price_small=100,
                price_big=100
            )
            db.session.add(menu_item)
            db.session.flush()
            
            print(f"✓ 創建測試菜單項目: {menu_item.item_name} (ID: {menu_item.menu_item_id})")
            
            # 創建訂單項目
            order_item = OrderItem(
                menu_item_id=menu_item.menu_item_id,
                quantity_small=2,
                subtotal=200
            )
            
            # 創建訂單
            order = Order(
                user_id=user.user_id,
                store_id=store.store_id,
                total_amount=200,
                items=[order_item]
            )
            
            db.session.add(order)
            db.session.commit()
            
            print(f"✓ 訂單創建成功，ID: {order.order_id}")
            
            # 清理測試資料
            db.session.delete(order)
            db.session.delete(menu_item)
            db.session.delete(user)
            db.session.commit()
            
            return True
            
    except Exception as e:
        print(f"❌ 訂單創建測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_ocr_order_creation():
    """測試OCR訂單創建"""
    print("\n=== OCR訂單創建測試 ===")
    
    try:
        from app import create_app
        from app.models import db, User, Store, Menu, MenuItem, Order, OrderItem, Language
        
        app = create_app()
        
        with app.app_context():
            # 確保語言存在
            language = Language.query.get('zh')
            if not language:
                language = Language(language_code='zh', language_name='中文')
                db.session.add(language)
                db.session.commit()
            
            # 創建測試使用者
            test_user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            user = User(
                line_user_id=test_user_id,
                preferred_lang='zh'
            )
            db.session.add(user)
            db.session.flush()
            
            # 獲取第一個店家
            store = Store.query.first()
            if not store:
                print("❌ 沒有找到店家資料")
                return False
            
            # 獲取或創建菜單
            menu = Menu.query.filter_by(store_id=store.store_id).first()
            if not menu:
                menu = Menu(
                    store_id=store.store_id,
                    version=1,
                    effective_date=datetime.now()
                )
                db.session.add(menu)
                db.session.flush()
            
            # 創建OCR菜單項目（模擬OCR項目）
            ocr_menu_item = MenuItem(
                menu_id=menu.menu_id,
                item_name="OCR測試商品",
                price_small=150,
                price_big=150
            )
            db.session.add(ocr_menu_item)
            db.session.flush()
            
            # 創建OCR訂單項目
            ocr_order_item = OrderItem(
                menu_item_id=ocr_menu_item.menu_item_id,
                quantity_small=1,
                subtotal=150,
                original_name="OCR測試商品",
                translated_name="OCR Test Item"
            )
            
            # 創建OCR訂單
            ocr_order = Order(
                user_id=user.user_id,
                store_id=store.store_id,
                total_amount=150,
                items=[ocr_order_item]
            )
            
            db.session.add(ocr_order)
            db.session.commit()
            
            print(f"✓ OCR訂單創建成功，ID: {ocr_order.order_id}")
            
            # 清理測試資料
            db.session.delete(ocr_order)
            db.session.delete(ocr_menu_item)
            db.session.delete(user)
            db.session.commit()
            
            return True
            
    except Exception as e:
        print(f"❌ OCR訂單創建測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("訂單創建測試")
    print("=" * 50)
    print(f"測試時間: {datetime.now()}")
    
    # 執行各種測試
    tests = [
        ("資料庫模型", test_database_models),
        ("使用者創建", test_user_creation),
        ("訂單創建", test_order_creation),
        ("OCR訂單創建", test_ocr_order_creation)
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
        print("\n🎉 所有測試通過！訂單創建功能正常")
    else:
        print("\n⚠️ 部分測試失敗，請檢查配置")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
