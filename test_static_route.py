#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
靜態路由測試腳本
測試語音檔案的靜態路由是否正常工作
"""

import os
import sys
import requests
import tempfile

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_static_route():
    """測試靜態路由"""
    print("🔍 開始測試靜態路由...")
    
    try:
        # 導入必要的模組
        from app import create_app
        from app.api.helpers import VOICE_DIR, generate_voice_with_custom_rate
        
        # 創建測試應用程式
        app = create_app()
        
        # 1. 生成測試語音檔
        print("\n1️⃣ 生成測試語音檔...")
        test_text = "測試語音檔案"
        voice_path = generate_voice_with_custom_rate(test_text, 1.0)
        
        if not voice_path or not os.path.exists(voice_path):
            print("❌ 語音檔生成失敗")
            return False
        
        print(f"✅ 語音檔生成成功: {voice_path}")
        
        # 2. 測試本地靜態路由
        print("\n2️⃣ 測試本地靜態路由...")
        with app.test_client() as client:
            fname = os.path.basename(voice_path)
            response = client.get(f'/api/voices/{fname}')
            
            print(f"📊 狀態碼: {response.status_code}")
            print(f"📊 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"📊 Content-Length: {response.headers.get('Content-Length', 'N/A')}")
            
            if response.status_code == 200:
                print("✅ 本地靜態路由測試成功")
                
                # 檢查回應內容
                if len(response.data) > 0:
                    print(f"✅ 回應內容大小: {len(response.data)} bytes")
                    
                    # 檢查是否為WAV檔案
                    if response.data.startswith(b'RIFF') and b'WAVE' in response.data:
                        print("✅ 回應內容為有效的WAV檔案")
                    else:
                        print("❌ 回應內容不是有效的WAV檔案")
                else:
                    print("❌ 回應內容為空")
            else:
                print(f"❌ 本地靜態路由測試失敗: {response.status_code}")
                print(f"📄 回應內容: {response.data.decode('utf-8', errors='ignore')}")
        
        # 3. 清理測試檔案
        print("\n3️⃣ 清理測試檔案...")
        try:
            os.remove(voice_path)
            print("✅ 測試檔案已清理")
        except Exception as e:
            print(f"❌ 檔案清理失敗: {e}")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🎉 靜態路由測試完成！")
    return True

def test_voice_directory_permissions():
    """測試語音目錄權限"""
    print("\n🔍 檢查語音目錄權限...")
    
    try:
        from app.api.helpers import VOICE_DIR
        
        print(f"📁 語音目錄: {VOICE_DIR}")
        
        # 檢查目錄是否存在
        if os.path.exists(VOICE_DIR):
            print("✅ 語音目錄存在")
            
            # 檢查目錄權限
            if os.access(VOICE_DIR, os.R_OK | os.W_OK):
                print("✅ 語音目錄可讀寫")
            else:
                print("❌ 語音目錄權限不足")
                return False
        else:
            print("❌ 語音目錄不存在")
            return False
            
        # 測試檔案創建
        test_file = os.path.join(VOICE_DIR, "test.txt")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            print("✅ 檔案創建測試成功")
            
            # 清理測試檔案
            os.remove(test_file)
            print("✅ 檔案刪除測試成功")
            
        except Exception as e:
            print(f"❌ 檔案操作測試失敗: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 檢查語音目錄失敗: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 開始靜態路由測試...")
    
    # 檢查語音目錄權限
    dir_ok = test_voice_directory_permissions()
    
    if dir_ok:
        # 執行靜態路由測試
        test_static_route()
    else:
        print("\n❌ 語音目錄權限問題，跳過靜態路由測試") 