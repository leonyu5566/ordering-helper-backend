#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 Cloud Run 配置
功能：檢查 Cloud Run 環境變數和資料庫連接是否正確
"""

import os
import sys

def check_cloud_run_config():
    """檢查 Cloud Run 配置"""
    print("🔍 檢查 Cloud Run 配置...")
    
    # 檢查必要的環境變數
    required_env_vars = {
        'DB_USER': '資料庫使用者名稱',
        'DB_PASSWORD': '資料庫密碼',
        'DB_HOST': '資料庫主機',
        'DB_DATABASE': '資料庫名稱'
    }
    
    missing_vars = []
    for var, description in required_env_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var} ({description})")
        else:
            print(f"✅ {var}: {value[:3]}***" if var == 'DB_PASSWORD' else f"✅ {var}: {value}")
    
    if missing_vars:
        print(f"❌ 缺少環境變數: {', '.join(missing_vars)}")
        print("\n📋 Cloud Run 環境變數設定建議:")
        print("DB_USER=your_db_user")
        print("DB_PASSWORD=your_db_password")
        print("DB_HOST=your_mysql_host")
        print("DB_DATABASE=gae252g1_db")
        return False
    else:
        print("✅ 所有必要的環境變數都已設定")
    
    # 檢查可選的環境變數
    optional_env_vars = {
        'GEMINI_API_KEY': 'Gemini API 金鑰',
        'LINE_CHANNEL_ACCESS_TOKEN': 'LINE Channel Access Token',
        'LINE_CHANNEL_SECRET': 'LINE Channel Secret',
        'AZURE_SPEECH_KEY': 'Azure Speech API 金鑰',
        'AZURE_SPEECH_REGION': 'Azure Speech 區域'
    }
    
    for var, description in optional_env_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: 已設定")
        else:
            print(f"⚠️  {var}: 未設定 ({description})")
    
    return True

def check_database_url():
    """檢查資料庫 URL 格式"""
    print("\n🔍 檢查資料庫 URL 格式...")
    
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_DATABASE')
    
    if all([db_user, db_password, db_host, db_name]):
        # 構建資料庫 URL
        database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}?ssl={{'ssl': {{}}}}&ssl_verify_cert=false"
        print(f"✅ 資料庫 URL 格式正確")
        print(f"   主機: {db_host}")
        print(f"   資料庫: {db_name}")
        print(f"   使用者: {db_user}")
        return True
    else:
        print("❌ 無法構建資料庫 URL，缺少必要環境變數")
        return False

def main():
    """主函數"""
    print("🚀 開始檢查 Cloud Run 配置...")
    
    # 檢查環境變數
    if not check_cloud_run_config():
        print("\n❌ 環境變數配置不完整")
        return False
    
    # 檢查資料庫 URL
    if not check_database_url():
        print("\n❌ 資料庫 URL 配置有問題")
        return False
    
    print("\n🎉 Cloud Run 配置檢查完成！")
    print("\n📋 部署建議:")
    print("1. 確保所有必要的環境變數都已設定")
    print("2. 檢查資料庫連接是否正常")
    print("3. 運行 tools/fix_database_compatibility.py 修復資料庫結構")
    print("4. 部署到 Cloud Run")
    
    return True

if __name__ == "__main__":
    if main():
        print("\n✅ 配置檢查通過")
    else:
        print("\n❌ 配置檢查失敗")
        sys.exit(1) 