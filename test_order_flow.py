#!/usr/bin/env python3
"""
訂單流程測試腳本
測試完整的訂單處理流程
"""

import os
import sys
import json
import requests
from datetime import datetime

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_order_creation():
    """測試訂單建立"""
    print("🧪 測試訂單建立...")
    
    # 測試訂單資料
    order_data = {
        "store_id": 2,
        "items": [
            {
                "menu_item_id": "temp_1",
                "item_name": "經典夏威夷奶香義大利麵",
                "quantity": 1,
                "price": 115
            }
        ],
        "language": "zh"
    }
    
    try:
        # 發送 POST 請求到訂單 API
        response = requests.post(
            "http://localhost:5000/api/orders",
            json=order_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📡 API 回應狀態: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ 訂單建立成功")
            print(f"📋 訂單 ID: {result.get('order_id')}")
            print(f"💰 總金額: {result.get('total_amount')}")
            print(f"🎤 語音生成: {result.get('voice_generated')}")
            
            # 檢查確認內容
            confirmation = result.get('confirmation', {})
            if confirmation:
                print("📝 訂單摘要:")
                print(f"   中文: {confirmation.get('chinese_summary', 'N/A')[:100]}...")
                print(f"   翻譯: {confirmation.get('translated_summary', 'N/A')[:100]}...")
            
            return result.get('order_id')
        else:
            print(f"❌ 訂單建立失敗: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return None

def test_voice_generation(order_id):
    """測試語音生成"""
    print(f"\n🎤 測試語音生成 (訂單 {order_id})...")
    
    try:
        # 測試語音生成 API
        response = requests.get(f"http://localhost:5000/api/orders/{order_id}/voice")
        
        print(f"📡 語音 API 回應狀態: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 語音生成成功")
            print(f"🎵 語音檔: {result.get('voice_url', 'N/A')}")
            return True
        else:
            print(f"❌ 語音生成失敗: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 語音測試失敗: {e}")
        return False

def test_order_confirmation(order_id):
    """測試訂單確認"""
    print(f"\n📋 測試訂單確認 (訂單 {order_id})...")
    
    try:
        # 測試訂單確認 API
        response = requests.get(f"http://localhost:5000/api/orders/{order_id}/confirm")
        
        print(f"📡 確認 API 回應狀態: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 訂單確認成功")
            print(f"📝 訂單摘要: {result.get('summary', 'N/A')[:100]}...")
            return True
        else:
            print(f"❌ 訂單確認失敗: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 確認測試失敗: {e}")
        return False

def check_line_notification():
    """檢查 LINE 通知"""
    print("\n📱 檢查 LINE 通知...")
    
    try:
        # 檢查最新的日誌
        log_file = "downloaded-logs-20250805-193614.json"
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # 查找 LINE 相關的日誌
            line_logs = [log for log in logs if "LINE" in log.get('textPayload', '') or "line" in log.get('textPayload', '').lower()]
            
            if line_logs:
                print(f"📱 找到 {len(line_logs)} 條 LINE 相關日誌")
                for log in line_logs[-3:]:  # 顯示最後3條
                    print(f"   {log.get('textPayload', '')}")
            else:
                print("📱 未找到 LINE 相關日誌")
            
            # 查找語音相關的日誌
            voice_logs = [log for log in logs if "語音" in log.get('textPayload', '') or "voice" in log.get('textPayload', '').lower()]
            
            if voice_logs:
                print(f"🎤 找到 {len(voice_logs)} 條語音相關日誌")
                for log in voice_logs[-3:]:  # 顯示最後3條
                    print(f"   {log.get('textPayload', '')}")
            else:
                print("🎤 未找到語音相關日誌")
                
        else:
            print("📱 未找到日誌檔案")
            
    except Exception as e:
        print(f"❌ 檢查 LINE 通知失敗: {e}")

def main():
    """主函數"""
    print("🚀 開始測試訂單流程...")
    print("=" * 50)
    
    # 1. 測試訂單建立
    order_id = test_order_creation()
    
    if order_id:
        # 2. 測試語音生成
        voice_ok = test_voice_generation(order_id)
        
        # 3. 測試訂單確認
        confirmation_ok = test_order_confirmation(order_id)
        
        # 4. 檢查 LINE 通知
        check_line_notification()
        
        # 總結
        print("\n" + "=" * 50)
        print("📊 測試結果總結:")
        print(f"訂單建立: ✅ (ID: {order_id})")
        print(f"語音生成: {'✅' if voice_ok else '❌'}")
        print(f"訂單確認: {'✅' if confirmation_ok else '❌'}")
        
        if voice_ok:
            print("\n🎉 語音生成成功！應該會收到語音檔。")
        else:
            print("\n⚠️  語音生成失敗，但訂單確認應該會顯示文字版本。")
    else:
        print("\n❌ 訂單建立失敗，無法進行後續測試。")

if __name__ == "__main__":
    main() 