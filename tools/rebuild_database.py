# =============================================================================
# 檔案名稱：tools/rebuild_database.py
# 功能描述：資料庫重建工具，用於建立或重新建立所有資料庫表格
# 主要職責：
# - 連接到指定的資料庫
# - 刪除現有的表格（如果存在）
# - 根據 models.py 建立新的表格
# - 顯示建立結果
# 使用時機：
# - 首次設定資料庫
# - 資料庫結構變更
# - 需要清空所有資料時
# 注意：此操作會刪除所有現有資料！
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重建資料庫表格的腳本
這個腳本會連接到資料庫並根據 models.py 中定義的模型建立所有表格
"""

import os
import sys
from dotenv import load_dotenv

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 載入環境變數
load_dotenv('notebook.env')

from app import create_app
from app.models import db

def rebuild_database():
    """重建資料庫表格"""
    print("開始重建資料庫表格...")
    
    # 建立 Flask 應用程式
    app = create_app()
    
    with app.app_context():
        try:
            # 刪除所有現有表格
            print("刪除現有表格...")
            db.drop_all()
            
            # 建立所有表格
            print("建立新表格...")
            db.create_all()
            
            print("✅ 資料庫表格重建完成！")
            
            # 顯示建立的表格
            print("\n建立的表格：")
            for table_name in db.engine.table_names():
                print(f"  - {table_name}")
                
        except Exception as e:
            print(f"❌ 重建資料庫時發生錯誤：{e}")
            return False
    
    return True

if __name__ == '__main__':
    print("=== 資料庫重建工具 ===")
    print("這個工具會刪除所有現有表格並重新建立")
    print("請確保你已經備份重要資料！")
    print()
    
    # 確認是否要繼續
    response = input("是否要繼續重建資料庫？(y/N): ")
    if response.lower() != 'y':
        print("取消重建")
        sys.exit(0)
    
    success = rebuild_database()
    if success:
        print("\n🎉 資料庫重建成功！")
    else:
        print("\n💥 資料庫重建失敗！")
        sys.exit(1) 