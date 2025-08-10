#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud MySQL 環境變數設定腳本

功能：
1. 設定 Cloud MySQL 連線所需的環境變數
2. 生成 .env 檔案
3. 驗證環境變數配置
4. 提供 Cloud Run 部署建議
"""

import os
import sys
import json
from pathlib import Path

def setup_environment_variables():
    """設定環境變數"""
    print("🔧 設定 Cloud MySQL 環境變數...")
    
    # 必要的環境變數
    required_vars = {
        'DB_USER': '資料庫使用者名稱',
        'DB_PASSWORD': '資料庫密碼',
        'DB_HOST': '資料庫主機位址',
        'DB_DATABASE': '資料庫名稱'
    }
    
    # 可選的環境變數
    optional_vars = {
        'DB_PORT': '3306',
        'DB_SSL_CA': '',
        'DB_SSL_CERT': '',
        'DB_SSL_KEY': '',
        'DB_POOL_SIZE': '10',
        'DB_MAX_OVERFLOW': '20',
        'DB_POOL_TIMEOUT': '30',
        'DB_POOL_RECYCLE': '3600',
        'DB_CONNECT_TIMEOUT': '10',
        'DB_READ_TIMEOUT': '30',
        'DB_WRITE_TIMEOUT': '30'
    }
    
    # 檢查現有環境變數
    existing_vars = {}
    missing_vars = []
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            existing_vars[var_name] = value
            print(f"✅ {var_name}: {description} - 已設定")
        else:
            missing_vars.append(var_name)
            print(f"❌ {var_name}: {description} - 未設定")
    
    # 如果所有必要變數都已設定，詢問是否要重新設定
    if not missing_vars:
        print("\n🎉 所有必要的環境變數都已設定！")
        response = input("是否要重新設定？(y/N): ").strip().lower()
        if response != 'y':
            return True
    
    # 設定缺失的環境變數
    print(f"\n📝 需要設定 {len(missing_vars)} 個環境變數...")
    
    for var_name in missing_vars:
        description = required_vars[var_name]
        print(f"\n🔧 設定 {var_name} ({description}):")
        
        if var_name == 'DB_PASSWORD':
            # 密碼輸入不顯示
            value = input("請輸入值: ").strip()
        else:
            value = input("請輸入值: ").strip()
        
        if value:
            os.environ[var_name] = value
            existing_vars[var_name] = value
            print(f"✅ {var_name} 已設定")
        else:
            print(f"❌ {var_name} 設定失敗")
            return False
    
    # 設定可選的環境變數
    print(f"\n📝 設定可選的環境變數...")
    
    for var_name, default_value in optional_vars.items():
        current_value = os.getenv(var_name, default_value)
        print(f"\n🔧 設定 {var_name} (目前值: {current_value}):")
        
        new_value = input("請輸入新值 (按 Enter 使用預設值): ").strip()
        
        if new_value:
            os.environ[var_name] = new_value
            existing_vars[var_name] = new_value
            print(f"✅ {var_name} 已設定為: {new_value}")
        else:
            os.environ[var_name] = default_value
            existing_vars[var_name] = default_value
            print(f"✅ {var_name} 使用預設值: {default_value}")
    
    return True

def generate_env_file():
    """生成 .env 檔案"""
    print("\n📄 生成 .env 檔案...")
    
    env_content = """# Cloud MySQL 環境變數配置
# 此檔案包含資料庫連線資訊，請妥善保管

# 必要環境變數
DB_USER={DB_USER}
DB_PASSWORD={DB_PASSWORD}
DB_HOST={DB_HOST}
DB_DATABASE={DB_DATABASE}

# 可選環境變數
DB_PORT={DB_PORT}
DB_SSL_CA={DB_SSL_CA}
DB_SSL_CERT={DB_SSL_CERT}
DB_SSL_KEY={DB_SSL_KEY}

# 連線池配置
DB_POOL_SIZE={DB_POOL_SIZE}
DB_MAX_OVERFLOW={DB_MAX_OVERFLOW}
DB_POOL_TIMEOUT={DB_POOL_TIMEOUT}
DB_POOL_RECYCLE={DB_POOL_RECYCLE}

# 超時配置
DB_CONNECT_TIMEOUT={DB_CONNECT_TIMEOUT}
DB_READ_TIMEOUT={DB_READ_TIMEOUT}
DB_WRITE_TIMEOUT={DB_WRITE_TIMEOUT}

# 其他配置
FLASK_ENV=production
FLASK_APP=run.py
""".format(**{k: os.getenv(k, '') for k in os.environ if k.startswith('DB_')})
    
    # 寫入 .env 檔案
    env_file_path = Path('.env')
    with open(env_file_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ .env 檔案已生成: {env_file_path.absolute()}")
    return env_file_path

def generate_cloud_run_env_vars():
    """生成 Cloud Run 環境變數設定"""
    print("\n☁️ 生成 Cloud Run 環境變數設定...")
    
    # 取得所有 DB_ 開頭的環境變數
    db_vars = {k: v for k, v in os.environ.items() if k.startswith('DB_')}
    
    if not db_vars:
        print("❌ 沒有找到資料庫環境變數")
        return None
    
    # 生成 gcloud 命令
    env_args = []
    for var_name, var_value in db_vars.items():
        env_args.append(f"{var_name}={var_value}")
    
    gcloud_command = f"""gcloud run deploy ordering-helper-backend \\
  --source . \\
  --platform managed \\
  --region asia-east1 \\
  --allow-unauthenticated \\
  --memory 2Gi \\
  --cpu 1 \\
  --max-instances 2 \\
  --set-env-vars {','.join(env_args)} \\
  --timeout 300"""
    
    print("📋 Cloud Run 部署命令:")
    print(gcloud_command)
    
    # 保存到檔案
    deploy_script_path = Path('deploy_cloud_run.sh')
    with open(deploy_script_path, 'w', encoding='utf-8') as f:
        f.write(f"#!/bin/bash\n# Cloud Run 部署腳本\n\n{gcloud_command}\n")
    
    # 設定執行權限
    deploy_script_path.chmod(0o755)
    
    print(f"✅ 部署腳本已保存: {deploy_script_path.absolute()}")
    return deploy_script_path

def validate_configuration():
    """驗證配置"""
    print("\n🔍 驗證環境變數配置...")
    
    try:
        # 嘗試導入配置模組
        sys.path.append(str(Path(__file__).parent.parent))
        from config.cloud_mysql_config import get_cloud_mysql_config
        
        config = get_cloud_mysql_config()
        validation_result = config.validate_config()
        
        if validation_result['valid']:
            print("✅ 配置驗證通過！")
            print(f"📊 連線資訊: {validation_result['config_info']}")
            
            if validation_result['warnings']:
                print("\n⚠️ 警告:")
                for warning in validation_result['warnings']:
                    print(f"   - {warning}")
        else:
            print("❌ 配置驗證失敗:")
            for error in validation_result['errors']:
                print(f"   - {error}")
            return False
            
    except ImportError as e:
        print(f"❌ 無法導入配置模組: {e}")
        return False
    except Exception as e:
        print(f"❌ 配置驗證失敗: {e}")
        return False
    
    return True

def main():
    """主函數"""
    print("🚀 Cloud MySQL 環境變數設定工具")
    print("=" * 50)
    
    # 設定環境變數
    if not setup_environment_variables():
        print("❌ 環境變數設定失敗")
        return
    
    # 生成 .env 檔案
    env_file = generate_env_file()
    
    # 生成 Cloud Run 部署腳本
    deploy_script = generate_cloud_run_env_vars()
    
    # 驗證配置
    if validate_configuration():
        print("\n🎉 環境變數設定完成！")
        print(f"📄 環境變數檔案: {env_file}")
        print(f"🚀 部署腳本: {deploy_script}")
        
        print("\n📋 下一步:")
        print("1. 檢查 .env 檔案內容")
        print("2. 執行部署腳本: ./deploy_cloud_run.sh")
        print("3. 或手動設定 Cloud Run 環境變數")
    else:
        print("\n❌ 配置驗證失敗，請檢查環境變數設定")

if __name__ == "__main__":
    main()
