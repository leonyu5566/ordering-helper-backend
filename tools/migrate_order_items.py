#!/usr/bin/env python3
"""
OrderItem 表結構遷移腳本
用於添加臨時項目支援的欄位
適用於生產環境
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

def migrate_order_items():
    """遷移 OrderItem 表結構"""
    app = create_app()
    
    with app.app_context():
        print("🔄 開始遷移 OrderItem 表結構...")
        
        try:
            # 檢查是否需要添加新欄位
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('order_items')]
            
            print(f"📋 當前欄位：{columns}")
            
            # 需要添加的欄位
            new_columns = [
                'temp_item_id',
                'temp_item_name', 
                'temp_item_price',
                'is_temp_item'
            ]
            
            missing_columns = [col for col in new_columns if col not in columns]
            
            if not missing_columns:
                print("✅ 所有欄位都已存在，無需遷移")
                return True
            
            print(f"🔧 需要添加的欄位：{missing_columns}")
            
            # 執行 ALTER TABLE 語句
            with db.engine.connect() as conn:
                # 修改 menu_item_id 為可空
                if 'menu_item_id' in columns:
                    print("🔧 修改 menu_item_id 為可空...")
                    try:
                        conn.execute(db.text("ALTER TABLE order_items MODIFY menu_item_id BIGINT NULL"))
                        print("✅ menu_item_id 已修改為可空")
                    except Exception as e:
                        print(f"⚠️  修改 menu_item_id 失敗（可能已經是可空）：{e}")
                
                # 添加新欄位
                for col in missing_columns:
                    try:
                        if col == 'temp_item_id':
                            conn.execute(db.text("ALTER TABLE order_items ADD COLUMN temp_item_id VARCHAR(100) NULL"))
                        elif col == 'temp_item_name':
                            conn.execute(db.text("ALTER TABLE order_items ADD COLUMN temp_item_name VARCHAR(100) NULL"))
                        elif col == 'temp_item_price':
                            conn.execute(db.text("ALTER TABLE order_items ADD COLUMN temp_item_price INT NULL"))
                        elif col == 'is_temp_item':
                            conn.execute(db.text("ALTER TABLE order_items ADD COLUMN is_temp_item BOOLEAN DEFAULT FALSE"))
                        
                        print(f"✅ 已添加欄位：{col}")
                    except Exception as e:
                        print(f"❌ 添加欄位 {col} 失敗：{e}")
                        return False
                
                conn.commit()
            
            print("🎉 遷移完成！")
            return True
            
        except Exception as e:
            print(f"❌ 遷移失敗：{e}")
            return False

def verify_migration():
    """驗證遷移是否成功"""
    app = create_app()
    
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('order_items')]
            
            required_columns = [
                'order_item_id', 'order_id', 'menu_item_id', 'quantity_small', 'subtotal',
                'temp_item_id', 'temp_item_name', 'temp_item_price', 'is_temp_item'
            ]
            
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"❌ 驗證失敗，缺少欄位：{missing_columns}")
                return False
            else:
                print("✅ 遷移驗證成功，所有必要欄位都存在")
                return True
                
        except Exception as e:
            print(f"❌ 驗證失敗：{e}")
            return False

def main():
    """主函數"""
    print("🚀 開始 OrderItem 表結構遷移...")
    
    # 執行遷移
    success = migrate_order_items()
    
    if success:
        # 驗證遷移
        print("\n🔍 驗證遷移結果...")
        verify_success = verify_migration()
        
        if verify_success:
            print("\n🎉 遷移完全成功！")
            print("💡 現在可以測試臨時訂單功能了")
        else:
            print("\n⚠️  遷移完成但驗證失敗")
    else:
        print("\n💥 遷移失敗")

if __name__ == "__main__":
    main() 