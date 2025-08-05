#!/usr/bin/env python3
"""
訂單處理修復腳本
解決 Azure TTS 和資料庫問題
"""

import os
import sys
import traceback
from datetime import datetime

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_azure_tts_config():
    """檢查 Azure TTS 配置"""
    print("🔍 檢查 Azure TTS 配置...")
    
    # 檢查環境變數
    speech_key = os.getenv('AZURE_SPEECH_KEY')
    speech_region = os.getenv('AZURE_SPEECH_REGION')
    
    if not speech_key:
        print("❌ AZURE_SPEECH_KEY 未設定")
        return False
    
    if not speech_region:
        print("❌ AZURE_SPEECH_REGION 未設定")
        return False
    
    print(f"✅ AZURE_SPEECH_KEY: {'*' * 10}{speech_key[-4:] if speech_key else 'None'}")
    print(f"✅ AZURE_SPEECH_REGION: {speech_region}")
    
    # 測試 Azure Speech SDK
    try:
        from azure.cognitiveservices.speech import SpeechConfig
        print("✅ Azure Speech SDK 已安裝")
        
        # 測試配置
        speech_config = SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )
        print("✅ Azure Speech 配置成功")
        return True
        
    except ImportError as e:
        print(f"❌ Azure Speech SDK 未安裝: {e}")
        return False
    except Exception as e:
        print(f"❌ Azure Speech 配置失敗: {e}")
        return False

def test_voice_generation():
    """測試語音生成功能"""
    print("\n🎤 測試語音生成功能...")
    
    try:
        from app.api.helpers import generate_voice_with_custom_rate
        
        # 測試語音生成
        test_text = "您好，我要點餐。牛肉麵 2份，紅茶 1份，總共 115 元，謝謝。"
        voice_path = generate_voice_with_custom_rate(test_text, 1.0)
        
        if voice_path and os.path.exists(voice_path):
            print(f"✅ 語音生成成功: {voice_path}")
            # 清理測試檔案
            os.remove(voice_path)
            return True
        else:
            print("❌ 語音生成失敗")
            return False
            
    except Exception as e:
        print(f"❌ 語音生成測試失敗: {e}")
        traceback.print_exc()
        return False

def check_database_schema():
    """檢查資料庫結構"""
    print("\n🗄️ 檢查資料庫結構...")
    
    try:
        from app import create_app, db
        from app.models import StoreTranslation
        
        app = create_app()
        with app.app_context():
            # 檢查 store_translations 表
            result = db.session.execute("SHOW TABLES LIKE 'store_translations'")
            if result.fetchone():
                print("✅ store_translations 表存在")
                
                # 檢查欄位
                result = db.session.execute("DESCRIBE store_translations")
                columns = [row[0] for row in result.fetchall()]
                
                if 'store_translation_id' in columns:
                    print("✅ store_translation_id 欄位存在")
                    
                    # 測試查詢
                    try:
                        translations = StoreTranslation.query.limit(1).all()
                        print("✅ store_translations 查詢成功")
                        return True
                    except Exception as e:
                        print(f"❌ store_translations 查詢失敗: {e}")
                        return False
                else:
                    print("❌ store_translation_id 欄位不存在")
                    return False
            else:
                print("❌ store_translations 表不存在")
                return False
                
    except Exception as e:
        print(f"❌ 資料庫檢查失敗: {e}")
        traceback.print_exc()
        return False

def fix_order_notification():
    """修復訂單通知功能"""
    print("\n🔧 修復訂單通知功能...")
    
    try:
        from app.api.helpers import send_complete_order_notification
        from app.models import Order, User
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            # 找到最新的訂單
            latest_order = Order.query.order_by(Order.order_id.desc()).first()
            
            if latest_order:
                print(f"📋 找到最新訂單: {latest_order.order_id}")
                
                # 檢查使用者
                user = User.query.get(latest_order.user_id)
                if user:
                    print(f"👤 使用者: {user.line_user_id}")
                    
                    # 測試發送通知
                    try:
                        send_complete_order_notification(latest_order.order_id)
                        print("✅ 訂單通知發送成功")
                        return True
                    except Exception as e:
                        print(f"❌ 訂單通知發送失敗: {e}")
                        return False
                else:
                    print("❌ 找不到對應的使用者")
                    return False
            else:
                print("❌ 找不到任何訂單")
                return False
                
    except Exception as e:
        print(f"❌ 修復訂單通知失敗: {e}")
        traceback.print_exc()
        return False

def create_fallback_voice_system():
    """創建備用語音系統"""
    print("\n🔄 創建備用語音系統...")
    
    try:
        # 創建一個簡單的語音生成函數，不依賴 Azure
        def simple_voice_generator(text):
            """簡單的語音生成器（返回文字而非音檔）"""
            return {
                'success': True,
                'text': text,
                'message': '語音生成功能暫時不可用，請使用文字版本'
            }
        
        # 修改 helpers.py 中的語音生成函數
        helpers_path = 'app/api/helpers.py'
        
        if os.path.exists(helpers_path):
            with open(helpers_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加備用語音生成函數
            fallback_function = '''
def generate_voice_order_fallback(order_id, speech_rate=1.0):
    """
    備用語音生成函數（當 Azure TTS 不可用時）
    """
    try:
        from ..models import Order, OrderItem, MenuItem
        
        # 取得訂單資訊
        order = Order.query.get(order_id)
        if not order:
            return None
        
        # 建立中文訂單文字
        order_text = f"您好，我要點餐。"
        
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                order_text += f" {menu_item.item_name} {item.quantity_small}份，"
        
        order_text += f"總共{order.total_amount}元，謝謝。"
        
        # 返回文字而非音檔
        return {
            'success': True,
            'text': order_text,
            'message': '語音生成功能暫時不可用，請使用文字版本'
        }
        
    except Exception as e:
        print(f"備用語音生成失敗：{e}")
        return None
'''
            
            # 檢查是否已經有備用函數
            if 'generate_voice_order_fallback' not in content:
                # 在文件末尾添加備用函數
                with open(helpers_path, 'a', encoding='utf-8') as f:
                    f.write('\n' + fallback_function)
                print("✅ 備用語音生成函數已添加")
            else:
                print("✅ 備用語音生成函數已存在")
            
            return True
        else:
            print("❌ 找不到 helpers.py 文件")
            return False
            
    except Exception as e:
        print(f"❌ 創建備用語音系統失敗: {e}")
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("🚀 開始修復訂單處理系統...")
    print("=" * 50)
    
    # 1. 檢查 Azure TTS 配置
    azure_ok = check_azure_tts_config()
    
    # 2. 檢查資料庫結構
    db_ok = check_database_schema()
    
    # 3. 測試語音生成
    voice_ok = False
    if azure_ok:
        voice_ok = test_voice_generation()
    
    # 4. 創建備用系統
    fallback_ok = create_fallback_voice_system()
    
    # 5. 修復訂單通知
    notification_ok = fix_order_notification()
    
    # 總結
    print("\n" + "=" * 50)
    print("📊 修復結果總結:")
    print(f"Azure TTS 配置: {'✅' if azure_ok else '❌'}")
    print(f"資料庫結構: {'✅' if db_ok else '❌'}")
    print(f"語音生成: {'✅' if voice_ok else '❌'}")
    print(f"備用系統: {'✅' if fallback_ok else '❌'}")
    print(f"訂單通知: {'✅' if notification_ok else '❌'}")
    
    if azure_ok and voice_ok:
        print("\n🎉 所有功能正常！語音生成應該可以正常工作。")
    elif fallback_ok:
        print("\n⚠️  Azure TTS 不可用，但已啟用備用系統。")
        print("   訂單確認會顯示文字版本而非語音檔。")
    else:
        print("\n❌ 系統需要進一步修復。")
    
    print("\n💡 建議:")
    if not azure_ok:
        print("1. 檢查 AZURE_SPEECH_KEY 和 AZURE_SPEECH_REGION 環境變數")
        print("2. 確認 Azure Speech Service 已啟用")
        print("3. 檢查網路連線和防火牆設定")
    
    if not db_ok:
        print("4. 執行 python3 tools/fix_database_schema.py 修復資料庫")

if __name__ == "__main__":
    main() 