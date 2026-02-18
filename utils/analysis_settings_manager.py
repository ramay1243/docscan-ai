#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для управления настройками анализа документов
"""

import json
import logging
from datetime import datetime
from models.sqlite_users import db, AnalysisSettings, AnalysisTemplate, User

logger = logging.getLogger(__name__)

class AnalysisSettingsManager:
    """Менеджер для работы с настройками анализа"""
    
    @staticmethod
    def get_user_settings(user_id):
        """Получить настройки анализа пользователя"""
        try:
            settings = AnalysisSettings.query.filter_by(user_id=user_id).first()
            if settings:
                return settings.to_dict()
            
            # Если настроек нет, возвращаем настройки по умолчанию
            return {
                'user_id': user_id,
                'legal_priority': 5,
                'financial_priority': 5,
                'operational_priority': 5,
                'strategic_priority': 5,
                'detail_level': 'standard',
                'custom_checks': [],
                'active_template': None,
                'use_default': True
            }
        except Exception as e:
            logger.error(f"❌ Ошибка получения настроек анализа: {e}")
            return None
    
    @staticmethod
    def save_user_settings(user_id, settings_data):
        """Сохранить настройки анализа пользователя"""
        try:
            # Проверяем, что пользователь существует и имеет бизнес-тариф
            user = User.query.filter_by(user_id=user_id).first()
            if not user:
                return False, "Пользователь не найден"
            
            if user.plan != 'premium':
                return False, "Настройки анализа доступны только для бизнес-тарифа"
            
            # Получаем или создаем настройки
            settings = AnalysisSettings.query.filter_by(user_id=user_id).first()
            
            if not settings:
                settings = AnalysisSettings(
                    user_id=user_id,
                    created_at=datetime.now().isoformat()
                )
                db.session.add(settings)
            
            # Обновляем настройки
            settings.legal_priority = settings_data.get('legal_priority', 5)
            settings.financial_priority = settings_data.get('financial_priority', 5)
            settings.operational_priority = settings_data.get('operational_priority', 5)
            settings.strategic_priority = settings_data.get('strategic_priority', 5)
            settings.detail_level = settings_data.get('detail_level', 'standard')
            settings.custom_checks = json.dumps(settings_data.get('custom_checks', []), ensure_ascii=False)
            settings.active_template = settings_data.get('active_template')
            settings.use_default = settings_data.get('use_default', False)
            settings.updated_at = datetime.now().isoformat()
            
            db.session.commit()
            
            logger.info(f"✅ Настройки анализа сохранены для пользователя {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Ошибка сохранения настроек анализа: {e}")
            return False, str(e)
    
    @staticmethod
    def reset_to_default(user_id):
        """Сбросить настройки к умолчанию"""
        try:
            settings = AnalysisSettings.query.filter_by(user_id=user_id).first()
            if settings:
                settings.use_default = True
                settings.updated_at = datetime.now().isoformat()
                db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Ошибка сброса настроек: {e}")
            return False, str(e)
    
    @staticmethod
    def create_template(user_id, template_name, settings_data):
        """Создать шаблон настроек"""
        try:
            user = User.query.filter_by(user_id=user_id).first()
            if not user or user.plan != 'premium':
                return False, "Шаблоны доступны только для бизнес-тарифа"
            
            # Проверяем, не существует ли уже шаблон с таким именем
            existing = AnalysisTemplate.query.filter_by(
                user_id=user_id,
                name=template_name
            ).first()
            
            if existing:
                return False, "Шаблон с таким именем уже существует"
            
            template = AnalysisTemplate(
                user_id=user_id,
                name=template_name,
                legal_priority=settings_data.get('legal_priority', 5),
                financial_priority=settings_data.get('financial_priority', 5),
                operational_priority=settings_data.get('operational_priority', 5),
                strategic_priority=settings_data.get('strategic_priority', 5),
                detail_level=settings_data.get('detail_level', 'standard'),
                custom_checks=json.dumps(settings_data.get('custom_checks', []), ensure_ascii=False),
                created_at=datetime.now().isoformat()
            )
            
            db.session.add(template)
            db.session.commit()
            
            logger.info(f"✅ Шаблон '{template_name}' создан для пользователя {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Ошибка создания шаблона: {e}")
            return False, str(e)
    
    @staticmethod
    def get_user_templates(user_id):
        """Получить все шаблоны пользователя"""
        try:
            templates = AnalysisTemplate.query.filter_by(user_id=user_id).order_by(
                AnalysisTemplate.created_at.desc()
            ).all()
            return [t.to_dict() for t in templates]
        except Exception as e:
            logger.error(f"❌ Ошибка получения шаблонов: {e}")
            return []
    
    @staticmethod
    def apply_template(user_id, template_id):
        """Применить шаблон к настройкам пользователя"""
        try:
            template = AnalysisTemplate.query.filter_by(
                id=template_id,
                user_id=user_id
            ).first()
            
            if not template:
                return False, "Шаблон не найден"
            
            # Получаем или создаем настройки
            settings = AnalysisSettings.query.filter_by(user_id=user_id).first()
            
            if not settings:
                settings = AnalysisSettings(
                    user_id=user_id,
                    created_at=datetime.now().isoformat()
                )
                db.session.add(settings)
            
            # Применяем настройки из шаблона
            settings.legal_priority = template.legal_priority
            settings.financial_priority = template.financial_priority
            settings.operational_priority = template.operational_priority
            settings.strategic_priority = template.strategic_priority
            settings.detail_level = template.detail_level
            settings.custom_checks = template.custom_checks
            settings.active_template = template.name
            settings.use_default = False
            settings.updated_at = datetime.now().isoformat()
            
            db.session.commit()
            
            logger.info(f"✅ Шаблон '{template.name}' применен для пользователя {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Ошибка применения шаблона: {e}")
            return False, str(e)
    
    @staticmethod
    def delete_template(user_id, template_id):
        """Удалить шаблон"""
        try:
            template = AnalysisTemplate.query.filter_by(
                id=template_id,
                user_id=user_id
            ).first()
            
            if not template:
                return False, "Шаблон не найден"
            
            db.session.delete(template)
            db.session.commit()
            
            logger.info(f"✅ Шаблон удален для пользователя {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Ошибка удаления шаблона: {e}")
            return False, str(e)

