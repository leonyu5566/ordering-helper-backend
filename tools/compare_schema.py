#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫結構比較工具
功能：比較實際資料庫結構與 schema 文件的差異
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import json

def get_database_connection():
    """取得資料庫連線"""
    DATABASE_URL = "mysql+aiomysql://gae252g1usr:gae252g1PSWD%21@35.201.153.17:3306/gae252g1_db"
    pymysql_url = DATABASE_URL.replace("mysql+aiomysql://", "mysql+pymysql://")
    return create_engine(pymysql_url)

def get_actual_schema():
    """獲取實際資料庫結構"""
    engine = get_database_connection()
    inspector = inspect(engine)
    
    schema = {}
    
    with engine.connect() as connection:
        # 獲取所有表格
        tables = inspector.get_table_names()
        
        for table_name in tables:
            # 獲取欄位資訊
            columns = inspector.get_columns(table_name)
            
            # 獲取主鍵資訊
            pk_constraint = inspector.get_pk_constraint(table_name)
            primary_keys = pk_constraint['constrained_columns'] if pk_constraint else []
            
            # 獲取外鍵資訊
            foreign_keys = inspector.get_foreign_keys(table_name)
            
            # 獲取索引資訊
            indexes = inspector.get_indexes(table_name)
            
            schema[table_name] = {
                'columns': {},
                'primary_keys': primary_keys,
                'foreign_keys': foreign_keys,
                'indexes': indexes
            }
            
            for column in columns:
                schema[table_name]['columns'][column['name']] = {
                    'type': str(column['type']),
                    'nullable': column['nullable'],
                    'default': column['default'],
                    'autoincrement': column.get('autoincrement', False)
                }
    
    return schema

def compare_schema():
    """比較實際資料庫結構與 schema 文件"""
    print("🔍 開始比較資料庫結構...")
    
    # 獲取實際資料庫結構
    actual_schema = get_actual_schema()
    
    # 定義 schema 文件中的期望結構
    expected_schema = {
        'languages': {
            'columns': {
                'line_lang_code': {'type': 'VARCHAR(10)', 'nullable': False, 'primary': True},
                'translation_lang_code': {'type': 'VARCHAR(5)', 'nullable': False},
                'stt_lang_code': {'type': 'VARCHAR(15)', 'nullable': False},
                'lang_name': {'type': 'VARCHAR(50)', 'nullable': False}
            }
        },
        'menus': {
            'columns': {
                'menu_id': {'type': 'INT(11)', 'nullable': False, 'primary': True, 'autoincrement': True},
                'store_id': {'type': 'INT(11)', 'nullable': False},
                'template_id': {'type': 'INT(11)', 'nullable': True},
                'version': {'type': 'INT(11)', 'nullable': False, 'default': 1},
                'effective_date': {'type': 'DATETIME', 'nullable': False},
                'created_at': {'type': 'DATETIME', 'nullable': True, 'default': 'CURRENT_TIMESTAMP'}
            }
        },
        'menu_items': {
            'columns': {
                'menu_item_id': {'type': 'INT(11)', 'nullable': False, 'primary': True, 'autoincrement': True},
                'menu_id': {'type': 'INT(11)', 'nullable': False},
                'item_name': {'type': 'VARCHAR(100)', 'nullable': False},
                'price_big': {'type': 'INT(11)', 'nullable': True},
                'price_small': {'type': 'INT(11)', 'nullable': False},
                'created_at': {'type': 'DATETIME', 'nullable': True, 'default': 'CURRENT_TIMESTAMP'}
            }
        },
        'menu_translations': {
            'columns': {
                'menu_translation_id': {'type': 'INT(11)', 'nullable': False, 'primary': True, 'autoincrement': True},
                'menu_item_id': {'type': 'INT(11)', 'nullable': False},
                'lang_code': {'type': 'VARCHAR(10)', 'nullable': False},
                'description': {'type': 'TEXT', 'nullable': True}
            }
        },
        'stores': {
            'columns': {
                'store_id': {'type': 'INT(11)', 'nullable': False, 'primary': True, 'autoincrement': True},
                'store_name': {'type': 'VARCHAR(100)', 'nullable': False},
                'partner_level': {'type': 'INT(11)', 'nullable': False, 'default': 0},
                'gps_lat': {'type': 'DOUBLE', 'nullable': True},
                'gps_lng': {'type': 'DOUBLE', 'nullable': True},
                'place_id': {'type': 'VARCHAR(255)', 'nullable': True},
                'review_summary': {'type': 'TEXT', 'nullable': True},
                'top_dish_1': {'type': 'VARCHAR(100)', 'nullable': True},
                'top_dish_2': {'type': 'VARCHAR(100)', 'nullable': True},
                'top_dish_3': {'type': 'VARCHAR(100)', 'nullable': True},
                'top_dish_4': {'type': 'VARCHAR(100)', 'nullable': True},
                'top_dish_5': {'type': 'VARCHAR(100)', 'nullable': True},
                'main_photo_url': {'type': 'VARCHAR(255)', 'nullable': True},
                'created_at': {'type': 'DATETIME', 'nullable': True, 'default': 'CURRENT_TIMESTAMP'},
                'latitude': {'type': 'DECIMAL(10,8)', 'nullable': True},
                'longitude': {'type': 'DECIMAL(11,8)', 'nullable': True}
            }
        },
        'store_translations': {
            'columns': {
                'id': {'type': 'INT(11)', 'nullable': False, 'primary': True, 'autoincrement': True},
                'store_id': {'type': 'INT(11)', 'nullable': False},
                'language_code': {'type': 'VARCHAR(10)', 'nullable': False},
                'description': {'type': 'TEXT', 'nullable': True},
                'translated_summary': {'type': 'TEXT', 'nullable': True}
            }
        },
        'users': {
            'columns': {
                'user_id': {'type': 'BIGINT(20)', 'nullable': False, 'primary': True, 'autoincrement': True},
                'line_user_id': {'type': 'VARCHAR(100)', 'nullable': False, 'unique': True},
                'preferred_lang': {'type': 'VARCHAR(10)', 'nullable': False},
                'created_at': {'type': 'DATETIME', 'nullable': True, 'default': 'CURRENT_TIMESTAMP'},
                'state': {'type': 'VARCHAR(50)', 'nullable': True, 'default': 'normal'}
            }
        },
        'orders': {
            'columns': {
                'order_id': {'type': 'BIGINT(20)', 'nullable': False, 'primary': True, 'autoincrement': True},
                'user_id': {'type': 'BIGINT(20)', 'nullable': False},
                'store_id': {'type': 'INT(11)', 'nullable': False},
                'order_time': {'type': 'DATETIME', 'nullable': True, 'default': 'CURRENT_TIMESTAMP'},
                'total_amount': {'type': 'INT(11)', 'nullable': False, 'default': 0},
                'status': {'type': 'VARCHAR(20)', 'nullable': True, 'default': 'pending'}
            }
        },
        'order_items': {
            'columns': {
                'order_item_id': {'type': 'BIGINT(20)', 'nullable': False, 'primary': True, 'autoincrement': True},
                'order_id': {'type': 'BIGINT(20)', 'nullable': False},
                'menu_item_id': {'type': 'BIGINT(20)', 'nullable': True},
                'quantity_small': {'type': 'INT(11)', 'nullable': False, 'default': 0},
                'subtotal': {'type': 'INT(11)', 'nullable': False},
                'created_at': {'type': 'DATETIME', 'nullable': True, 'default': 'CURRENT_TIMESTAMP'},
                'original_name': {'type': 'VARCHAR(100)', 'nullable': True},
                'translated_name': {'type': 'VARCHAR(100)', 'nullable': True}
            }
        },
        'voice_files': {
            'columns': {
                'voice_file_id': {'type': 'BIGINT(20)', 'nullable': False, 'primary': True, 'autoincrement': True},
                'order_id': {'type': 'BIGINT(20)', 'nullable': False},
                'file_url': {'type': 'VARCHAR(500)', 'nullable': False},
                'file_type': {'type': 'VARCHAR(10)', 'nullable': True, 'default': 'mp3'},
                'speech_rate': {'type': 'FLOAT', 'nullable': True, 'default': 1.0},
                'created_at': {'type': 'DATETIME', 'nullable': True, 'default': 'CURRENT_TIMESTAMP'}
            }
        },
        'ocr_menus': {
            'columns': {
                'ocr_menu_id': {'type': 'BIGINT(20)', 'nullable': False, 'primary': True, 'autoincrement': True},
                'user_id': {'type': 'BIGINT(20)', 'nullable': False},
                'store_name': {'type': 'VARCHAR(100)', 'nullable': True},
                'upload_time': {'type': 'DATETIME', 'nullable': True, 'default': 'CURRENT_TIMESTAMP'}
            }
        },
        'ocr_menu_items': {
            'columns': {
                'ocr_menu_item_id': {'type': 'BIGINT(20)', 'nullable': False, 'primary': True, 'autoincrement': True},
                'ocr_menu_id': {'type': 'BIGINT(20)', 'nullable': False},
                'item_name': {'type': 'VARCHAR(100)', 'nullable': False},
                'price_big': {'type': 'INT(11)', 'nullable': True},
                'price_small': {'type': 'INT(11)', 'nullable': False},
                'translated_desc': {'type': 'TEXT', 'nullable': True}
            }
        },
        'menu_crawls': {
            'columns': {
                'crawl_id': {'type': 'BIGINT(20)', 'nullable': False, 'primary': True, 'autoincrement': True},
                'store_id': {'type': 'INT(11)', 'nullable': False},
                'crawl_time': {'type': 'DATETIME', 'nullable': True, 'default': 'CURRENT_TIMESTAMP'},
                'menu_version': {'type': 'INT(11)', 'nullable': True},
                'menu_version_hash': {'type': 'VARCHAR(64)', 'nullable': True},
                'has_update': {'type': 'TINYINT(1)', 'nullable': True, 'default': 0},
                'store_reviews_popular': {'type': 'JSON', 'nullable': True}
            }
        },
        'menu_templates': {
            'columns': {
                'template_id': {'type': 'INT(11)', 'nullable': False, 'primary': True, 'autoincrement': True},
                'template_name': {'type': 'VARCHAR(100)', 'nullable': True},
                'description': {'type': 'TEXT', 'nullable': True}
            }
        },
        'user_actions': {
            'columns': {
                'action_id': {'type': 'BIGINT(20)', 'nullable': False, 'primary': True, 'autoincrement': True},
                'user_id': {'type': 'BIGINT(20)', 'nullable': False},
                'action_type': {'type': 'VARCHAR(50)', 'nullable': False},
                'action_time': {'type': 'DATETIME', 'nullable': True, 'default': 'CURRENT_TIMESTAMP'},
                'details': {'type': 'JSON', 'nullable': True}
            }
        }
    }
    
    # 比較結果
    differences = {
        'missing_tables': [],
        'extra_tables': [],
        'missing_columns': {},
        'extra_columns': {},
        'column_differences': {}
    }
    
    # 檢查缺少的表格
    for table_name in expected_schema:
        if table_name not in actual_schema:
            differences['missing_tables'].append(table_name)
    
    # 檢查多餘的表格
    for table_name in actual_schema:
        if table_name not in expected_schema:
            differences['extra_tables'].append(table_name)
    
    # 檢查欄位差異
    for table_name in expected_schema:
        if table_name in actual_schema:
            expected_columns = expected_schema[table_name]['columns']
            actual_columns = actual_schema[table_name]['columns']
            
            # 檢查缺少的欄位
            missing_columns = []
            for col_name in expected_columns:
                if col_name not in actual_columns:
                    missing_columns.append(col_name)
            
            if missing_columns:
                differences['missing_columns'][table_name] = missing_columns
            
            # 檢查多餘的欄位
            extra_columns = []
            for col_name in actual_columns:
                if col_name not in expected_columns:
                    extra_columns.append(col_name)
            
            if extra_columns:
                differences['extra_columns'][table_name] = extra_columns
            
            # 檢查欄位類型差異
            column_diffs = []
            for col_name in expected_columns:
                if col_name in actual_columns:
                    expected_col = expected_columns[col_name]
                    actual_col = actual_columns[col_name]
                    
                    # 簡化類型比較（移除長度資訊）
                    expected_type = expected_col['type'].split('(')[0].upper()
                    actual_type = actual_col['type'].split('(')[0].upper()
                    
                    if expected_type != actual_type:
                        column_diffs.append({
                            'column': col_name,
                            'expected': expected_col['type'],
                            'actual': actual_col['type']
                        })
            
            if column_diffs:
                differences['column_differences'][table_name] = column_diffs
    
    return differences

def print_comparison_results(differences):
    """印出比較結果"""
    print("\n" + "="*60)
    print("📊 資料庫結構比較結果")
    print("="*60)
    
    if not any(differences.values()):
        print("✅ 資料庫結構與 schema 文件完全一致！")
        return
    
    # 缺少的表格
    if differences['missing_tables']:
        print(f"\n❌ 缺少的表格 ({len(differences['missing_tables'])} 個):")
        for table in differences['missing_tables']:
            print(f"   - {table}")
    
    # 多餘的表格
    if differences['extra_tables']:
        print(f"\n➕ 多餘的表格 ({len(differences['extra_tables'])} 個):")
        for table in differences['extra_tables']:
            print(f"   - {table}")
    
    # 缺少的欄位
    if differences['missing_columns']:
        print(f"\n❌ 缺少的欄位:")
        for table, columns in differences['missing_columns'].items():
            print(f"   📋 {table}:")
            for col in columns:
                print(f"      - {col}")
    
    # 多餘的欄位
    if differences['extra_columns']:
        print(f"\n➕ 多餘的欄位:")
        for table, columns in differences['extra_columns'].items():
            print(f"   📋 {table}:")
            for col in columns:
                print(f"      - {col}")
    
    # 欄位類型差異
    if differences['column_differences']:
        print(f"\n⚠️  欄位類型差異:")
        for table, diffs in differences['column_differences'].items():
            print(f"   📋 {table}:")
            for diff in diffs:
                print(f"      - {diff['column']}: 期望 {diff['expected']}, 實際 {diff['actual']}")

def main():
    """主函數"""
    try:
        print("🔍 開始比較資料庫結構...")
        differences = compare_schema()
        print_comparison_results(differences)
        
        # 生成更新建議
        if any(differences.values()):
            print("\n" + "="*60)
            print("📝 更新建議")
            print("="*60)
            
            if differences['missing_columns']:
                print("\n🔧 需要新增的欄位 SQL:")
                for table, columns in differences['missing_columns'].items():
                    print(f"\n-- {table} 表格:")
                    for col in columns:
                        expected_schema = {
                            'order_items': {
                                'original_name': 'VARCHAR(100) NULL',
                                'translated_name': 'VARCHAR(100) NULL'
                            }
                        }
                        if table in expected_schema and col in expected_schema[table]:
                            print(f"ALTER TABLE {table} ADD COLUMN {col} {expected_schema[table][col]};")
                        else:
                            print(f"-- 需要確認 {col} 的欄位定義")
        
    except Exception as e:
        print(f"❌ 比較過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()
