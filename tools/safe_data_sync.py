#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全資料同步工具
功能：處理 created_at 欄位的資料同步問題
解決方案：
1. 使用資料庫自動設定時間戳
2. 提供安全的資料匯入/匯出功能
3. 避免時間欄位衝突
"""

import os
import sys
import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import json

def get_database_connection():
    """取得資料庫連線"""
    DATABASE_URL = "mysql+aiomysql://gae252g1usr:gae252g1PSWD%21@35.201.153.17:3306/gae252g1_db"
    pymysql_url = DATABASE_URL.replace("mysql+aiomysql://", "mysql+pymysql://")
    return create_engine(pymysql_url)

def export_data_without_timestamps(table_name, output_file=None):
    """
    匯出資料時排除時間戳欄位
    避免同步時的時間衝突問題
    """
    engine = get_database_connection()
    
    try:
        with engine.connect() as connection:
            # 獲取表格結構
            desc_result = connection.execute(text(f"DESCRIBE {table_name}"))
            columns = desc_result.fetchall()
            
            # 過濾掉時間戳欄位
            timestamp_columns = ['created_at', 'updated_at', 'order_time', 'upload_time']
            safe_columns = []
            
            for col in columns:
                field_name = col[0]
                if field_name not in timestamp_columns:
                    safe_columns.append(field_name)
            
            print(f"📋 安全欄位列表: {safe_columns}")
            
            # 匯出資料
            columns_str = ', '.join(safe_columns)
            query = f"SELECT {columns_str} FROM {table_name}"
            result = connection.execute(text(query))
            
            data = []
            for row in result.fetchall():
                row_dict = {}
                for i, col_name in enumerate(safe_columns):
                    value = row[i]
                    # 處理特殊資料類型
                    if isinstance(value, datetime.datetime):
                        value = value.isoformat()
                    row_dict[col_name] = value
                data.append(row_dict)
            
            # 儲存到檔案
            if output_file is None:
                output_file = f"{table_name}_export.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 成功匯出 {len(data)} 筆資料到 {output_file}")
            print(f"⚠️  已排除時間戳欄位: {timestamp_columns}")
            
            return output_file
            
    except SQLAlchemyError as e:
        print(f"❌ 匯出失敗: {e}")
        return None

def import_data_safely(table_name, data_file):
    """
    安全匯入資料，讓資料庫自動設定時間戳
    """
    engine = get_database_connection()
    
    try:
        # 讀取資料
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            print("❌ 沒有資料可匯入")
            return False
        
        with engine.connect() as connection:
            # 獲取表格結構
            desc_result = connection.execute(text(f"DESCRIBE {table_name}"))
            columns = desc_result.fetchall()
            
            # 找出時間戳欄位
            timestamp_columns = ['created_at', 'updated_at', 'order_time', 'upload_time']
            auto_timestamp_columns = []
            
            for col in columns:
                field_name = col[0]
                field_type = col[1]
                if field_name in timestamp_columns and 'CURRENT_TIMESTAMP' in str(col[5]):
                    auto_timestamp_columns.append(field_name)
            
            print(f"🕐 自動時間戳欄位: {auto_timestamp_columns}")
            
            # 準備匯入資料
            success_count = 0
            for item in data:
                try:
                    # 移除時間戳欄位，讓資料庫自動設定
                    safe_item = {}
                    for key, value in item.items():
                        if key not in timestamp_columns:
                            safe_item[key] = value
                    
                    # 建立 INSERT 語句
                    columns = list(safe_item.keys())
                    values = list(safe_item.values())
                    placeholders = ', '.join(['%s'] * len(columns))
                    columns_str = ', '.join(columns)
                    
                    insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    
                    connection.execute(text(insert_sql), values)
                    success_count += 1
                    
                except Exception as e:
                    print(f"❌ 匯入項目失敗: {e}")
                    print(f"   項目資料: {item}")
            
            connection.commit()
            print(f"✅ 成功匯入 {success_count} 筆資料")
            print(f"⚠️  時間戳由資料庫自動設定")
            
            return True
            
    except Exception as e:
        print(f"❌ 匯入失敗: {e}")
        return False

def create_safe_sync_script(table_name):
    """
    建立安全的同步腳本
    """
    script_content = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
安全同步腳本 - {table_name}
功能：安全地同步 {table_name} 表格的資料
\"\"\"

import os
import sys
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def sync_{table_name}_data():
    \"\"\"
    同步 {table_name} 資料
    \"\"\"
    # 資料庫連線設定
    DATABASE_URL = "mysql+pymysql://gae252g1usr:gae252g1PSWD%21@35.201.153.17:3306/gae252g1_db"
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # 1. 匯出現有資料（排除時間戳）
            print("📤 匯出現有資料...")
            export_query = f\"\"\"
            SELECT * FROM {table_name}
            \"\"\"
            result = connection.execute(text(export_query))
            
            # 過濾時間戳欄位
            timestamp_columns = ['created_at', 'updated_at', 'order_time', 'upload_time']
            data = []
            
            for row in result.fetchall():
                row_dict = {{}}
                for i, col in enumerate(result.keys()):
                    if col not in timestamp_columns:
                        row_dict[col] = row[i]
                data.append(row_dict)
            
            # 2. 儲存備份
            backup_file = f"{table_name}_backup.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 備份已儲存到 {{backup_file}}")
            print(f"⚠️  已排除時間戳欄位: {{timestamp_columns}}")
            
            return True
            
    except Exception as e:
        print(f"❌ 同步失敗: {{e}}")
        return False

if __name__ == "__main__":
    sync_{table_name}_data()
"""
    
    script_file = f"sync_{table_name}.py"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ 同步腳本已建立: {script_file}")
    return script_file

def main():
    """主函數"""
    print("🚀 安全資料同步工具")
    print("=" * 50)
    
    while True:
        print("\n📋 請選擇操作：")
        print("1. 匯出資料（排除時間戳）")
        print("2. 匯入資料（安全模式）")
        print("3. 建立同步腳本")
        print("4. 檢查表格結構")
        print("5. 退出")
        
        choice = input("\n請輸入選項 (1-5): ").strip()
        
        if choice == '1':
            table_name = input("請輸入表格名稱: ").strip()
            output_file = input("請輸入輸出檔案名稱 (留空使用預設): ").strip()
            if not output_file:
                output_file = None
            
            export_data_without_timestamps(table_name, output_file)
            
        elif choice == '2':
            table_name = input("請輸入表格名稱: ").strip()
            data_file = input("請輸入資料檔案路徑: ").strip()
            
            import_data_safely(table_name, data_file)
            
        elif choice == '3':
            table_name = input("請輸入表格名稱: ").strip()
            create_safe_sync_script(table_name)
            
        elif choice == '4':
            table_name = input("請輸入表格名稱: ").strip()
            engine = get_database_connection()
            
            try:
                with engine.connect() as connection:
                    desc_result = connection.execute(text(f"DESCRIBE {table_name}"))
                    columns = desc_result.fetchall()
                    
                    print(f"\n📋 {table_name} 表格結構:")
                    print("-" * 60)
                    for col in columns:
                        field, type_name, null, key, default, extra = col
                        print(f"{field:<20} {type_name:<20} {null:<8} {key:<8} {str(default):<15} {extra}")
                        
            except Exception as e:
                print(f"❌ 檢查失敗: {e}")
                
        elif choice == '5':
            print("👋 再見！")
            break
            
        else:
            print("❌ 無效選項，請重新選擇")

if __name__ == "__main__":
    main()
