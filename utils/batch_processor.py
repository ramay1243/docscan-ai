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
                            
                            # Генерируем полный отчет (PDF) для документа
                            report_path = None
                            try:
                                from services.pdf_generator import generate_analysis_pdf
                                
                                # Получаем настройки брендинга
                                branding_settings = None
                                try:
                                    from models.sqlite_users import BrandingSettings
                                    branding_obj = BrandingSettings.query.filter_by(user_id=user_id).first()
                                    if branding_obj and branding_obj.is_active:
                                        branding_settings = {
                                            'is_active': True,
                                            'logo_path': branding_obj.logo_path,
                                            'primary_color': branding_obj.primary_color,
                                            'secondary_color': branding_obj.secondary_color,
                                            'company_name': branding_obj.company_name
                                        }
                                except Exception as e:
                                    logger.warning(f"⚠️ Не удалось загрузить настройки брендинга: {e}")
                                
                                reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'reports', 'batch', f'task_{task_id}')
                                os.makedirs(reports_dir, exist_ok=True)
                                
                                safe_filename = "".join(c for c in file_record.filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                                report_filename = f"{safe_filename}_report.pdf"
                                report_path_full = os.path.join(reports_dir, report_filename)
                                
                                # generate_analysis_pdf принимает: (analysis_data, filename="document.pdf", branding_settings=None)
                                pdf_content = generate_analysis_pdf(
                                    analysis_result,  # analysis_data
                                    file_record.filename,  # filename
                                    branding_settings  # branding_settings
                                )
                                
                                with open(report_path_full, 'wb') as f:
                                    f.write(pdf_content)
                                
                                report_path = f'static/reports/batch/task_{task_id}/{report_filename}'
                                logger.info(f"✅ Полный отчет создан: {report_path}")
                            except Exception as e:
                                logger.warning(f"⚠️ Не удалось создать полный отчет для {file_record.filename}: {e}")
                            
                            # Обновляем запись файла
                            file_record.status = 'completed'
                            file_record.analysis_result_json = json.dumps(analysis_result, ensure_ascii=False)
                            file_record.analysis_history_id = history.id
                            file_record.full_report_path = report_path
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
        """Генерирует улучшенный сводный отчет по всем документам"""
        try:
            task = BatchProcessingTask.query.get(task_id)
            if not task:
                return
            
            # Получаем все файлы задачи для доступа к путям отчетов
            files = BatchProcessingFile.query.filter_by(task_id=task_id).all()
            file_reports = {f.filename: f.full_report_path for f in files if f.full_report_path}
            
            # Подсчитываем статистику
            total = len(results)
            completed = len([r for r in results if r.get('status') == 'completed'])
            failed = len([r for r in results if r.get('status') == 'failed'])
            success_rate = int((completed / total * 100)) if total > 0 else 0
            
            # Подсчитываем типы документов
            doc_types = {}
            risk_levels = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}
            
            # Собираем основные проблемы и риски
            all_issues = []
            critical_files = []
            high_risk_files = []
            
            for result in results:
                if result.get('status') == 'completed' and result.get('analysis'):
                    analysis = result['analysis']
                    doc_type = analysis.get('document_type_name', 'Неизвестно')
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                    
                    risk = analysis.get('risk_level', 'INFO')
                    if risk:
                        risk_levels[risk] = risk_levels.get(risk, 0) + 1
                    
                    # Собираем файлы с высоким риском
                    if risk == 'CRITICAL':
                        critical_files.append(result['filename'])
                    elif risk == 'HIGH':
                        high_risk_files.append(result['filename'])
                    
                    # Собираем основные проблемы из разных источников
                    issues_list = []
                    
                    # Из issues
                    issues = analysis.get('issues', [])
                    if isinstance(issues, list):
                        issues_list.extend([str(i) for i in issues if i])
                    elif isinstance(issues, str):
                        issues_list.append(issues)
                    
                    # Из risk_analysis.key_risks
                    if not issues_list:
                        risk_analysis = analysis.get('risk_analysis', {})
                        if isinstance(risk_analysis, dict):
                            key_risks = risk_analysis.get('key_risks', [])
                            if isinstance(key_risks, list):
                                for risk in key_risks[:3]:
                                    if isinstance(risk, dict):
                                        risk_title = risk.get('title', '')
                                        if risk_title:
                                            issues_list.append(risk_title)
                                    elif isinstance(risk, str):
                                        issues_list.append(risk)
                    
                    # Из risks
                    if not issues_list:
                        risks = analysis.get('risks', [])
                        if isinstance(risks, list):
                            issues_list.extend([str(r) for r in risks[:3] if r])
                        elif isinstance(risks, str):
                            issues_list.append(risks)
                    
                    all_issues.extend(issues_list[:3])  # Берем первые 3 проблемы
            
            # Вычисляем время обработки
            processing_time = "Неизвестно"
            if task.started_at and task.completed_at:
                try:
                    start = datetime.fromisoformat(task.started_at)
                    end = datetime.fromisoformat(task.completed_at)
                    delta = end - start
                    processing_time = f"{delta.total_seconds():.1f} секунд"
                except:
                    pass
            
            # Создаем улучшенный отчет
            report_text = f"""
{'='*80}
СВОДНЫЙ ОТЧЕТ ПО ПАКЕТНОЙ ОБРАБОТКЕ ДОКУМЕНТОВ
{'='*80}

ОБЩАЯ ИНФОРМАЦИЯ:
- Название задачи: {task.task_name or f'Задача #{task.id}'}
- ID задачи: {task.id}
- Дата создания: {task.created_at}
- Дата завершения: {task.completed_at}
- Время обработки: {processing_time}

{'='*80}
СТАТИСТИКА ОБРАБОТКИ:
{'='*80}
- Всего файлов: {total}
- Успешно обработано: {completed}
- Ошибок: {failed}
- Процент успешности: {success_rate}%

{'='*80}
АНАЛИЗ ТИПОВ ДОКУМЕНТОВ:
{'='*80}
"""
            if doc_types:
                for doc_type, count in sorted(doc_types.items(), key=lambda x: x[1], reverse=True):
                    percentage = int((count / completed * 100)) if completed > 0 else 0
                    report_text += f"- {doc_type}: {count} ({percentage}%)\n"
            else:
                report_text += "- Типы документов не определены\n"
            
            report_text += f"\n{'='*80}\nАНАЛИЗ УРОВНЕЙ РИСКА:\n{'='*80}\n"
            risk_names = {
                'CRITICAL': 'Критический',
                'HIGH': 'Высокий',
                'MEDIUM': 'Средний',
                'LOW': 'Низкий',
                'INFO': 'Информационный'
            }
            
            total_risks = sum(risk_levels.values())
            for risk, count in risk_levels.items():
                if count > 0:
                    percentage = int((count / total_risks * 100)) if total_risks > 0 else 0
                    report_text += f"- {risk_names.get(risk, risk)} ({risk}): {count} ({percentage}%)\n"
            
            # Анализ рисковости
            high_risk_count = risk_levels.get('CRITICAL', 0) + risk_levels.get('HIGH', 0)
            if high_risk_count > 0:
                high_risk_percent = int((high_risk_count / total_risks * 100)) if total_risks > 0 else 0
                report_text += f"\n⚠️ ВНИМАНИЕ: {high_risk_count} документов ({high_risk_percent}%) имеют высокий или критический уровень риска!\n"
            
            # Сводка по проблемам
            if critical_files or high_risk_files:
                report_text += f"\n{'='*80}\nКРИТИЧЕСКИЕ И ВЫСОКОРИСКОВАННЫЕ ДОКУМЕНТЫ:\n{'='*80}\n"
                if critical_files:
                    report_text += f"\n🔴 КРИТИЧЕСКИЙ РИСК ({len(critical_files)} документов):\n"
                    for filename in critical_files:
                        report_text += f"   - {filename}\n"
                if high_risk_files:
                    report_text += f"\n🟠 ВЫСОКИЙ РИСК ({len(high_risk_files)} документов):\n"
                    for filename in high_risk_files:
                        report_text += f"   - {filename}\n"
            
            # Основные проблемы
            if all_issues:
                report_text += f"\n{'='*80}\nОСНОВНЫЕ НАЙДЕННЫЕ ПРОБЛЕМЫ И РИСКИ:\n{'='*80}\n"
                unique_issues = list(dict.fromkeys(all_issues))[:10]  # Уникальные, максимум 10
                for i, issue in enumerate(unique_issues, 1):
                    report_text += f"{i}. {issue}\n"
            
            report_text += f"\n{'='*80}\nДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ ПО КАЖДОМУ ДОКУМЕНТУ:\n{'='*80}\n"
            for i, result in enumerate(results, 1):
                report_text += f"\n{i}. {result['filename']}\n"
                report_text += f"   {'-'*76}\n"
                if result.get('status') == 'completed':
                    analysis = result.get('analysis', {})
                    doc_type = analysis.get('document_type_name', 'Неизвестно')
                    risk = analysis.get('risk_level', 'INFO')
                    risk_display = risk_names.get(risk, risk) if risk else 'Не определен'
                    
                    report_text += f"   Статус: ✅ Успешно обработан\n"
                    report_text += f"   Тип документа: {doc_type}\n"
                    report_text += f"   Уровень риска: {risk_display} ({risk if risk else 'N/A'})\n"
                    
                    # Краткое резюме - извлекаем из разных возможных полей
                    summary = analysis.get('summary', '')
                    if not summary:
                        # Пытаемся извлечь из executive_summary
                        exec_summary = analysis.get('executive_summary', {})
                        if isinstance(exec_summary, dict):
                            summary = exec_summary.get('risk_description', '') or exec_summary.get('decision_support', '')
                    
                    if not summary:
                        # Пытаемся извлечь из expert_analysis
                        expert_analysis = analysis.get('expert_analysis', {})
                        if isinstance(expert_analysis, dict):
                            # Берем первую непустую секцию
                            for key in ['legal_expertise', 'financial_analysis', 'operational_risks', 'strategic_assessment']:
                                section_text = expert_analysis.get(key, '')
                                if section_text and len(section_text) > 20:
                                    summary = section_text
                                    break
                    
                    if summary:
                        summary_short = summary[:200] + '...' if len(summary) > 200 else summary
                        report_text += f"   Краткое резюме: {summary_short}\n"
                    
                    # Основные проблемы - извлекаем из key_risks
                    issues = []
                    
                    # Сначала пытаемся получить из issues
                    issues_raw = analysis.get('issues', [])
                    if issues_raw:
                        if isinstance(issues_raw, list):
                            issues = [str(item) for item in issues_raw if item]
                        elif isinstance(issues_raw, str):
                            issues = [issues_raw]
                    
                    # Если issues нет, пытаемся извлечь из risk_analysis.key_risks
                    if not issues:
                        risk_analysis = analysis.get('risk_analysis', {})
                        if isinstance(risk_analysis, dict):
                            key_risks = risk_analysis.get('key_risks', [])
                            if isinstance(key_risks, list):
                                for risk in key_risks[:3]:
                                    if isinstance(risk, dict):
                                        # Формируем строку из риска
                                        risk_title = risk.get('title', '')
                                        risk_desc = risk.get('description', '')
                                        risk_level = risk.get('level', '')
                                        if risk_title:
                                            issue_text = f"{risk_level}: {risk_title}"
                                            if risk_desc:
                                                issue_text += f" - {risk_desc[:100]}"
                                            issues.append(issue_text)
                                    elif isinstance(risk, str):
                                        issues.append(risk)
                    
                    # Если все еще нет, пытаемся извлечь из risks
                    if not issues:
                        risks = analysis.get('risks', [])
                        if isinstance(risks, list):
                            issues = [str(r) for r in risks[:3] if r]
                        elif isinstance(risks, str):
                            issues = [risks]
                    
                    if issues:
                        report_text += f"   Основные проблемы:\n"
                        for issue in issues[:3]:
                            if issue and issue.strip():
                                report_text += f"      • {issue}\n"
                    
                    # Ссылка на полный отчет
                    report_path = file_reports.get(result['filename'])
                    if report_path:
                        # Убираем "static/reports/batch/" из начала пути для URL
                        url_path = report_path
                        if url_path.startswith('static/reports/batch/'):
                            url_path = url_path.replace('static/reports/batch/', '')
                        elif url_path.startswith('reports/batch/'):
                            url_path = url_path.replace('reports/batch/', '')
                        elif url_path.startswith('static/'):
                            url_path = url_path.replace('static/', '')
                        
                        # Получаем базовый URL из переменных окружения
                        import os
                        base_url = os.getenv('BASE_URL', 'https://docscan-ai.ru')
                        # Убираем слэш в конце, если есть
                        base_url = base_url.rstrip('/')
                        
                        # Формируем полную ссылку
                        full_url = f"{base_url}/batch-report/{url_path}"
                        report_text += f"   📄 Полный отчет: {full_url}\n"
                else:
                    report_text += f"   Статус: ❌ Ошибка обработки\n"
                    report_text += f"   Ошибка: {result.get('error', 'Неизвестная ошибка')}\n"
            
            # Рекомендации
            report_text += f"\n{'='*80}\nРЕКОМЕНДАЦИИ:\n{'='*80}\n"
            if critical_files or high_risk_files:
                report_text += f"1. ⚠️ Обратите особое внимание на документы с критическим и высоким уровнем риска.\n"
                report_text += f"2. 📋 Рекомендуется детально изучить полные отчеты по этим документам.\n"
                report_text += f"3. 🔍 Проведите дополнительную проверку документов с высоким риском.\n"
            else:
                report_text += f"1. ✅ Все документы имеют приемлемый уровень риска.\n"
                report_text += f"2. 📋 Рекомендуется ознакомиться с полными отчетами для детального анализа.\n"
            
            if failed > 0:
                report_text += f"4. 🔧 Проверьте файлы с ошибками обработки и попробуйте обработать их повторно.\n"
            
            report_text += f"\n{'='*80}\n"
            report_text += f"Сгенерировано: {datetime.now().isoformat()}\n"
            report_text += f"{'='*80}\n"
            
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

