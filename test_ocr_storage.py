#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 OCR 菜單和訂單摘要儲存功能
"""

import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, User, Store, Order, OrderItem, OCRMenu, OCRMenuItem, OrderSummary
import datetime

def test_ocr_storage():
    """測試 OCR 菜單和訂單摘要儲存功能"""
    
    # 建立 Flask 應用
    app = create_app()
    
    with app.app_context():
        try:
            print("🧪 開始測試 OCR 菜單和訂單摘要儲存功能...")
            
            # 1. 建立測試使用者
            test_user = User(
                line_user_id="test_user_123",
                preferred_lang="zh"
            )
            db.session.add(test_user)
            db.session.flush()
            print(f"✅ 建立測試使用者: {test_user.user_id}")
            
            # 2. 建立測試店家
            test_store = Store(
                store_name="測試店家",
                partner_level=0
            )
            db.session.add(test_store)
            db.session.flush()
            print(f"✅ 建立測試店家: {test_store.store_id}")
            
            # 3. 建立測試訂單
            test_order = Order(
                user_id=test_user.user_id,
                store_id=test_store.store_id,
                order_time=datetime.datetime.now(),
                total_amount=150,
                status='pending'
            )
            db.session.add(test_order)
            db.session.flush()
            print(f"✅ 建立測試訂單: {test_order.order_id}")
            
            # 4. 建立測試訂單項目（模擬 OCR 菜單）
            test_order_item = OrderItem(
                order_id=test_order.order_id,
                menu_item_id=None,  # OCR 菜單沒有 menu_item_id
                quantity_small=2,
                subtotal=100,
                original_name="紅燒牛肉麵",  # 原始中文菜名
                translated_name="Beef Noodle Soup"  # 翻譯菜名
            )
            db.session.add(test_order_item)
            
            test_order_item2 = OrderItem(
                order_id=test_order.order_id,
                menu_item_id=None,
                quantity_small=1,
                subtotal=50,
                original_name="小菜",
                translated_name="Side Dish"
            )
            db.session.add(test_order_item2)
            
            db.session.flush()
            print(f"✅ 建立測試訂單項目")
            
            # 5. 測試儲存 OCR 菜單和訂單摘要
            from app.api.helpers import save_ocr_menu_and_summary_to_database
            
            # 準備測試資料
            ocr_items = [
                {
                    'name': {
                        'original': '紅燒牛肉麵',
                        'translated': 'Beef Noodle Soup'
                    },
                    'price': 50,
                    'item_name': '紅燒牛肉麵',
                    'translated_name': 'Beef Noodle Soup'
                },
                {
                    'name': {
                        'original': '小菜',
                        'translated': 'Side Dish'
                    },
                    'price': 50,
                    'item_name': '小菜',
                    'translated_name': 'Side Dish'
                }
            ]
            
            chinese_summary = f"訂單編號：{test_order.order_id}\n店家：{test_store.store_name}\n訂購項目：\n- 紅燒牛肉麵 x2\n- 小菜 x1\n總金額：${test_order.total_amount}"
            user_language_summary = f"Order #{test_order.order_id}\nStore: {test_store.store_name}\nItems:\n- Beef Noodle Soup x2\n- Side Dish x1\nTotal: ${test_order.total_amount}"
            
            # 呼叫儲存函數
            save_result = save_ocr_menu_and_summary_to_database(
                order_id=test_order.order_id,
                ocr_items=ocr_items,
                chinese_summary=chinese_summary,
                user_language_summary=user_language_summary,
                user_language="zh",
                total_amount=test_order.total_amount,
                user_id=test_user.user_id,
                store_name=test_store.store_name
            )
            
            if save_result['success']:
                print(f"✅ OCR 菜單和訂單摘要儲存成功")
                print(f"   OCR 菜單 ID: {save_result['ocr_menu_id']}")
                print(f"   訂單摘要 ID: {save_result['summary_id']}")
                
                # 6. 驗證資料庫中的資料
                ocr_menu = OCRMenu.query.get(save_result['ocr_menu_id'])
                if ocr_menu:
                    print(f"✅ OCR 菜單驗證成功: {ocr_menu.store_name}")
                    print(f"   使用者 ID: {ocr_menu.user_id}")
                    print(f"   上傳時間: {ocr_menu.upload_time}")
                    
                    # 檢查菜單項目
                    ocr_items_count = OCRMenuItem.query.filter_by(ocr_menu_id=ocr_menu.ocr_menu_id).count()
                    print(f"   OCR 菜單項目數量: {ocr_items_count}")
                else:
                    print("❌ OCR 菜單驗證失敗")
                
                order_summary = OrderSummary.query.get(save_result['summary_id'])
                if order_summary:
                    print(f"✅ 訂單摘要驗證成功")
                    print(f"   訂單 ID: {order_summary.order_id}")
                    print(f"   OCR 菜單 ID: {order_summary.ocr_menu_id}")
                    print(f"   使用者語言: {order_summary.user_language}")
                    print(f"   總金額: {order_summary.total_amount}")
                else:
                    print("❌ 訂單摘要驗證失敗")
                
            else:
                print(f"❌ OCR 菜單和訂單摘要儲存失敗: {save_result['message']}")
            
            # 7. 清理測試資料
            print("\n🧹 清理測試資料...")
            db.session.delete(test_order)
            db.session.delete(test_store)
            db.session.delete(test_user)
            db.session.commit()
            print("✅ 測試資料清理完成")
            
            print("\n🎉 測試完成！")
            
        except Exception as e:
            print(f"❌ 測試過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == "__main__":
    test_ocr_storage()
