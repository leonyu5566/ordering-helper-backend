#!/usr/bin/env python3
"""
資料庫結構修復腳本
專門處理 store_translations 表的欄位問題
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import *
from sqlalchemy import text

def fix_store_translations_table():
    """修復 store_translations 表結構"""
    app = create_app()
    
    with app.app_context():
        try:
            # 檢查 store_translations 表是否存在
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'store_translations' not in existing_tables:
                print("❌ store_translations 表不存在，正在創建...")
                db.create_all()
                print("✅ store_translations 表已創建")
            else:
                print("✅ store_translations 表存在")
            
            # 檢查 store_translation_id 欄位
            store_translations_columns = inspector.get_columns('store_translations')
            column_names = [col['name'] for col in store_translations_columns]
            
            if 'store_translation_id' not in column_names:
                print("❌ store_translation_id 欄位不存在，正在添加...")
                
                # 添加 store_translation_id 欄位
                with db.engine.connect() as conn:
                    # 先備份現有資料
                    result = conn.execute(text("SELECT * FROM store_translations"))
                    existing_data = result.fetchall()
                    
                    # 刪除舊表
                    conn.execute(text("DROP TABLE IF EXISTS store_translations"))
                    conn.commit()
                    
                    # 重新創建表
                    db.create_all()
                    
                    # 恢復資料（如果有）
                    if existing_data:
                        print(f"📋 恢復 {len(existing_data)} 筆資料...")
                        for row in existing_data:
                            # 根據實際的欄位結構調整
                            conn.execute(text("""
                                INSERT INTO store_translations 
                                (store_id, lang_code, description_trans, reviews) 
                                VALUES (%s, %s, %s, %s)
                            """), (row[1], row[2], row[3], row[4] if len(row) > 4 else None))
                        conn.commit()
                
                print("✅ store_translation_id 欄位已添加")
            else:
                print("✅ store_translation_id 欄位存在")
            
            # 檢查其他必要欄位
            required_columns = ['store_id', 'lang_code', 'description_trans', 'reviews']
            missing_columns = [col for col in required_columns if col not in column_names]
            
            if missing_columns:
                print(f"❌ 缺少欄位：{missing_columns}")
                return False
            else:
                print("✅ 所有必要欄位都存在")
            
            # 測試查詢
            try:
                result = db.session.execute(text("SELECT * FROM store_translations LIMIT 1"))
                print("✅ store_translations 表查詢測試成功")
            except Exception as e:
                print(f"❌ store_translations 表查詢失敗：{e}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 修復 store_translations 表時發生錯誤：{e}")
            return False

def fix_other_tables():
    """修復其他可能的表結構問題"""
    app = create_app()
    
    with app.app_context():
        try:
            # 確保所有表都存在
            db.create_all()
            print("✅ 所有表結構已更新")
            
            # 檢查並初始化語言資料
            languages = Language.query.all()
            if not languages:
                print("🌐 初始化語言資料...")
                from tools.manage_translations import init_languages
                init_languages()
                print("✅ 語言資料初始化完成")
            else:
                print(f"✅ 語言資料已存在 ({len(languages)} 筆)")
            
            return True
            
        except Exception as e:
            print(f"❌ 修復其他表時發生錯誤：{e}")
            return False

def main():
    """主函數"""
    print("🔧 開始修復資料庫結構...")
    
    # 修復 store_translations 表
    if fix_store_translations_table():
        print("✅ store_translations 表修復完成")
    else:
        print("❌ store_translations 表修復失敗")
        return
    
    # 修復其他表
    if fix_other_tables():
        print("✅ 其他表修復完成")
    else:
        print("❌ 其他表修復失敗")
        return
    
    print("🎉 資料庫結構修復完成！")

if __name__ == "__main__":
    main() 