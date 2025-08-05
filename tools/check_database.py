# =============================================================================
# 檔案名稱：tools/check_database.py
# 功能描述：資料庫結構檢查和修復工具
# 主要職責：
# - 檢查資料庫表格結構
# - 檢查必要的欄位是否存在
# - 修復常見的資料庫結構問題
# - 提供詳細的診斷報告
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫結構檢查和修復工具
這個腳本會檢查資料庫結構並修復常見問題
"""

import os
import sys
from dotenv import load_dotenv

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 載入環境變數
load_dotenv('notebook.env')

from app import create_app
from app.models import db, User, Language
import datetime
import uuid

def check_database_structure():
    """檢查資料庫結構"""
    print("🔍 檢查資料庫結構...")
    
    # 建立 Flask 應用程式
    app = create_app()
    
    with app.app_context():
        try:
            # 檢查必要的表格是否存在
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            required_tables = ['users', 'languages', 'stores', 'menus', 'menu_items', 'orders', 'order_items']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                print(f"❌ 缺少必要的表格：{missing_tables}")
                return False
            else:
                print("✅ 所有必要表格都存在")
            
            # 檢查 users 表格結構
            users_columns = inspector.get_columns('users')
            user_column_names = [col['name'] for col in users_columns]
            
            required_user_columns = ['user_id', 'line_user_id', 'preferred_lang', 'created_at']
            missing_user_columns = [col for col in required_user_columns if col not in user_column_names]
            
            if missing_user_columns:
                print(f"❌ users 表格缺少欄位：{missing_user_columns}")
                return False
            else:
                print("✅ users 表格結構正確")
            
            # 檢查 user_id 是否為自動遞增
            user_id_col = next((col for col in users_columns if col['name'] == 'user_id'), None)
            if user_id_col:
                if user_id_col.get('autoincrement', False):
                    print("✅ user_id 欄位已設定為自動遞增")
                else:
                    print("⚠️  user_id 欄位未設定為自動遞增")
                    return False
            else:
                print("❌ 找不到 user_id 欄位")
                return False
            
            # 檢查語言資料
            languages = Language.query.all()
            if not languages:
                print("⚠️  語言表格為空，正在初始化...")
                from tools.manage_translations import init_languages
                init_languages()
                print("✅ 語言資料初始化完成")
            else:
                print(f"✅ 語言表格包含 {len(languages)} 筆資料")
            
            return True
            
        except Exception as e:
            print(f"❌ 檢查資料庫時發生錯誤：{e}")
            return False

def fix_database_issues():
    """修復資料庫問題"""
    print("🔧 嘗試修復資料庫問題...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # 檢查並修復 users 表格
            inspector = db.inspect(db.engine)
            users_columns = inspector.get_columns('users')
            user_id_col = next((col for col in users_columns if col['name'] == 'user_id'), None)
            
            if user_id_col and not user_id_col.get('autoincrement', False):
                print("🔧 修復 user_id 自動遞增設定...")
                # 這裡需要執行 ALTER TABLE 語句
                db.engine.execute("ALTER TABLE users MODIFY user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT")
                print("✅ user_id 自動遞增設定已修復")
            
            # 確保語言資料存在
            languages = Language.query.all()
            if not languages:
                print("🔧 初始化語言資料...")
                from tools.manage_translations import init_languages
                init_languages()
                print("✅ 語言資料初始化完成")
            
            return True
            
        except Exception as e:
            print(f"❌ 修復資料庫時發生錯誤：{e}")
            return False

def test_user_creation():
    """測試使用者建立功能"""
    print("🧪 測試使用者建立功能...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # 建立測試使用者
            test_user = User(
                line_user_id=f"test_{uuid.uuid4().hex[:8]}",
                preferred_lang='zh',
                created_at=datetime.datetime.utcnow()
            )
            
            db.session.add(test_user)
            db.session.flush()
            
            print(f"✅ 測試使用者建立成功，user_id: {test_user.user_id}")
            
            # 清理測試資料
            db.session.delete(test_user)
            db.session.commit()
            
            print("✅ 測試資料清理完成")
            return True
            
        except Exception as e:
            print(f"❌ 測試使用者建立失敗：{e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("=== 資料庫結構檢查工具 ===")
    print()
    
    # 檢查資料庫結構
    if check_database_structure():
        print("\n✅ 資料庫結構檢查通過")
        
        # 測試使用者建立
        if test_user_creation():
            print("\n✅ 使用者建立功能正常")
            print("\n🎉 資料庫狀態良好！")
        else:
            print("\n❌ 使用者建立功能有問題")
            print("\n🔧 嘗試修復...")
            if fix_database_issues():
                print("✅ 修復完成，請重新測試")
            else:
                print("❌ 修復失敗，可能需要重建資料庫")
    else:
        print("\n❌ 資料庫結構有問題")
        print("\n🔧 嘗試修復...")
        if fix_database_issues():
            print("✅ 修復完成")
        else:
            print("❌ 修復失敗，建議重建資料庫")
            print("\n💡 建議執行：python tools/rebuild_database.py") 