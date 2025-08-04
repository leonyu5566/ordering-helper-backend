# =============================================================================
# 檔案名稱：app/gradual_migration.py
# 功能描述：漸進式遷移模組，確保不影響現有功能
# 主要功能：
# - 漸進式功能遷移
# - 完整的測試驗證
# - 性能監控和優化
# - 回滾機制
# =============================================================================

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import threading
import queue

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationStage(Enum):
    """遷移階段"""
    PREPARATION = "preparation"
    TESTING = "testing"
    SMALL_SCALE = "small_scale"
    MEDIUM_SCALE = "medium_scale"
    FULL_DEPLOYMENT = "full_deployment"
    ROLLBACK = "rollback"

class MigrationStatus(Enum):
    """遷移狀態"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class MigrationConfig:
    """遷移配置"""
    # 功能開關
    enable_langchain: bool = False
    enable_fallback: bool = True
    enable_monitoring: bool = True
    
    # 流量控制
    traffic_percentage: float = 0.0  # 0.0 = 0%, 1.0 = 100%
    max_concurrent_requests: int = 10
    
    # 性能閾值
    max_response_time: float = 5.0  # 秒
    min_success_rate: float = 0.95  # 95%
    max_error_rate: float = 0.05    # 5%
    
    # 監控設定
    monitoring_interval: int = 60    # 秒
    alert_threshold: float = 0.1     # 10% 錯誤率觸發警報

class PerformanceMetrics:
    """性能指標"""
    
    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.response_times = []
        self.errors = []
        self.lock = threading.Lock()
    
    def record_request(self, success: bool, response_time: float, error: str = None):
        """記錄請求"""
        with self.lock:
            self.request_count += 1
            self.total_response_time += response_time
            self.response_times.append(response_time)
            
            if success:
                self.success_count += 1
            else:
                self.error_count += 1
                if error:
                    self.errors.append(error)
    
    def get_metrics(self) -> Dict:
        """獲取指標"""
        with self.lock:
            if self.request_count == 0:
                return {
                    "request_count": 0,
                    "success_rate": 0.0,
                    "error_rate": 0.0,
                    "avg_response_time": 0.0,
                    "recent_errors": []
                }
            
            success_rate = self.success_count / self.request_count
            error_rate = self.error_count / self.request_count
            avg_response_time = self.total_response_time / self.request_count
            
            return {
                "request_count": self.request_count,
                "success_rate": success_rate,
                "error_rate": error_rate,
                "avg_response_time": avg_response_time,
                "recent_errors": self.errors[-10:]  # 最近10個錯誤
            }
    
    def reset(self):
        """重置指標"""
        with self.lock:
            self.request_count = 0
            self.success_count = 0
            self.error_count = 0
            self.total_response_time = 0.0
            self.response_times = []
            self.errors = []

class GradualMigration:
    """漸進式遷移管理器"""
    
    def __init__(self, config: MigrationConfig = None):
        self.config = config or MigrationConfig()
        self.stage = MigrationStage.PREPARATION
        self.status = MigrationStatus.NOT_STARTED
        self.metrics = PerformanceMetrics()
        self.monitoring_thread = None
        self.monitoring_active = False
        self.alert_queue = queue.Queue()
        
        # 初始化組件
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化組件"""
        try:
            # 檢查 LangChain 可用性
            from app.langchain_integration import get_integration
            self.langchain_integration = get_integration()
            
            # 檢查原始功能可用性
            self.original_functions = self._get_original_functions()
            
            logger.info("✅ 漸進式遷移管理器初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 漸進式遷移管理器初始化失敗：{e}")
            self.status = MigrationStatus.FAILED
    
    def _get_original_functions(self) -> Dict:
        """獲取原始功能"""
        try:
            # 導入原始功能
            from app.api.helpers import process_menu_with_gemini, translate_text
            from app.webhook.routes import get_ai_recommendations
            
            return {
                "menu_ocr": process_menu_with_gemini,
                "translation": translate_text,
                "recommendation": get_ai_recommendations
            }
        except Exception as e:
            logger.error(f"獲取原始功能失敗：{e}")
            return {}
    
    def should_use_langchain(self, user_id: str = None) -> bool:
        """判斷是否應該使用 LangChain"""
        if not self.config.enable_langchain:
            return False
        
        # 基於流量百分比的決定
        if user_id:
            # 使用用戶 ID 的 hash 來決定
            import hashlib
            hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            user_percentage = (hash_value % 100) / 100.0
            
            return user_percentage < self.config.traffic_percentage
        else:
            # 隨機決定
            import random
            return random.random() < self.config.traffic_percentage
    
    def safe_process_menu_ocr(self, image_path: str, target_language: str = 'en', 
                            user_id: str = None) -> Dict:
        """安全的菜單 OCR 處理"""
        start_time = time.time()
        
        try:
            if self.should_use_langchain(user_id):
                # 使用 LangChain
                result = self.langchain_integration.process_menu_ocr_langchain(
                    image_path, target_language
                )
                success = result.get("success", False)
            else:
                # 使用原始功能
                result = self.original_functions["menu_ocr"](image_path, target_language)
                success = result.get("success", False)
            
            response_time = time.time() - start_time
            
            # 記錄指標
            self.metrics.record_request(success, response_time)
            
            # 檢查性能閾值
            if response_time > self.config.max_response_time:
                logger.warning(f"⚠️ 回應時間過長：{response_time:.2f}秒")
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            self.metrics.record_request(False, response_time, str(e))
            
            # 回退到原始功能
            if self.config.enable_fallback:
                logger.warning(f"🔄 回退到原始功能：{e}")
                return self.original_functions["menu_ocr"](image_path, target_language)
            else:
                raise e
    
    def safe_translate_text(self, text: str, target_language: str = 'en', 
                          user_id: str = None) -> str:
        """安全的文字翻譯"""
        start_time = time.time()
        
        try:
            if self.should_use_langchain(user_id):
                # 使用 LangChain
                result = self.langchain_integration.translate_text_langchain(
                    text, target_language
                )
                translated_text = result.get("translated_text", text)
                success = translated_text != text
            else:
                # 使用原始功能
                translated_text = self.original_functions["translation"](text, target_language)
                success = translated_text != text
            
            response_time = time.time() - start_time
            
            # 記錄指標
            self.metrics.record_request(success, response_time)
            
            return translated_text
            
        except Exception as e:
            response_time = time.time() - start_time
            self.metrics.record_request(False, response_time, str(e))
            
            # 回退到原始功能
            if self.config.enable_fallback:
                logger.warning(f"🔄 回退到原始功能：{e}")
                return self.original_functions["translation"](text, target_language)
            else:
                raise e
    
    def safe_get_recommendations(self, food_request: str, user_language: str = 'zh',
                               user_id: str = None) -> List[Dict]:
        """安全的餐飲推薦"""
        start_time = time.time()
        
        try:
            if self.should_use_langchain(user_id):
                # 使用 LangChain
                result = self.langchain_integration.get_recommendations_langchain(
                    food_request, user_language
                )
                recommendations = result.get("recommendations", [])
                success = len(recommendations) > 0
            else:
                # 使用原始功能
                recommendations = self.original_functions["recommendation"](
                    food_request, user_language
                )
                success = len(recommendations) > 0
            
            response_time = time.time() - start_time
            
            # 記錄指標
            self.metrics.record_request(success, response_time)
            
            return recommendations
            
        except Exception as e:
            response_time = time.time() - start_time
            self.metrics.record_request(False, response_time, str(e))
            
            # 回退到原始功能
            if self.config.enable_fallback:
                logger.warning(f"🔄 回退到原始功能：{e}")
                return self.original_functions["recommendation"](food_request, user_language)
            else:
                raise e
    
    def start_monitoring(self):
        """開始監控"""
        if not self.config.enable_monitoring:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        logger.info("📊 監控已啟動")
    
    def stop_monitoring(self):
        """停止監控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("📊 監控已停止")
    
    def _monitoring_loop(self):
        """監控循環"""
        while self.monitoring_active:
            try:
                metrics = self.metrics.get_metrics()
                
                # 檢查性能閾值
                if metrics["error_rate"] > self.config.alert_threshold:
                    self._send_alert("高錯誤率", metrics)
                
                if metrics["avg_response_time"] > self.config.max_response_time:
                    self._send_alert("回應時間過長", metrics)
                
                if metrics["success_rate"] < self.config.min_success_rate:
                    self._send_alert("成功率過低", metrics)
                
                # 記錄指標
                logger.info(f"📊 性能指標：{json.dumps(metrics, indent=2)}")
                
                time.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                logger.error(f"監控循環錯誤：{e}")
                time.sleep(self.config.monitoring_interval)
    
    def _send_alert(self, alert_type: str, metrics: Dict):
        """發送警報"""
        alert = {
            "type": alert_type,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "stage": self.stage.value,
            "status": self.status.value
        }
        
        self.alert_queue.put(alert)
        logger.warning(f"🚨 警報：{alert_type} - {json.dumps(metrics, indent=2)}")
    
    def get_alerts(self) -> List[Dict]:
        """獲取警報"""
        alerts = []
        while not self.alert_queue.empty():
            alerts.append(self.alert_queue.get())
        return alerts
    
    def update_traffic_percentage(self, percentage: float):
        """更新流量百分比"""
        if 0.0 <= percentage <= 1.0:
            self.config.traffic_percentage = percentage
            logger.info(f"📈 流量百分比已更新：{percentage * 100:.1f}%")
        else:
            logger.error(f"❌ 無效的流量百分比：{percentage}")
    
    def rollback(self):
        """回滾到原始功能"""
        self.config.enable_langchain = False
        self.config.traffic_percentage = 0.0
        self.status = MigrationStatus.ROLLED_BACK
        logger.warning("🔄 已回滾到原始功能")
    
    def get_migration_status(self) -> Dict:
        """獲取遷移狀態"""
        metrics = self.metrics.get_metrics()
        alerts = self.get_alerts()
        
        return {
            "stage": self.stage.value,
            "status": self.status.value,
            "config": {
                "enable_langchain": self.config.enable_langchain,
                "traffic_percentage": self.config.traffic_percentage,
                "enable_fallback": self.config.enable_fallback,
                "enable_monitoring": self.config.enable_monitoring
            },
            "metrics": metrics,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }

# 全域遷移管理器實例
migration_manager = GradualMigration()

def get_migration_manager() -> GradualMigration:
    """獲取遷移管理器實例"""
    return migration_manager

# 便捷函數
def safe_menu_ocr(image_path: str, target_language: str = 'en', user_id: str = None) -> Dict:
    """安全的菜單 OCR"""
    return migration_manager.safe_process_menu_ocr(image_path, target_language, user_id)

def safe_translate_text(text: str, target_language: str = 'en', user_id: str = None) -> str:
    """安全的文字翻譯"""
    return migration_manager.safe_translate_text(text, target_language, user_id)

def safe_get_recommendations(food_request: str, user_language: str = 'zh', user_id: str = None) -> List[Dict]:
    """安全的餐飲推薦"""
    return migration_manager.safe_get_recommendations(food_request, user_language, user_id) 