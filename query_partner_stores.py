#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查詢 Cloud MySQL 資料庫中的合作店家

功能：
1. 透過 Cloud Run 服務連線 Cloud MySQL 資料庫
2. 查詢所有合作店家（partner_level > 0）
3. 顯示店家的詳細資訊
4. 支援多語言查詢

使用方法：
python3 query_partner_stores.py [語言代碼]

範例：
python3 query_partner_stores.py          # 預設中文
python3 query_partner_stores.py en      # 英文
python3 query_partner_stores.py ja      # 日文
python3 query_partner_stores.py ko      # 韓文
"""

import requests
import json
import sys
from datetime import datetime

# Cloud Run 服務 URL
CLOUD_RUN_URL = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"

def get_partner_stores(language='zh'):
    """
    透過 Cloud Run 服務查詢合作店家
    
    Args:
        language (str): 語言代碼 (zh, en, ja, ko)
    
    Returns:
        dict: 店家資料
    """
    try:
        print(f"🔍 正在查詢 {language} 語言的合作店家...")
        
        # 查詢所有店家
        stores_url = f"{CLOUD_RUN_URL}/api/stores"
        response = requests.get(stores_url, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ 查詢失敗，狀態碼: {response.status_code}")
            print(f"錯誤訊息: {response.text}")
            return None
        
        data = response.json()
        stores = data.get('stores', [])
        
        # 篩選合作店家 (partner_level > 0)
        partner_stores = [store for store in stores if store.get('partner_level', 0) > 0]
        
        print(f"✅ 成功查詢到 {len(stores)} 個店家")
        print(f"🎯 其中合作店家: {len(partner_stores)} 個")
        
        return partner_stores
        
    except requests.exceptions.Timeout:
        print("❌ 請求超時，請檢查網路連線")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ 連線失敗，請檢查 Cloud Run 服務是否正常運行")
        return None
    except Exception as e:
        print(f"❌ 查詢異常: {e}")
        return None

def get_store_details(store_id, language='zh'):
    """
    取得特定店家的詳細資訊（包含多語言翻譯）
    
    Args:
        store_id (int): 店家 ID
        language (str): 語言代碼
    
    Returns:
        dict: 店家詳細資訊
    """
    try:
        store_url = f"{CLOUD_RUN_URL}/api/stores/{store_id}?lang={language}"
        response = requests.get(store_url, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ 無法取得店家 {store_id} 的詳細資訊")
            return None
            
    except Exception as e:
        print(f"❌ 取得店家詳細資訊失敗: {e}")
        return None

def display_partner_stores(partner_stores, language='zh'):
    """
    顯示合作店家資訊
    
    Args:
        partner_stores (list): 合作店家列表
        language (str): 語言代碼
    """
    if not partner_stores:
        print("📭 沒有找到合作店家")
        return
    
    print(f"\n{'='*80}")
    print(f"🏪 合作店家列表 ({language.upper()}) - 共 {len(partner_stores)} 家")
    print(f"{'='*80}")
    
    for i, store in enumerate(partner_stores, 1):
        print(f"\n{i}. 店家 ID: {store['store_id']}")
        print(f"   店名: {store['store_name']}")
        
        # 顯示合作等級
        partner_level = store.get('partner_level', 0)
        if partner_level == 1:
            level_text = "🌟 合作店家"
        elif partner_level == 2:
            level_text = "💎 VIP 店家"
        else:
            level_text = "❓ 未知等級"
        print(f"   等級: {level_text}")
        
        # 顯示位置資訊
        if store.get('gps_lat') and store.get('gps_lng'):
            print(f"   位置: {store['gps_lat']:.6f}, {store['gps_lng']:.6f}")
        
        # 顯示評論摘要
        if store.get('review_summary'):
            summary = store['review_summary'][:100] + "..." if len(store['review_summary']) > 100 else store['review_summary']
            print(f"   評論: {summary}")
        
        # 顯示招牌照片
        if store.get('main_photo_url'):
            print(f"   照片: {store['main_photo_url']}")
        
        # 顯示建立時間
        if store.get('created_at'):
            created_time = datetime.fromisoformat(store['created_at'].replace('Z', '+00:00'))
            print(f"   建立: {created_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("-" * 60)

def test_cloud_run_connection():
    """測試 Cloud Run 服務連線"""
    print("🔍 測試 Cloud Run 服務連線...")
    
    try:
        health_url = f"{CLOUD_RUN_URL}/api/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Cloud Run 服務連線正常")
            return True
        else:
            print(f"❌ Cloud Run 服務異常，狀態碼: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cloud Run 連線失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 合作店家查詢工具")
    print("=" * 50)
    
    # 取得語言參數
    language = sys.argv[1] if len(sys.argv) > 1 else 'zh'
    
    # 支援的語言
    supported_languages = {
        'zh': '中文',
        'en': 'English',
        'ja': '日本語',
        'ko': '한국어'
    }
    
    if language not in supported_languages:
        print(f"❌ 不支援的語言: {language}")
        print(f"支援的語言: {', '.join(supported_languages.keys())}")
        return
    
    print(f"🌐 使用語言: {supported_languages[language]}")
    
    # 測試 Cloud Run 連線
    if not test_cloud_run_connection():
        print("❌ 無法連線到 Cloud Run 服務，請檢查服務狀態")
        return
    
    # 查詢合作店家
    partner_stores = get_partner_stores(language)
    
    if partner_stores is None:
        print("❌ 查詢合作店家失敗")
        return
    
    # 顯示結果
    display_partner_stores(partner_stores, language)
    
    # 統計資訊
    print(f"\n📊 統計摘要:")
    print(f"   總店家數: {len(partner_stores)}")
    
    # 按合作等級統計
    level_1_count = len([s for s in partner_stores if s.get('partner_level') == 1])
    level_2_count = len([s for s in partner_stores if s.get('partner_level') == 2])
    
    print(f"   合作店家 (Level 1): {level_1_count}")
    print(f"   VIP 店家 (Level 2): {level_2_count}")
    
    print(f"\n✅ 查詢完成！")

if __name__ == "__main__":
    main()
