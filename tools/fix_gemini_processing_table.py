#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復 gemini_processing 表不存在問題
功能：檢查並創建缺失的 gemini_processing 表
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, GeminiProcessing

def fix_gemini_processing_table():
    """修復 gemini_processing 表"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 檢查 gemini_processing 表...")
            
            # 檢查表是否存在
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'gemini_processing' not in existing_tables:
                print("❌ gemini_processing 表不存在，正在創建...")
                
                # 創建表
                db.create_all()
                
                # 再次檢查
                inspector = db.inspect(db.engine)
                updated_tables = inspector.get_table_names()
                
                if 'gemini_processing' in updated_tables:
                    print("✅ gemini_processing 表創建成功！")
                else:
                    print("❌ 表創建失敗")
                    return False
            else:
                print("✅ gemini_processing 表已存在")
            
            # 檢查表結構
            print("🔍 檢查表結構...")
            columns = inspector.get_columns('gemini_processing')
            column_names = [col['name'] for col in columns]
            
            expected_columns = [
                'processing_id', 'user_id', 'store_id', 'image_url', 
                'ocr_result', 'structured_menu', 'status', 'created_at'
            ]
            
            missing_columns = [col for col in expected_columns if col not in column_names]
            
            if missing_columns:
                print(f"⚠️  缺少欄位: {missing_columns}")
                print("建議重新創建表...")
                return False
            else:
                print("✅ 表結構正確")
            
            return True
            
        except Exception as e:
            print(f"❌ 修復過程中發生錯誤: {e}")
            return False

if __name__ == "__main__":
    print("🚀 開始修復 gemini_processing 表...")
    
    if fix_gemini_processing_table():
        print("🎉 修復完成！")
    else:
        print("❌ 修復失敗")
        sys.exit(1) 