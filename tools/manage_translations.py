#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻譯管理工具
用於管理資料庫中的多語言翻譯
"""

import os
import sys
from dotenv import load_dotenv

# 載入環境變數
load_dotenv('notebook.env')

# 設定 Flask 應用
from app import create_app
from app.models import db, Language, MenuItem, MenuTranslation, Store, StoreTranslation

def init_languages():
    """初始化支援的語言"""
    print("🌍 初始化支援的語言...")
    
    languages = [
        {'lang_code': 'zh', 'lang_name': '中文'},
        {'lang_code': 'en', 'lang_name': 'English'},
        {'lang_code': 'ja', 'lang_name': '日本語'},
        {'lang_code': 'ko', 'lang_name': '한국어'}
    ]
    
    for lang_data in languages:
        existing = Language.query.get(lang_data['lang_code'])
        if not existing:
            new_lang = Language(**lang_data)
            db.session.add(new_lang)
            print(f"✅ 新增語言：{lang_data['lang_name']} ({lang_data['lang_code']})")
        else:
            print(f"ℹ️ 語言已存在：{lang_data['lang_name']} ({lang_data['lang_code']})")
    
    db.session.commit()
    print("✅ 語言初始化完成！")

def add_menu_translation(menu_item_id, lang_code, translated_name, description=None):
    """新增菜單翻譯"""
    try:
        # 檢查是否已存在翻譯
        existing = MenuTranslation.query.filter_by(
            menu_item_id=menu_item_id,
            lang_code=lang_code
        ).first()
        
        if existing:
            # 更新現有翻譯
            existing.description = translated_name
            if description:
                existing.description = description
            db.session.commit()
            print(f"✅ 更新菜單翻譯: {translated_name}")
        else:
            # 新增翻譯
            new_translation = MenuTranslation(
                menu_item_id=menu_item_id,
                lang_code=lang_code,
                description=translated_name
            )
            db.session.add(new_translation)
            db.session.commit()
            print(f"✅ 新增菜單翻譯: {translated_name}")
            
    except Exception as e:
        print(f"❌ 新增菜單翻譯失敗: {e}")
        db.session.rollback()

def add_store_translation(store_id, lang_code, description_trans=None, reviews=None):
    """新增店家翻譯"""
    try:
        # 檢查店家是否存在
        store = Store.query.get(store_id)
        if not store:
            print(f"❌ 找不到店家 ID: {store_id}")
            return False
        
        # 檢查語言是否存在
        language = Language.query.get(lang_code)
        if not language:
            print(f"❌ 不支援的語言代碼: {lang_code}")
            return False
        
        # 檢查是否已有翻譯
        existing = StoreTranslation.query.filter_by(
            store_id=store_id,
            language_code=lang_code
        ).first()
        
        if existing:
            # 更新現有翻譯
            if description_trans:
                existing.description = description_trans
            if reviews:
                existing.translated_summary = reviews
            print(f"🔄 更新店家翻譯：{store.store_name} ({lang_code})")
        else:
            # 新增翻譯
            translation = StoreTranslation(
                store_id=store_id,
                language_code=lang_code,
                description=description_trans,
                translated_summary=reviews
            )
            db.session.add(translation)
            print(f"✅ 新增店家翻譯：{store.store_name} ({lang_code})")
        
        db.session.commit()
        return True
        
    except Exception as e:
        print(f"❌ 新增店家翻譯失敗：{e}")
        db.session.rollback()
        return False

def list_menu_translations():
    """列出所有菜單翻譯"""
    try:
        translations = MenuTranslation.query.all()
        print(f"\n📋 菜單翻譯列表 (共 {len(translations)} 筆):")
        print("-" * 60)
        
        for trans in translations:
            menu_item = MenuItem.query.get(trans.menu_item_id)
            item_name = menu_item.item_name if menu_item else "未知項目"
            print(f"翻譯: {trans.description}")
            print(f"  原始: {item_name}")
            print(f"  語言: {trans.lang_code}")
            print(f"  項目ID: {trans.menu_item_id}")
            print("-" * 30)
            
    except Exception as e:
        print(f"❌ 列出菜單翻譯失敗: {e}")

def list_store_translations(store_id=None):
    """列出店家翻譯"""
    if store_id:
        translations = StoreTranslation.query.filter_by(store_id=store_id).all()
        if not translations:
            print(f"❌ 找不到店家 {store_id} 的翻譯")
            return
        
        store = Store.query.get(store_id)
        print(f"\n🏪 店家翻譯：{store.store_name}")
        print("-" * 50)
    else:
        translations = StoreTranslation.query.all()
        print(f"\n🏪 所有店家翻譯（共 {len(translations)} 筆）")
        print("-" * 50)
    
    for trans in translations:
        store = Store.query.get(trans.store_id)
        language = Language.query.get(trans.language_code)
        print(f"ID: {trans.id}")
        print(f"店家: {store.store_name}")
        print(f"語言: {language.lang_name} ({trans.language_code})")
        if trans.description:
            print(f"描述翻譯: {trans.description}")
        if trans.translated_summary:
            print(f"評論翻譯: {trans.translated_summary}")
        print("-" * 30)

def bulk_translate_menu_items(store_id, target_language):
    """批量翻譯菜單項目（使用AI）"""
    print(f"🤖 開始批量翻譯店家 {store_id} 的菜單到 {target_language}...")
    
    menu_items = MenuItem.query.filter_by(store_id=store_id).all()
    
    if not menu_items:
        print(f"❌ 找不到店家 {store_id} 的菜單項目")
        return
    
    from app.api.helpers import translate_text
    
    success_count = 0
    for item in menu_items:
        try:
            # 檢查是否已有翻譯
            existing = MenuTranslation.query.filter_by(
                menu_item_id=item.menu_item_id,
                lang_code=target_language
            ).first()
            
            if existing:
                print(f"ℹ️ 跳過已有翻譯：{item.item_name}")
                continue
            
            # 使用AI翻譯
            translated_name = translate_text(item.item_name, target_language)
            
            # 儲存翻譯
            translation = MenuTranslation(
                menu_item_id=item.menu_item_id,
                lang_code=target_language,
                description=translated_name
            )
            db.session.add(translation)
            success_count += 1
            
            print(f"✅ {item.item_name} → {translated_name}")
            
        except Exception as e:
            print(f"❌ 翻譯失敗 {item.item_name}: {e}")
    
    db.session.commit()
    print(f"✅ 批量翻譯完成！成功翻譯 {success_count} 個項目")

def main():
    """主函數"""
    app = create_app()
    
    with app.app_context():
        print("🚀 翻譯管理工具")
        print("=" * 50)
        
        while True:
            print("\n請選擇操作：")
            print("1. 初始化支援語言")
            print("2. 新增菜單翻譯")
            print("3. 新增店家翻譯")
            print("4. 列出菜單翻譯")
            print("5. 列出店家翻譯")
            print("6. 批量翻譯菜單")
            print("0. 退出")
            
            choice = input("\n請輸入選項 (0-6): ").strip()
            
            if choice == '0':
                print("👋 再見！")
                break
            elif choice == '1':
                init_languages()
            elif choice == '2':
                menu_item_id = int(input("請輸入菜單項目 ID: "))
                lang_code = input("請輸入語言代碼 (en/ja/ko): ")
                translated_name = input("請輸入翻譯後的菜名: ")
                description = input("請輸入描述翻譯 (可選): ") or None
                add_menu_translation(menu_item_id, lang_code, translated_name, description)
            elif choice == '3':
                store_id = int(input("請輸入店家 ID: "))
                lang_code = input("請輸入語言代碼 (en/ja/ko): ")
                description_trans = input("請輸入店家描述翻譯 (可選): ") or None
                reviews = input("請輸入評論翻譯 (可選): ") or None
                add_store_translation(store_id, lang_code, description_trans, reviews)
            elif choice == '4':
                list_menu_translations()
            elif choice == '5':
                store_id = input("請輸入店家 ID (留空顯示全部): ").strip()
                if store_id:
                    list_store_translations(int(store_id))
                else:
                    list_store_translations()
            elif choice == '6':
                store_id = int(input("請輸入店家 ID: "))
                target_language = input("請輸入目標語言 (en/ja/ko): ")
                bulk_translate_menu_items(store_id, target_language)
            else:
                print("❌ 無效的選項，請重新選擇")

if __name__ == "__main__":
    main() 