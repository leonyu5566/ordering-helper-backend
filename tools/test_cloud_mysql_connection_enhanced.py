#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強的 Cloud MySQL 連線測試工具

功能：
1. 測試 Cloud Run 服務與 Cloud MySQL 的連線
2. 測試資料庫效能和連線池
3. 診斷常見連線問題
4. 生成詳細的測試報告
"""

import sys
import os
import time
import requests
import json
from datetime import datetime
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent.parent))

def test_cloud_run_health():
    """測試 Cloud Run 健康檢查"""
    print("🔍 測試 Cloud Run 健康檢查...")
    
    try:
        # 從環境變數取得 Cloud Run URL
        base_url = os.getenv('CLOUD_RUN_URL', 'https://ordering-helper-backend-1095766716155.asia-east1.run.app')
        
        # 測試健康檢查端點
        health_url = f"{base_url}/api/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Cloud Run 服務正常運行")
            return True, response.json() if response.content else {}
        else:
            print(f"❌ Cloud Run 服務異常，狀態碼: {response.status_code}")
            return False, {'status_code': response.status_code, 'response': response.text}
            
    except Exception as e:
        print(f"❌ Cloud Run 連線失敗: {e}")
        return False, {'error': str(e)}

def test_database_connection():
    """測試資料庫連線"""
    print("\n🔍 測試資料庫連線...")
    
    try:
        base_url = os.getenv('CLOUD_RUN_URL', 'https://ordering-helper-backend-1095766716155.asia-east1.run.app')
        
        # 測試店家列表查詢
        stores_url = f"{base_url}/api/stores"
        start_time = time.time()
        response = requests.get(stores_url, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            store_count = len(data.get('stores', []))
            print(f"✅ 資料庫連線正常")
            print(f"📊 查詢到 {store_count} 個店家")
            print(f"⏱️ 回應時間: {response_time:.2f} 秒")
            return True, {
                'store_count': store_count,
                'response_time': response_time,
                'data_size': len(response.content)
            }
        else:
            print(f"❌ 資料庫查詢失敗，狀態碼: {response.status_code}")
            return False, {
                'status_code': response.status_code,
                'response': response.text,
                'response_time': response_time
            }
            
    except Exception as e:
        print(f"❌ 資料庫連線失敗: {e}")
        return False, {'error': str(e)}

def test_database_performance():
    """測試資料庫效能"""
    print("\n🔍 測試資料庫效能...")
    
    try:
        base_url = os.getenv('CLOUD_RUN_URL', 'https://ordering-helper-backend-1095766716155.asia-east1.run.app')
        
        # 執行多個查詢來測試效能
        test_endpoints = [
            '/api/stores',
            '/api/menu/1',
            '/api/orders?limit=10'
        ]
        
        performance_results = {}
        
        for endpoint in test_endpoints:
            url = f"{base_url}{endpoint}"
            print(f"  測試 {endpoint}...")
            
            try:
                start_time = time.time()
                response = requests.get(url, timeout=30)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    performance_results[endpoint] = {
                        'status': 'success',
                        'response_time': response_time,
                        'data_size': len(response.content),
                        'status_code': response.status_code
                    }
                    print(f"    ✅ 成功 - {response_time:.2f}s")
                else:
                    performance_results[endpoint] = {
                        'status': 'error',
                        'response_time': response_time,
                        'status_code': response.status_code,
                        'error': response.text
                    }
                    print(f"    ❌ 失敗 - {response.status_code}")
                    
            except Exception as e:
                performance_results[endpoint] = {
                    'status': 'exception',
                    'error': str(e)
                }
                print(f"    ❌ 異常 - {e}")
        
        return True, performance_results
        
    except Exception as e:
        print(f"❌ 效能測試失敗: {e}")
        return False, {'error': str(e)}

def test_connection_pool():
    """測試連線池"""
    print("\n🔍 測試連線池...")
    
    try:
        base_url = os.getenv('CLOUD_RUN_URL', 'https://ordering-helper-backend-1095766716155.asia-east1.run.app')
        
        # 同時發送多個請求來測試連線池
        concurrent_requests = 5
        urls = [f"{base_url}/api/stores" for _ in range(concurrent_requests)]
        
        print(f"  發送 {concurrent_requests} 個並發請求...")
        
        import concurrent.futures
        
        def make_request(url):
            start_time = time.time()
            try:
                response = requests.get(url, timeout=30)
                response_time = time.time() - start_time
                return {
                    'status': 'success',
                    'response_time': response_time,
                    'status_code': response.status_code
                }
            except Exception as e:
                response_time = time.time() - start_time
                return {
                    'status': 'error',
                    'response_time': response_time,
                    'error': str(e)
                }
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            results = list(executor.map(make_request, urls))
        total_time = time.time() - start_time
        
        # 分析結果
        successful_requests = sum(1 for r in results if r['status'] == 'success')
        avg_response_time = sum(r['response_time'] for r in results if r['status'] == 'success') / max(successful_requests, 1)
        
        print(f"  📊 並發測試結果:")
        print(f"    總請求數: {concurrent_requests}")
        print(f"    成功請求: {successful_requests}")
        print(f"    總時間: {total_time:.2f}s")
        print(f"    平均回應時間: {avg_response_time:.2f}s")
        
        return True, {
            'concurrent_requests': concurrent_requests,
            'successful_requests': successful_requests,
            'total_time': total_time,
            'avg_response_time': avg_response_time,
            'results': results
        }
        
    except Exception as e:
        print(f"❌ 連線池測試失敗: {e}")
        return False, {'error': str(e)}

def diagnose_connection_issues():
    """診斷連線問題"""
    print("\n🔍 診斷連線問題...")
    
    issues = []
    recommendations = []
    
    # 檢查環境變數
    required_env_vars = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_DATABASE']
    missing_env_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_env_vars:
        issues.append(f"缺少環境變數: {', '.join(missing_env_vars)}")
        recommendations.append("設定必要的資料庫環境變數")
    
    # 檢查 Cloud Run URL
    cloud_run_url = os.getenv('CLOUD_RUN_URL')
    if not cloud_run_url:
        issues.append("未設定 CLOUD_RUN_URL 環境變數")
        recommendations.append("設定正確的 Cloud Run 服務 URL")
    
    # 檢查網路連線
    if cloud_run_url:
        try:
            response = requests.get(f"{cloud_run_url}/api/health", timeout=5)
            if response.status_code != 200:
                issues.append(f"Cloud Run 服務回應異常: {response.status_code}")
                recommendations.append("檢查 Cloud Run 服務狀態和配置")
        except requests.exceptions.ConnectionError:
            issues.append("無法連線到 Cloud Run 服務")
            recommendations.append("檢查網路連線和防火牆設定")
        except requests.exceptions.Timeout:
            issues.append("Cloud Run 服務回應超時")
            recommendations.append("檢查服務負載和超時設定")
    
    # 檢查資料庫連線參數
    db_host = os.getenv('DB_HOST')
    if db_host and ':' in db_host:
        host, port = db_host.split(':', 1)
        try:
            port_num = int(port)
            if port_num < 1 or port_num > 65535:
                issues.append(f"無效的資料庫端口: {port}")
                recommendations.append("檢查資料庫端口設定")
        except ValueError:
            issues.append(f"無效的資料庫端口格式: {port}")
            recommendations.append("使用有效的端口號碼")
    
    return issues, recommendations

def generate_test_report(results):
    """生成測試報告"""
    print("\n" + "="*60)
    print("📊 Cloud MySQL 連線測試報告")
    print("="*60)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"測試時間: {timestamp}")
    
    # 健康檢查結果
    health_success, health_data = results.get('health', (False, {}))
    print(f"\n🏥 Cloud Run 健康檢查: {'✅ 通過' if health_success else '❌ 失敗'}")
    if health_data:
        print(f"   回應資料: {health_data}")
    
    # 資料庫連線結果
    db_success, db_data = results.get('database', (False, {}))
    print(f"\n🗄️ 資料庫連線: {'✅ 通過' if db_success else '❌ 失敗'}")
    if db_data and 'store_count' in db_data:
        print(f"   店家數量: {db_data['store_count']}")
        print(f"   回應時間: {db_data['response_time']:.2f}s")
    
    # 效能測試結果
    perf_success, perf_data = results.get('performance', (False, {}))
    print(f"\n⚡ 效能測試: {'✅ 通過' if perf_success else '❌ 失敗'}")
    if perf_data:
        for endpoint, result in perf_data.items():
            status = "✅" if result.get('status') == 'success' else "❌"
            response_time = result.get('response_time', 0)
            print(f"   {endpoint}: {status} {response_time:.2f}s")
    
    # 連線池測試結果
    pool_success, pool_data = results.get('connection_pool', (False, {}))
    print(f"\n🔗 連線池測試: {'✅ 通過' if pool_success else '❌ 失敗'}")
    if pool_data and 'successful_requests' in pool_data:
        print(f"   並發請求: {pool_data['concurrent_requests']}")
        print(f"   成功請求: {pool_data['successful_requests']}")
        print(f"   平均回應時間: {pool_data['avg_response_time']:.2f}s")
    
    # 問題診斷
    issues, recommendations = results.get('diagnosis', ([], []))
    if issues:
        print(f"\n🚨 發現問題:")
        for issue in issues:
            print(f"   - {issue}")
    
    if recommendations:
        print(f"\n💡 建議:")
        for rec in recommendations:
            print(f"   - {rec}")
    
    # 總結
    total_tests = len([k for k in results.keys() if k != 'diagnosis'])
    passed_tests = sum(1 for k in results.keys() if k != 'diagnosis' and results[k][0])
    
    print(f"\n📈 測試總結: {passed_tests}/{total_tests} 項通過 ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 所有測試通過！Cloud MySQL 連線正常。")
    elif passed_tests >= total_tests * 0.8:
        print("⚠️ 大部分功能正常，建議檢查失敗的項目。")
    else:
        print("🚨 多項測試失敗，建議立即檢查系統配置。")
    
    return results

def save_report_to_file(results, timestamp):
    """保存測試報告到檔案"""
    report_content = f"""# Cloud MySQL 連線測試報告

## 測試時間
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 測試結果

"""
    
    # 健康檢查
    health_success, health_data = results.get('health', (False, {}))
    report_content += f"### Cloud Run 健康檢查: {'✅ 通過' if health_success else '❌ 失敗'}\n"
    if health_data:
        report_content += f"回應資料: {json.dumps(health_data, indent=2, ensure_ascii=False)}\n"
    
    # 資料庫連線
    db_success, db_data = results.get('database', (False, {}))
    report_content += f"\n### 資料庫連線: {'✅ 通過' if db_success else '❌ 失敗'}\n"
    if db_data and 'store_count' in db_data:
        report_content += f"- 店家數量: {db_data['store_count']}\n"
        report_content += f"- 回應時間: {db_data['response_time']:.2f}s\n"
    
    # 效能測試
    perf_success, perf_data = results.get('performance', (False, {}))
    report_content += f"\n### 效能測試: {'✅ 通過' if perf_success else '❌ 失敗'}\n"
    if perf_data:
        for endpoint, result in perf_data.items():
            status = "✅" if result.get('status') == 'success' else "❌"
            response_time = result.get('response_time', 0)
            report_content += f"- {endpoint}: {status} {response_time:.2f}s\n"
    
    # 連線池測試
    pool_success, pool_data = results.get('connection_pool', (False, {}))
    report_content += f"\n### 連線池測試: {'✅ 通過' if pool_success else '❌ 失敗'}\n"
    if pool_data and 'successful_requests' in pool_data:
        report_content += f"- 並發請求: {pool_data['concurrent_requests']}\n"
        report_content += f"- 成功請求: {pool_data['successful_requests']}\n"
        report_content += f"- 平均回應時間: {pool_data['avg_response_time']:.2f}s\n"
    
    # 問題診斷
    issues, recommendations = results.get('diagnosis', ([], []))
    if issues:
        report_content += f"\n## 發現問題\n"
        for issue in issues:
            report_content += f"- {issue}\n"
    
    if recommendations:
        report_content += f"\n## 建議\n"
        for rec in recommendations:
            report_content += f"- {rec}\n"
    
    # 保存到檔案
    filename = f"cloud_mysql_connection_test_{timestamp}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n📄 測試報告已保存到: {filename}")
    return filename

def main():
    """主測試函數"""
    print("🚀 開始 Cloud MySQL 連線測試...")
    print("="*50)
    
    # 檢查環境變數
    cloud_run_url = os.getenv('CLOUD_RUN_URL')
    if not cloud_run_url:
        print("⚠️ 警告: 未設定 CLOUD_RUN_URL 環境變數")
        print("使用預設 URL: https://ordering-helper-backend-1095766716155.asia-east1.run.app")
    
    # 執行測試
    results = {}
    
    results['health'] = test_cloud_run_health()
    results['database'] = test_database_connection()
    results['performance'] = test_database_performance()
    results['connection_pool'] = test_connection_pool()
    
    # 問題診斷
    issues, recommendations = diagnose_connection_issues()
    results['diagnosis'] = (issues, recommendations)
    
    # 生成報告
    generate_test_report(results)
    
    # 保存報告到檔案
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_report_to_file(results, timestamp)

if __name__ == "__main__":
    main()
