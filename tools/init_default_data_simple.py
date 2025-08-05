#!/usr/bin/env python3
"""
簡化版預設資料初始化腳本
用於創建預設的店家資料，確保系統可以正常運行
不依賴外部 API，適合本地測試
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 設置環境變數以避免 API 錯誤
os.environ['GEMINI_API_KEY'] = 'dummy_key'
os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'dummy_token'
os.environ['LINE_CHANNEL_SECRET'] = 'dummy_secret'

from app import create_app, db
from app.models import Store, Menu, MenuItem, Language
import datetime

def init_languages_simple():
    """簡化版語言初始化"""
    languages = [
        {'lang_code': 'zh', 'lang_name': '中文'},
        {'lang_code': 'en', 'lang_name': 'English'},
        {'lang_code': 'ja', 'lang_name': '日本語'}
    ]
    
    for lang_data in languages:
        existing = Language.query.get(lang_data['lang_code'])
        if not existing:
            lang = Language(
                lang_code=lang_data['lang_code'],
                lang_name=lang_data['lang_name']
            )
            db.session.add(lang)
            print(f"  ✅ 創建語言: {lang_data['lang_name']}")

def init_default_data_simple():
    """簡化版預設資料初始化"""
    app = create_app()
    
    with app.app_context():
        print("🚀 開始初始化預設資料...")
        
        # 1. 確保語言資料存在
        print("🌐 檢查語言資料...")
        languages = Language.query.all()
        if not languages:
            print("  - 初始化語言資料...")
            init_languages_simple()
            db.session.commit()
            print("  ✅ 語言資料初始化完成")
        else:
            print(f"  ✅ 語言資料已存在 ({len(languages)} 種語言)")
        
        # 2. 創建預設店家
        print("🏪 檢查預設店家...")
        default_store = Store.query.filter_by(store_name='預設店家').first()
        if not default_store:
            print("  - 創建預設店家...")
            default_store = Store(
                store_name='預設店家',
                partner_level=0,  # 非合作店家
                created_at=datetime.datetime.utcnow()
            )
            db.session.add(default_store)
            db.session.commit()
            print(f"  ✅ 預設店家已創建 (store_id: {default_store.store_id})")
        else:
            print(f"  ✅ 預設店家已存在 (store_id: {default_store.store_id})")
        
        # 3. 創建預設菜單
        print("📋 檢查預設菜單...")
        default_menu = Menu.query.filter_by(store_id=default_store.store_id).first()
        if not default_menu:
            print("  - 創建預設菜單...")
            default_menu = Menu(
                store_id=default_store.store_id,
                version=1,
                created_at=datetime.datetime.utcnow()
            )
            db.session.add(default_menu)
            db.session.commit()
            print(f"  ✅ 預設菜單已創建 (menu_id: {default_menu.menu_id})")
        else:
            print(f"  ✅ 預設菜單已存在 (menu_id: {default_menu.menu_id})")
        
        # 4. 創建一些預設菜單項目（可選）
        print("🍕 檢查預設菜單項目...")
        existing_items = MenuItem.query.filter_by(menu_id=default_menu.menu_id).count()
        if existing_items == 0:
            print("  - 創建預設菜單項目...")
            default_items = [
                {
                    'item_name': '測試披薩',
                    'price_small': 150,
                    'price_big': 200
                },
                {
                    'item_name': '測試義大利麵',
                    'price_small': 120,
                    'price_big': 150
                },
                {
                    'item_name': '測試飲料',
                    'price_small': 50,
                    'price_big': 50
                }
            ]
            
            for item_data in default_items:
                menu_item = MenuItem(
                    menu_id=default_menu.menu_id,
                    item_name=item_data['item_name'],
                    price_small=item_data['price_small'],
                    price_big=item_data['price_big'],
                    created_at=datetime.datetime.utcnow()
                )
                db.session.add(menu_item)
            
            db.session.commit()
            print(f"  ✅ 已創建 {len(default_items)} 個預設菜單項目")
        else:
            print(f"  ✅ 預設菜單項目已存在 ({existing_items} 個項目)")
        
        # 5. 顯示總結
        print("✅ 所有預設資料初始化完成！")
        
        # 顯示總結
        print("\n📊 資料庫狀態：")
        print(f"  - 店家數量: {Store.query.count()}")
        print(f"  - 菜單數量: {Menu.query.count()}")
        print(f"  - 菜單項目數量: {MenuItem.query.count()}")
        print(f"  - 語言數量: {Language.query.count()}")
        
        return True

if __name__ == "__main__":
    success = init_default_data_simple()
    if success:
        print("\n🎉 預設資料初始化成功！系統現在可以正常運行。")
    else:
        print("\n💥 預設資料初始化失敗！請檢查錯誤訊息。")
        sys.exit(1) 