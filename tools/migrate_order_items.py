#!/usr/bin/env python3
"""
OrderItem 表結構遷移腳本
用於添加臨時項目支援的欄位
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
                return
            
            print(f"🔧 需要添加的欄位：{missing_columns}")
            
            # 執行 ALTER TABLE 語句
            with db.engine.connect() as conn:
                # 修改 menu_item_id 為可空
                if 'menu_item_id' in columns:
                    print("🔧 修改 menu_item_id 為可空...")
                    conn.execute(db.text("ALTER TABLE order_items MODIFY menu_item_id BIGINT NULL"))
                
                # 添加新欄位
                for col in missing_columns:
                    if col == 'temp_item_id':
                        conn.execute(db.text("ALTER TABLE order_items ADD COLUMN temp_item_id VARCHAR(100) NULL"))
                    elif col == 'temp_item_name':
                        conn.execute(db.text("ALTER TABLE order_items ADD COLUMN temp_item_name VARCHAR(100) NULL"))
                    elif col == 'temp_item_price':
                        conn.execute(db.text("ALTER TABLE order_items ADD COLUMN temp_item_price INT NULL"))
                    elif col == 'is_temp_item':
                        conn.execute(db.text("ALTER TABLE order_items ADD COLUMN is_temp_item BOOLEAN DEFAULT FALSE"))
                    
                    print(f"✅ 已添加欄位：{col}")
                
                conn.commit()
            
            print("🎉 遷移完成！")
            
        except Exception as e:
            print(f"❌ 遷移失敗：{e}")
            raise

if __name__ == "__main__":
    print("🚀 開始 OrderItem 表結構遷移...")
    migrate_order_items() 