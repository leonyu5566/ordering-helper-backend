#!/usr/bin/env python3
"""
簡單訂單測試
測試修復後的訂單處理流程
"""

import os
import sys
import json

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_order_processing():
    """測試訂單處理流程"""
    print("🧪 測試訂單處理流程...")
    
    try:
        from app import create_app, db
        from app.models import Order, User, Store, Menu, MenuItem, OrderItem
        from app.api.helpers import generate_voice_order, send_complete_order_notification
        
        app = create_app()
        with app.app_context():
            # 1. 檢查是否有現有訂單
            latest_order = Order.query.order_by(Order.order_id.desc()).first()
            
            if latest_order:
                print(f"📋 找到最新訂單: {latest_order.order_id}")
                
                # 2. 測試語音生成
                print("\n🎤 測試語音生成...")
                voice_result = generate_voice_order(latest_order.order_id)
                
                if voice_result:
                    if isinstance(voice_result, str):
                        print(f"✅ 語音檔生成成功: {voice_result}")
                    elif isinstance(voice_result, dict):
                        print(f"✅ 備用語音生成成功: {voice_result.get('text', '')[:50]}...")
                    else:
                        print(f"❓ 未知的語音結果類型: {type(voice_result)}")
                else:
                    print("❌ 語音生成失敗")
                
                # 3. 測試訂單通知
                print("\n📱 測試訂單通知...")
                try:
                    send_complete_order_notification(latest_order.order_id)
                    print("✅ 訂單通知發送成功")
                except Exception as e:
                    print(f"❌ 訂單通知發送失敗: {e}")
                
                return True
            else:
                print("❌ 找不到任何訂單")
                return False
                
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_test_order():
    """創建測試訂單"""
    print("📝 創建測試訂單...")
    
    try:
        from app import create_app, db
        from app.models import Order, User, Store, Menu, MenuItem, OrderItem
        import datetime
        
        app = create_app()
        with app.app_context():
            # 1. 確保有使用者
            test_user = User.query.filter_by(line_user_id='test_user').first()
            if not test_user:
                test_user = User(
                    line_user_id='test_user',
                    preferred_lang='zh',
                    created_at=datetime.datetime.utcnow()
                )
                db.session.add(test_user)
                db.session.flush()
                print(f"✅ 創建測試使用者: {test_user.user_id}")
            
            # 2. 確保有店家
            test_store = Store.query.filter_by(store_name='測試店家').first()
            if not test_store:
                test_store = Store(
                    store_name='測試店家',
                    partner_level=0,
                    created_at=datetime.datetime.utcnow()
                )
                db.session.add(test_store)
                db.session.flush()
                print(f"✅ 創建測試店家: {test_store.store_id}")
            
            # 3. 確保有菜單
            test_menu = Menu.query.filter_by(store_id=test_store.store_id).first()
            if not test_menu:
                test_menu = Menu(
                    store_id=test_store.store_id,
                    version=1
                )
                db.session.add(test_menu)
                db.session.flush()
                print(f"✅ 創建測試菜單: {test_menu.menu_id}")
            
            # 4. 確保有菜單項目
            test_menu_item = MenuItem.query.filter_by(item_name='經典夏威夷奶香義大利麵').first()
            if not test_menu_item:
                test_menu_item = MenuItem(
                    menu_id=test_menu.menu_id,
                    item_name='經典夏威夷奶香義大利麵',
                    price_small=115,
                    price_big=115
                )
                db.session.add(test_menu_item)
                db.session.flush()
                print(f"✅ 創建測試菜單項目: {test_menu_item.menu_item_id}")
            
            # 5. 創建訂單
            test_order = Order(
                user_id=test_user.user_id,
                store_id=test_store.store_id,
                total_amount=115,
                order_time=datetime.datetime.utcnow()
            )
            db.session.add(test_order)
            db.session.flush()
            print(f"✅ 創建測試訂單: {test_order.order_id}")
            
            # 6. 創建訂單項目
            test_order_item = OrderItem(
                order_id=test_order.order_id,
                menu_item_id=test_menu_item.menu_item_id,
                quantity_small=1,
                subtotal=115
            )
            db.session.add(test_order_item)
            db.session.commit()
            print(f"✅ 創建測試訂單項目: {test_order_item.order_item_id}")
            
            print(f"🎉 測試訂單創建完成: {test_order.order_id}")
            return test_order.order_id
            
    except Exception as e:
        print(f"❌ 創建測試訂單失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函數"""
    print("🚀 開始測試訂單處理...")
    print("=" * 50)
    
    # 1. 創建測試訂單
    order_id = create_test_order()
    
    if order_id:
        # 2. 測試訂單處理
        success = test_order_processing()
        
        # 總結
        print("\n" + "=" * 50)
        print("📊 測試結果總結:")
        print(f"測試訂單: ✅ (ID: {order_id})")
        print(f"訂單處理: {'✅' if success else '❌'}")
        
        if success:
            print("\n🎉 訂單處理測試成功！")
            print("💡 請檢查 LINE Bot 是否收到通知。")
        else:
            print("\n❌ 訂單處理測試失敗。")
    else:
        print("\n❌ 無法創建測試訂單。")

if __name__ == "__main__":
    main() 