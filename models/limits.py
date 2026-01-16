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
            if os.path.exists("docscan_ip_limits.json"):
                with open("docscan_ip_limits.json", 'r', encoding='utf-8') as f:
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
            with open("docscan_ip_limits.json", 'w') as f:
                json.dump(self.ip_limits, f, ensure_ascii=False, indent=2)
            logger.info("💾 IP-лимиты сохранены")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения IP-лимитов: {e}")

    def get_client_ip(self, request):
        """Получаем реальный IP клиента - ВАЖНО: консистентный порядок проверки"""
        x_forwarded_for = request.headers.get('X-Forwarded-For', '')
        x_real_ip = request.headers.get('X-Real-IP', '')
        remote_addr = request.remote_addr or 'None'
        
        # ВАЖНО: Всегда проверяем в одном порядке для консистентности
        # X-Real-IP обычно более надежный (устанавливается прокси/балансировщиком напрямую)
        # X-Forwarded-For может содержать цепочку IP через запятую
        
        if x_real_ip and x_real_ip.strip():
            ip = x_real_ip.strip()
            logger.debug(f"🔍 IP определен из X-Real-IP: {ip}")
            return ip
        elif x_forwarded_for and x_forwarded_for.strip():
            # X-Forwarded-For может содержать цепочку: client, proxy1, proxy2
            # Берем первый IP (оригинальный клиент)
            ip = x_forwarded_for.split(',')[0].strip()
            logger.debug(f"🔍 IP определен из X-Forwarded-For (первый): {ip}")
            return ip
        else:
            ip = remote_addr
            logger.debug(f"🔍 IP определен из remote_addr: {ip}")
            return ip

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
            logger.info(f"📡 IP {real_ip} может сделать анализ ({ip_data['used_today']}/3)")
        else:
            logger.info(f"🚫 IP {real_ip} уже использовал бесплатный анализ сегодня ({ip_data['used_today']}/3)")
        
        return can_analyze

    def record_ip_usage(self, request, user_id=None):
        """Записывает использование для IP"""
        real_ip = self.get_client_ip(request)
        
        if real_ip not in self.ip_limits:
            self.ip_limits[real_ip] = {
                'used_today': 0,
                'last_reset': date.today().isoformat(),
                'first_seen': datetime.now().isoformat(),
                'last_user': user_id
            }
        
        # Сбрасываем лимит IP если новый день
        if self.ip_limits[real_ip]['last_reset'] < date.today().isoformat():
            self.ip_limits[real_ip]['used_today'] = 0
            self.ip_limits[real_ip]['last_reset'] = date.today().isoformat()
        
        # Обновляем последнего пользователя для этого IP
        self.ip_limits[real_ip]['last_user'] = user_id
        
        self.ip_limits[real_ip]['used_today'] += 1
        self.save_ip_limits()
        logger.info(f"📡 Записано использование для IP {real_ip}: {self.ip_limits[real_ip]['used_today']}/3 (user: {user_id})")