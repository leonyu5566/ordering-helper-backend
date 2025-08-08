#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 GCP Cloud MySQL 資料庫結構
比較實際資料庫與 cloud_mysql_schema.md 的差異
"""

import requests
import json
from datetime import datetime

# Cloud Run 服務 URL
CLOUD_RUN_URL = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"

def check_database_schema():
    """檢查資料庫結構"""
    try:
        print("🔍 檢查資料庫結構...")
        
        # 使用 debug 端點來檢查資料庫結構
        response = requests.get(f"{CLOUD_RUN_URL}/api/test", timeout=15)
        
        print(f"狀態碼: {response.status_code}")
        print(f"回應內容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 資料庫連線正常")
            return True
        else:
            print("❌ 資料庫連線失敗")
            return False
            
    except Exception as e:
        print(f"❌ 資料庫檢查異常: {e}")
        return False

def test_table_structure():
    """測試各個表的結構"""
    tables_to_test = [
        ('stores', '/api/stores'),
        ('orders', '/api/orders'),
        ('menu_items', '/api/menu/1'),
        ('users', '/api/test')
    ]
    
    results = {}
    
    for table_name, endpoint in tables_to_test:
        try:
            print(f"\n🔍 測試 {table_name} 表結構...")
            response = requests.get(f"{CLOUD_RUN_URL}{endpoint}", timeout=15)
            
            print(f"狀態碼: {response.status_code}")
            print(f"回應內容: {response.text[:200]}...")
            
            if response.status_code == 200:
                print(f"✅ {table_name} 表查詢正常")
                results[table_name] = "正常"
            elif response.status_code == 404:
                print(f"⚠️ {table_name} 表沒有資料（正常）")
                results[table_name] = "無資料"
            else:
                print(f"❌ {table_name} 表查詢失敗")
                results[table_name] = "失敗"
                
        except Exception as e:
            print(f"❌ {table_name} 表檢查異常: {e}")
            results[table_name] = "異常"
    
    return results

def analyze_schema_differences():
    """分析 schema 差異"""
    print("\n📊 分析資料庫結構差異...")
    
    # 根據測試結果分析可能的差異
    known_issues = [
        {
            "table": "order_items",
            "issue": "缺少 original_name 和 translated_name 欄位",
            "expected": "original_name VARCHAR(100), translated_name VARCHAR(100)",
            "status": "需要新增"
        },
        {
            "table": "orders", 
            "issue": "使用 order_time 而非 order_date",
            "expected": "order_time DATETIME",
            "status": "已確認"
        },
        {
            "table": "stores",
            "issue": "欄位名稱與 schema 文件不完全一致",
            "expected": "partner_level, gps_lat, gps_lng, place_id 等",
            "status": "已確認"
        }
    ]
    
    return known_issues

def main():
    """主函數"""
    print("🚀 開始檢查 GCP Cloud MySQL 資料庫結構")
    print(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目標服務: {CLOUD_RUN_URL}")
    print("=" * 60)
    
    # 檢查基本連線
    connection_ok = check_database_schema()
    
    if connection_ok:
        # 測試各表結構
        table_results = test_table_structure()
        
        # 分析已知差異
        known_issues = analyze_schema_differences()
        
        # 總結報告
        print("\n" + "=" * 60)
        print("📊 資料庫結構檢查結果")
        print("=" * 60)
        
        print("\n📋 表結構測試結果:")
        for table, status in table_results.items():
            print(f"  {table}: {status}")
        
        print("\n⚠️ 已知結構差異:")
        for issue in known_issues:
            print(f"  {issue['table']}: {issue['issue']} ({issue['status']})")
            print(f"    預期: {issue['expected']}")
        
        print("\n💡 建議:")
        print("  1. 更新 cloud_mysql_schema.md 以反映實際結構")
        print("  2. 新增 order_items 表的雙語欄位")
        print("  3. 確認所有表的欄位名稱和類型")
        
    else:
        print("❌ 無法連接到資料庫，請檢查服務狀態")

if __name__ == "__main__":
    main()
