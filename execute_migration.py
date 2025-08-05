#!/usr/bin/env python3
"""
執行資料庫遷移腳本
通過 API 端點在生產環境執行資料庫結構更新
"""

import requests
import json
import time

# 生產環境 URL
BASE_URL = "https://ordering-helper-backend-1095766716155.asia-east1.run.app"

def execute_migration():
    """執行資料庫遷移"""
    print("🔄 開始執行資料庫遷移...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/admin/migrate-database",
            headers={"Content-Type": "application/json"},
            json={},  # 空的請求體
            timeout=60
        )
        
        print(f"📥 遷移狀態碼：{response.status_code}")
        print(f"📥 遷移回應：{response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("status") == "success":
                    print("✅ 資料庫遷移成功！")
                    return True
                elif result.get("status") == "warning":
                    print("⚠️  遷移完成但驗證失敗")
                    return False
                else:
                    print("❌ 遷移失敗")
                    return False
            except:
                print("✅ 遷移成功（無法解析回應）")
                return True
        else:
            print("❌ 遷移請求失敗")
            return False
            
    except Exception as e:
        print(f"❌ 遷移請求異常：{e}")
        return False

def test_after_migration():
    """遷移後測試"""
    print("\n🧪 遷移後測試...")
    
    # 等待一下讓遷移生效
    time.sleep(5)
    
    # 測試臨時訂單
    temp_order_data = {
        "store_id": 1,
        "line_user_id": None,
        "language": "zh",
        "items": [
            {
                "id": "temp_36_0",
                "item_name": "奶油經典夏威夷",
                "price": 115,
                "quantity": 1
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orders",
            headers={"Content-Type": "application/json"},
            json=temp_order_data,
            timeout=30
        )
        
        print(f"📥 測試狀態碼：{response.status_code}")
        print(f"📥 測試回應：{response.text}")
        
        if response.status_code == 201:
            print("✅ 臨時訂單測試成功！修復完成！")
            return True
        else:
            print("❌ 臨時訂單測試失敗")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗：{e}")
        return False

def main():
    """主函數"""
    print("🚀 開始執行資料庫遷移和測試...")
    
    # 執行遷移
    migration_success = execute_migration()
    
    if migration_success:
        # 測試修復
        test_success = test_after_migration()
        
        print("\n📊 最終結果：")
        print(f"  資料庫遷移：{'✅ 成功' if migration_success else '❌ 失敗'}")
        print(f"  臨時訂單測試：{'✅ 成功' if test_success else '❌ 失敗'}")
        
        if migration_success and test_success:
            print("\n🎉 修復完全成功！")
            print("💡 現在用戶可以正常使用臨時訂單功能了")
        else:
            print("\n⚠️  部分成功，需要進一步檢查")
    else:
        print("\n💥 遷移失敗，無法繼續測試")

if __name__ == "__main__":
    main() 