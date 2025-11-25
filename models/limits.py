import json
import os
from datetime import datetime, date
from config import Config
import logging

logger = logging.getLogger(__name__)

class IPLimitManager:
    def __init__(self):
        self.ip_limits = self.load_ip_limits()
        logger.info(f"🌐 Менеджер IP-лимитов загружен: {len(self.ip_limits)} IP-адресов")

    def load_ip_limits(self):
        """Загружает лимиты по IP из файла"""
        try:
            if os.path.exists(Config.IP_LIMITS_FILE):
                with open(Config.IP_LIMITS_FILE, 'w', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Очищаем старые записи (старше 1 дня)
                    today = date.today().isoformat()
                    clean_data = {}
                    for ip, ip_data in data.items():
                        if ip_data.get('last_reset', today) >= today:
                            clean_data[ip] = ip_data
                    
                    logger.info(f"✅ Загружено {len(clean_data)} IP-адресов")
                    return clean_data
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки IP-лимитов: {e}")
        
        return {}

    def save_ip_limits(self):
        """Сохраняет лимиты по IP в файл"""
        try:
            with open("docscan_ip_limits.json", 'w') as f:  # ← ПРАВИЛЬНО!
                json.dump(self.ip_limits, f, ensure_ascii=False, indent=2)
            logger.info("💾 IP-лимиты сохранены")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения IP-лимитов: {e}")

    def get_client_ip(self, request):
        """Получаем реальный IP клиента на Render"""
        if request.headers.get('X-Forwarded-For'):
            # На Render используем этот заголовок
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr

    def can_analyze_by_ip(self, request):
        """Проверяет может ли IP сделать анализ"""
        real_ip = self.get_client_ip(request)
        logger.info(f"🔍 IP клиента: {real_ip}")
        
        # Исключаем локальные IP для тестирования
        if real_ip in ['127.0.0.1', 'localhost']:
            logger.info("✅ Локальный IP - пропускаем проверку")
            return True
            
        if real_ip not in self.ip_limits:
            self.ip_limits[real_ip] = {
                'used_today': 0,
                'last_reset': date.today().isoformat(),
                'first_seen': datetime.now().isoformat()
            }
            logger.info(f"➕ Новый IP добавлен: {real_ip}")
        
        ip_data = self.ip_limits[real_ip]
        
        # Сбрасываем лимит если новый день
        if ip_data['last_reset'] < date.today().isoformat():
            ip_data['used_today'] = 0
            ip_data['last_reset'] = date.today().isoformat()
            logger.info(f"🔄 Сброшен лимит для IP {real_ip}")
        
        # МАКСИМУМ 1 БЕСПЛАТНЫЙ АНАЛИЗ В ДЕНЬ С ОДНОГО IP
        can_analyze = ip_data['used_today'] < 1
        
        if can_analyze:
            logger.info(f"📡 IP {real_ip} может сделать анализ ({ip_data['used_today']}/1)")
        else:
            logger.info(f"🚫 IP {real_ip} уже использовал бесплатный анализ сегодня ({ip_data['used_today']}/1)")
        
        return can_analyze

    def record_ip_usage(self, request):
        """Записывает использование для IP"""
        real_ip = self.get_client_ip(request)
        
        if real_ip not in self.ip_limits:
            self.ip_limits[real_ip] = {
                'used_today': 0,
                'last_reset': date.today().isoformat(),
                'first_seen': datetime.now().isoformat()
            }
        
        # Сбрасываем лимит IP если новый день
        if self.ip_limits[real_ip]['last_reset'] < date.today().isoformat():
            self.ip_limits[real_ip]['used_today'] = 0
            self.ip_limits[real_ip]['last_reset'] = date.today().isoformat()
        
        self.ip_limits[real_ip]['used_today'] += 1
        self.save_ip_limits()
        logger.info(f"📡 Записано использование для IP {real_ip}: {self.ip_limits[real_ip]['used_today']}/1")
