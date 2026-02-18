#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для пакетной обработки документов
"""

import os
import json
import logging
import threading
from datetime import datetime
from models.sqlite_users import db, BatchProcessingTask, BatchProcessingFile, AnalysisHistory
from services.file_processing import extract_text_from_file, validate_file
from services.analysis import analyze_text
from utils.analysis_settings_manager import AnalysisSettingsManager

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Менеджер для пакетной обработки документов"""
    
    @staticmethod
    def create_batch_task(user_id, task_name=None, file_count=0):
        """Создать новую пакетную задачу"""
        try:
            task = BatchProcessingTask(
                user_id=user_id,
                task_name=task_name,
                status='pending',
                total_files=file_count,
                processed_files=0,
                failed_files=0,
                created_at=datetime.now().isoformat()
            )
            db.session.add(task)
            db.session.commit()
            
            logger.info(f"✅ Создана пакетная задача {task.id} для пользователя {user_id}")
            return task.id, None
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Ошибка создания пакетной задачи: {e}")
            return None, str(e)
    
    @staticmethod
    def add_file_to_task(task_id, filename, file_path):
        """Добавить файл в пакетную задачу"""
        try:
            file_record = BatchProcessingFile(
                task_id=task_id,
                filename=filename,
                file_path=file_path,
                status='pending',
                created_at=datetime.now().isoformat()
            )
            db.session.add(file_record)
            db.session.commit()
            
            return file_record.id, None
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Ошибка добавления файла в задачу: {e}")
            return None, str(e)
    
    @staticmethod
    def process_batch_task_async(task_id, user_id, app_instance):
        """Асинхронная обработка пакетной задачи (запускается в отдельном потоке)"""
        def process_task():
            # Создаем контекст приложения для работы с БД в отдельном потоке
            with app_instance.app_context():
                try:
                    logger.info(f"🚀 Начало обработки пакетной задачи {task_id}")
                    
                    # Обновляем статус задачи
                    task = BatchProcessingTask.query.get(task_id)
                    if not task:
                        logger.error(f"❌ Задача {task_id} не найдена")
                        return
                    
                    task.status = 'processing'
                    task.started_at = datetime.now().isoformat()
                    db.session.commit()
                
                    # Получаем все файлы задачи
                    files = BatchProcessingFile.query.filter_by(task_id=task_id).all()
                    
                    results = []
                    processed_count = 0
                    failed_count = 0
                    
                    # Загружаем настройки анализа пользователя
                    analysis_settings = None
                    try:
                        user = app_instance.user_manager.get_user(user_id)
                        if user and user.plan == 'premium':
                            analysis_settings = AnalysisSettingsManager.get_user_settings(user_id)
                            if analysis_settings and analysis_settings.get('use_default'):
                                analysis_settings = None
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось загрузить настройки анализа: {e}")
                    
                    # Обрабатываем каждый файл
                    for file_record in files:
                        try:
                            logger.info(f"📄 Обработка файла: {file_record.filename}")
                            
                            file_record.status = 'processing'
                            db.session.commit()
                            
                            # Извлекаем текст из файла
                            if not file_record.file_path:
                                raise Exception(f"Путь к файлу не указан для {file_record.filename}")
                            
                            if not os.path.exists(file_record.file_path):
                                raise Exception(f"Файл не найден: {file_record.file_path}")
                            
                            # extract_text_from_file возвращает либо текст, либо строку ошибки
                            # Проверяем, что это текст (не ошибка)
                            text_result = extract_text_from_file(file_record.file_path, file_record.filename)
                            
                            # Если результат начинается с "❌" или "Ошибка", это ошибка
                            if isinstance(text_result, str) and (text_result.startswith("❌") or text_result.startswith("Ошибка") or text_result.startswith("Ошибка чтения")):
                                raise Exception(text_result)
                            
                            text = text_result
                            # Для PDF пытаемся определить количество страниц
                            pages_count = 1
                            if file_record.filename.lower().endswith('.pdf'):
                                try:
                                    import PyPDF2
                                    with open(file_record.file_path, 'rb') as f:
                                        reader = PyPDF2.PdfReader(f)
                                        pages_count = len(reader.pages)
                                except:
                                    pass
                            
                            if not text or len(text.strip()) < 50:
                                raise Exception("Не удалось извлечь текст или документ слишком короткий")
                            
                            # Получаем пользователя для проверки лимитов
                            user = app_instance.user_manager.get_user(user_id)
                            if not user:
                                raise Exception("Пользователь не найден")
                            
                            # Проверяем лимиты
                            if not app_instance.user_manager.can_analyze(user_id):
                                raise Exception("Достигнут дневной лимит анализов")
                            
                            # Выполняем анализ
                            analysis_result = analyze_text(
                                text=text,
                                user_plan=user.plan if hasattr(user, 'plan') else user.get('plan', 'free'),
                                is_authenticated=True,
                                user_id=user_id,
                                analysis_settings=analysis_settings
                            )
                            
                            # Записываем использование
                            app_instance.user_manager.record_usage(user_id)
                            
                            # Сохраняем в историю
                            history = AnalysisHistory(
                                user_id=user_id,
                                filename=file_record.filename,
                                document_type=analysis_result.get('document_type'),
                                document_type_name=analysis_result.get('document_type_name'),
                                risk_level=analysis_result.get('risk_level'),
                                created_at=datetime.now().isoformat(),
                                analysis_summary=analysis_result.get('summary', '')[:500]
                            )
                            db.session.add(history)
                            db.session.flush()
                            
                            # Обновляем запись файла
                            file_record.status = 'completed'
                            file_record.analysis_result_json = json.dumps(analysis_result, ensure_ascii=False)
                            file_record.analysis_history_id = history.id
                            file_record.processed_at = datetime.now().isoformat()
                            db.session.commit()
                            
                            results.append({
                                'filename': file_record.filename,
                                'status': 'completed',
                                'analysis': analysis_result
                            })
                            
                            processed_count += 1
                            task.processed_files = processed_count
                            db.session.commit()
                            
                            logger.info(f"✅ Файл {file_record.filename} обработан успешно")
                            
                        except Exception as e:
                            logger.error(f"❌ Ошибка обработки файла {file_record.filename}: {e}")
                            file_record.status = 'failed'
                            file_record.error_message = str(e)
                            file_record.processed_at = datetime.now().isoformat()
                            db.session.commit()
                            
                            results.append({
                                'filename': file_record.filename,
                                'status': 'failed',
                                'error': str(e)
                            })
                            
                            failed_count += 1
                            task.failed_files = failed_count
                            db.session.commit()
                    
                    # Сохраняем результаты
                    task.results_json = json.dumps(results, ensure_ascii=False)
                    task.status = 'completed'
                    task.completed_at = datetime.now().isoformat()
                    db.session.commit()
                    
                    logger.info(f"✅ Пакетная задача {task_id} завершена. Обработано: {processed_count}, Ошибок: {failed_count}")
                    
                    # Генерируем сводный отчет (опционально)
                    try:
                        BatchProcessor.generate_summary_report(task_id, results)
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось сгенерировать сводный отчет: {e}")
                    
                    # Создаем уведомление о завершении
                    try:
                        from models.sqlite_users import Notification
                        notification = Notification(
                            user_id=user_id,
                            title=f"Пакетная обработка завершена",
                            message=f"Задача '{task.task_name or f'Задача #{task_id}'}' завершена. Обработано: {processed_count} из {task.total_files} файлов.",
                            type='batch_completed',
                            created_at=datetime.now().isoformat()
                        )
                        db.session.add(notification)
                        db.session.commit()
                        logger.info(f"✅ Уведомление создано для пользователя {user_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось создать уведомление: {e}")
                    
                except Exception as e:
                    logger.error(f"❌ Критическая ошибка обработки пакетной задачи {task_id}: {e}")
                    try:
                        task = BatchProcessingTask.query.get(task_id)
                        if task:
                            task.status = 'failed'
                            task.error_message = str(e)
                            task.completed_at = datetime.now().isoformat()
                            db.session.commit()
                    except Exception as db_error:
                        logger.error(f"❌ Ошибка сохранения статуса ошибки: {db_error}")
        
        # Запускаем обработку в отдельном потоке
        thread = threading.Thread(target=process_task)
        thread.daemon = True
        thread.start()
    
    @staticmethod
    def generate_summary_report(task_id, results):
        """Генерирует сводный отчет по всем документам"""
        try:
            task = BatchProcessingTask.query.get(task_id)
            if not task:
                return
            
            # Подсчитываем статистику
            total = len(results)
            completed = len([r for r in results if r.get('status') == 'completed'])
            failed = len([r for r in results if r.get('status') == 'failed'])
            
            # Подсчитываем типы документов
            doc_types = {}
            risk_levels = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}
            
            for result in results:
                if result.get('status') == 'completed' and result.get('analysis'):
                    analysis = result['analysis']
                    doc_type = analysis.get('document_type_name', 'Неизвестно')
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                    
                    risk = analysis.get('risk_level', 'INFO')
                    risk_levels[risk] = risk_levels.get(risk, 0) + 1
            
            # Создаем простой текстовый отчет
            report_text = f"""
СВОДНЫЙ ОТЧЕТ ПО ПАКЕТНОЙ ОБРАБОТКЕ
Задача: {task.task_name or f'Задача #{task.id}'}
Дата создания: {task.created_at}
Дата завершения: {task.completed_at}

СТАТИСТИКА:
- Всего файлов: {total}
- Успешно обработано: {completed}
- Ошибок: {failed}

ТИПЫ ДОКУМЕНТОВ:
"""
            for doc_type, count in doc_types.items():
                report_text += f"- {doc_type}: {count}\n"
            
            report_text += "\nУРОВНИ РИСКА:\n"
            for risk, count in risk_levels.items():
                if count > 0:
                    report_text += f"- {risk}: {count}\n"
            
            report_text += "\nДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:\n"
            for i, result in enumerate(results, 1):
                report_text += f"\n{i}. {result['filename']}\n"
                if result.get('status') == 'completed':
                    analysis = result.get('analysis', {})
                    report_text += f"   Тип: {analysis.get('document_type_name', 'Неизвестно')}\n"
                    report_text += f"   Уровень риска: {analysis.get('risk_level', 'Не определен')}\n"
                else:
                    report_text += f"   Ошибка: {result.get('error', 'Неизвестная ошибка')}\n"
            
            # Сохраняем отчет в файл
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'reports', 'batch')
            os.makedirs(reports_dir, exist_ok=True)
            
            report_path = os.path.join(reports_dir, f'batch_task_{task_id}_report.txt')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            # Обновляем задачу
            task.summary_report_path = f'static/reports/batch/batch_task_{task_id}_report.txt'
            db.session.commit()
            
            logger.info(f"✅ Сводный отчет создан: {report_path}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации сводного отчета: {e}")
    
    @staticmethod
    def get_task_status(task_id):
        """Получить статус задачи"""
        try:
            task = BatchProcessingTask.query.get(task_id)
            if not task:
                return None, "Задача не найдена"
            return task.to_dict(), None
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса задачи: {e}")
            return None, str(e)
    
    @staticmethod
    def get_user_tasks(user_id, limit=20):
        """Получить все задачи пользователя"""
        try:
            tasks = BatchProcessingTask.query.filter_by(user_id=user_id).order_by(
                BatchProcessingTask.created_at.desc()
            ).limit(limit).all()
            return [task.to_dict() for task in tasks]
        except Exception as e:
            logger.error(f"❌ Ошибка получения задач пользователя: {e}")
            return []
    
    @staticmethod
    def get_task_files(task_id):
        """Получить все файлы задачи"""
        try:
            files = BatchProcessingFile.query.filter_by(task_id=task_id).order_by(
                BatchProcessingFile.created_at.asc()
            ).all()
            return [f.to_dict() for f in files]
        except Exception as e:
            logger.error(f"❌ Ошибка получения файлов задачи: {e}")
            return []

