#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud MySQL 連線測試腳本

功能：
1. 測試 Cloud MySQL 資料庫連線
2. 檢查環境變數配置
3. 驗證資料庫操作
4. 提供詳細的錯誤診斷
"""

import os
import sys
import pymysql
import time
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

def test_environment_variables():
    """測試環境變數配置"""
    print("=== 環境變數檢查 ===")
    
    required_vars = {
        'DB_USER': os.getenv('DB_USER'),
        'DB_PASSWORD': os.getenv('DB_PASSWORD'),
        'DB_HOST': os.getenv('DB_HOST'),
        'DB_DATABASE': os.getenv('DB_DATABASE'),
        'DB_PORT': os.getenv('DB_PORT', '3306')
    }
    
    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value:
            print(f"✓ {var_name}: {var_value if var_name != 'DB_PASSWORD' else '***'}")
        else:
            print(f"❌ {var_name}: 未設定")
            all_set = False
    
    return all_set, required_vars

def test_basic_connection(db_config):
    """測試基本連線"""
    print("\n=== 基本連線測試 ===")
    
    try:
        # 嘗試建立連線
        print(f"嘗試連線到: {db_config['DB_HOST']}:{db_config['DB_PORT']}")
        
        connection = pymysql.connect(
            host=db_config['DB_HOST'],
            port=int(db_config['DB_PORT']),
            user=db_config['DB_USER'],
            password=db_config['DB_PASSWORD'],
            database=db_config['DB_DATABASE'],
            charset='utf8mb4',
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30
        )
        
        print("✓ 基本連線成功")
        
        # 測試查詢
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"✓ 查詢測試成功: {result}")
            
            # 檢查資料庫版本
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✓ MySQL 版本: {version[0]}")
            
            # 檢查當前時間
            cursor.execute("SELECT NOW()")
            current_time = cursor.fetchone()
            print(f"✓ 資料庫時間: {current_time[0]}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 基本連線失敗: {str(e)}")
        return False

def test_ssl_connection(db_config):
    """測試 SSL 連線"""
    print("\n=== SSL 連線測試 ===")
    
    try:
        # 嘗試 SSL 連線
        print("嘗試 SSL 連線...")
        
        connection = pymysql.connect(
            host=db_config['DB_HOST'],
            port=int(db_config['DB_PORT']),
            user=db_config['DB_USER'],
            password=db_config['DB_PASSWORD'],
            database=db_config['DB_DATABASE'],
            charset='utf8mb4',
            ssl={'ssl': {}},
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30
        )
        
        print("✓ SSL 連線成功")
        
        # 檢查 SSL 狀態
        with connection.cursor() as cursor:
            cursor.execute("SHOW STATUS LIKE 'Ssl_cipher'")
            ssl_status = cursor.fetchone()
            print(f"✓ SSL 加密: {ssl_status[1] if ssl_status else 'N/A'}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ SSL 連線失敗: {str(e)}")
        return False

def test_database_operations(db_config):
    """測試資料庫操作"""
    print("\n=== 資料庫操作測試 ===")
    
    try:
        connection = pymysql.connect(
            host=db_config['DB_HOST'],
            port=int(db_config['DB_PORT']),
            user=db_config['DB_USER'],
            password=db_config['DB_PASSWORD'],
            database=db_config['DB_DATABASE'],
            charset='utf8mb4',
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30
        )
        
        with connection.cursor() as cursor:
            # 檢查資料表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"✓ 資料表數量: {len(tables)}")
            
            if tables:
                print("資料表列表:")
                for table in tables[:10]:  # 只顯示前10個
                    print(f"  - {table[0]}")
            
            # 檢查使用者表
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()
            print(f"✓ 使用者數量: {user_count[0]}")
            
            # 檢查訂單表
            cursor.execute("SELECT COUNT(*) FROM orders")
            order_count = cursor.fetchone()
            print(f"✓ 訂單數量: {order_count[0]}")
            
            # 檢查店家表
            cursor.execute("SELECT COUNT(*) FROM stores")
            store_count = cursor.fetchone()
            print(f"✓ 店家數量: {store_count[0]}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 資料庫操作失敗: {str(e)}")
        return False

def test_connection_pool():
    """測試連線池"""
    print("\n=== 連線池測試 ===")
    
    try:
        import sqlalchemy
        from sqlalchemy import create_engine, text
        from sqlalchemy.pool import QueuePool
        
        # 構建資料庫 URL
        db_url = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_DATABASE')}"
        
        # 建立引擎
        engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            connect_args={
                'charset': 'utf8mb4',
                'connect_timeout': 10,
                'read_timeout': 30,
                'write_timeout': 30
            }
        )
        
        # 測試連線
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            print("✓ SQLAlchemy 連線成功")
            
            # 測試查詢
            result = connection.execute(text("SELECT COUNT(*) FROM users"))
            count = result.fetchone()
            print(f"✓ SQLAlchemy 查詢成功: {count[0]} 使用者")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ 連線池測試失敗: {str(e)}")
        return False

def main():
    """主函數"""
    print("Cloud MySQL 連線測試")
    print("=" * 50)
    print(f"測試時間: {datetime.now()}")
    
    # 檢查環境變數
    env_ok, db_config = test_environment_variables()
    
    if not env_ok:
        print("\n❌ 環境變數配置不完整，無法進行連線測試")
        return False
    
    # 執行各種測試
    tests = [
        ("基本連線", lambda: test_basic_connection(db_config)),
        ("SSL 連線", lambda: test_ssl_connection(db_config)),
        ("資料庫操作", lambda: test_database_operations(db_config)),
        ("連線池", lambda: test_connection_pool())
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
        print("\n🎉 所有測試通過！資料庫連線正常")
    else:
        print("\n⚠️ 部分測試失敗，請檢查配置")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
