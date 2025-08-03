# =============================================================================
# 檔案名稱：app/errors.py
# 功能描述：全域錯誤處理和日誌記錄系統
# 主要職責：
# - 處理 HTTP 錯誤（404、500、403 等）
# - 記錄應用程式日誌
# - 提供統一的錯誤回應格式
# - 追蹤 API 呼叫和使用者操作
# 支援功能：
# - 自動錯誤記錄
# - 自定義錯誤頁面
# - API 錯誤處理
# - 操作日誌追蹤
# =============================================================================

import logging
import traceback
from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.exceptions import HTTPException
import os
from datetime import datetime

# 設定日誌
def setup_logging(app):
    """設定應用程式日誌"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 檔案日誌處理器
    file_handler = logging.FileHandler('logs/app.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    file_handler.setFormatter(formatter)
    
    # 設定應用程式日誌
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('應用程式啟動')

# 錯誤處理 Blueprint
errors = Blueprint('errors', __name__)

@errors.app_errorhandler(404)
def not_found_error(error):
    """處理 404 錯誤"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'API 端點不存在'}), 404
    return '<h1>404 - 頁面不存在</h1><p>抱歉，您要尋找的頁面不存在。</p>', 404

@errors.app_errorhandler(500)
def internal_error(error):
    """處理 500 錯誤"""
    # 記錄錯誤
    current_app.logger.error(f'伺服器錯誤: {error}')
    current_app.logger.error(traceback.format_exc())
    
    if request.path.startswith('/api/'):
        return jsonify({'error': '伺服器內部錯誤'}), 500
    return '<h1>500 - 伺服器錯誤</h1><p>抱歉，伺服器發生錯誤。</p>', 500

@errors.app_errorhandler(403)
def forbidden_error(error):
    """處理 403 錯誤"""
    if request.path.startswith('/api/'):
        return jsonify({'error': '權限不足'}), 403
    return render_template('errors/403.html'), 403

@errors.app_errorhandler(HTTPException)
def handle_http_error(error):
    """處理 HTTP 錯誤"""
    if request.path.startswith('/api/'):
        return jsonify({'error': error.description}), error.code
    return render_template('errors/generic.html', error=error), error.code

# 自定義錯誤類別
class APIError(Exception):
    """API 錯誤類別"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv

@errors.app_errorhandler(APIError)
def handle_api_error(error):
    """處理 API 錯誤"""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

# 日誌記錄函數
def log_error(error, context=None):
    """記錄錯誤到日誌"""
    
    error_info = {
        'error': str(error),
        'timestamp': datetime.now().isoformat(),
        'url': request.url,
        'method': request.method,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'context': context
    }
    
    current_app.logger.error(f'錯誤詳情: {error_info}')
    current_app.logger.error(traceback.format_exc())

def log_api_call(endpoint, method, status_code, response_time=None):
    """記錄 API 呼叫"""
    
    api_log = {
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'response_time': response_time,
        'timestamp': datetime.now().isoformat()
    }
    
    current_app.logger.info(f'API 呼叫: {api_log}')

def log_user_action(user_id, action, details=None):
    """記錄使用者操作"""
    
    action_log = {
        'user_id': user_id,
        'action': action,
        'details': details,
        'ip': request.remote_addr,
        'timestamp': datetime.now().isoformat()
    }
    
    current_app.logger.info(f'使用者操作: {action_log}')

def register_error_handlers(app):
    """註冊錯誤處理器"""
    # 設定日誌
    setup_logging(app)
    
    # 註冊錯誤處理 Blueprint
    app.register_blueprint(errors) 