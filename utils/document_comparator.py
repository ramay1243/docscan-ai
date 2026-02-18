#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для сравнения документов
"""

import os
import json
import logging
import difflib
from datetime import datetime
from models.sqlite_users import db, DocumentComparison
from services.file_processing import extract_text_from_file
from config import Config
import requests

logger = logging.getLogger(__name__)

class DocumentComparator:
    """Менеджер для сравнения документов"""
    
    @staticmethod
    def create_comparison(user_id, original_filename, original_path, modified_filename, modified_path):
        """Создать новую задачу сравнения"""
        try:
            comparison = DocumentComparison(
                user_id=user_id,
                original_filename=original_filename,
                original_file_path=original_path,
                modified_filename=modified_filename,
                modified_file_path=modified_path,
                status='pending',
                created_at=datetime.now().isoformat()
            )
            db.session.add(comparison)
            db.session.commit()
            logger.info(f"✅ Создано сравнение {comparison.id} для пользователя {user_id}")
            return comparison.id, None
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Ошибка создания сравнения: {e}")
            return None, str(e)
    
    @staticmethod
    def compare_documents(comparison_id, user_id, app_instance):
        """Сравнить два документа"""
        try:
            comparison = DocumentComparison.query.get(comparison_id)
            if not comparison:
                return None, "Сравнение не найдено"
            
            comparison.status = 'processing'
            db.session.commit()
            
            logger.info(f"🔍 Начало сравнения документов {comparison_id}")
            
            # Извлекаем текст из обоих документов
            original_text = extract_text_from_file(comparison.original_file_path, comparison.original_filename)
            modified_text = extract_text_from_file(comparison.modified_file_path, comparison.modified_filename)
            
            if not original_text or len(original_text.strip()) < 10:
                raise Exception("Не удалось извлечь текст из оригинального документа")
            
            if not modified_text or len(modified_text.strip()) < 10:
                raise Exception("Не удалось извлечь текст из измененного документа")
            
            # Нормализуем текст для сравнения
            original_lines = [line.strip() for line in original_text.split('\n') if line.strip()]
            modified_lines = [line.strip() for line in modified_text.split('\n') if line.strip()]
            
            # Используем difflib для сравнения
            differ = difflib.Differ()
            diff = list(differ.compare(original_lines, modified_lines))
            
            # Анализируем различия
            changes = {
                'added': [],
                'removed': [],
                'modified': [],
                'unchanged': []
            }
            
            current_change = None
            for line in diff:
                if line.startswith('+ '):
                    text = line[2:]
                    if text.strip():
                        changes['added'].append(text)
                        if current_change and current_change['type'] == 'removed':
                            changes['modified'].append({
                                'original': current_change['text'],
                                'modified': text
                            })
                            current_change = None
                        else:
                            current_change = {'type': 'added', 'text': text}
                elif line.startswith('- '):
                    text = line[2:]
                    if text.strip():
                        changes['removed'].append(text)
                        current_change = {'type': 'removed', 'text': text}
                elif line.startswith('  '):
                    text = line[2:]
                    if text.strip():
                        changes['unchanged'].append(text)
                    current_change = None
            
            # Подсчитываем статистику
            total_changes = len(changes['added']) + len(changes['removed']) + len(changes['modified'])
            
            # Формируем текст для анализа AI
            changes_summary = []
            if changes['added']:
                changes_summary.append(f"Добавлено {len(changes['added'])} фрагментов:")
                for i, change in enumerate(changes['added'][:5], 1):
                    changes_summary.append(f"{i}. {change[:200]}")
            
            if changes['removed']:
                changes_summary.append(f"\nУдалено {len(changes['removed'])} фрагментов:")
                for i, change in enumerate(changes['removed'][:5], 1):
                    changes_summary.append(f"{i}. {change[:200]}")
            
            if changes['modified']:
                changes_summary.append(f"\nИзменено {len(changes['modified'])} фрагментов:")
                for i, change in enumerate(changes['modified'][:3], 1):
                    changes_summary.append(f"{i}. Было: {change['original'][:150]}")
                    changes_summary.append(f"   Стало: {change['modified'][:150]}")
            
            changes_text = '\n'.join(changes_summary)
            
            # Анализируем изменения через AI
            risk_analysis = None
            try:
                if not Config.YANDEX_API_KEY or not Config.YANDEX_FOLDER_ID:
                    logger.warning(f"⚠️ YandexGPT API ключи не настроены. Пропускаем анализ рисков.")
                elif total_changes == 0:
                    logger.info(f"ℹ️ Изменений не обнаружено, анализ AI не требуется")
                else:
                    logger.info(f"🤖 Отправка запроса к YandexGPT для анализа {total_changes} изменений")
                if Config.YANDEX_API_KEY and Config.YANDEX_FOLDER_ID and total_changes > 0:
                    system_prompt = """Ты эксперт по анализу изменений в юридических документах. Проанализируй изменения между двумя версиями документа и оцени риски.

Для каждого изменения определи:
1. Тип изменения (условия оплаты, сроки, ответственность, права сторон, условия расторжения и т.д.)
2. Уровень риска (CRITICAL, HIGH, MEDIUM, LOW, INFO)
3. Влияние на права и обязанности сторон
4. Рекомендации

Верни результат ТОЛЬКО в формате JSON без дополнительного текста с полями:
- summary: краткое резюме изменений
- overall_risk: общий уровень риска изменений (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- key_warnings: массив ключевых предупреждений
- changes_analysis: массив объектов с полями:
  - type: тип изменения
  - risk_level: уровень риска
  - description: описание изменения
  - impact: влияние на стороны
  - recommendation: рекомендация"""
                    
                    user_prompt = f"""ОРИГИНАЛЬНЫЙ ДОКУМЕНТ (первые 2000 символов):
{original_text[:2000]}

ИЗМЕНЕННЫЙ ДОКУМЕНТ (первые 2000 символов):
{modified_text[:2000]}

ВЫЯВЛЕННЫЕ ИЗМЕНЕНИЯ:
{changes_text}

Проанализируй эти изменения и верни JSON с анализом рисков."""
                    
                    data = {
                        "modelUri": f"gpt://{Config.YANDEX_FOLDER_ID}/yandexgpt/latest",
                        "completionOptions": {
                            "stream": False,
                            "temperature": 0.3,
                            "maxTokens": 2000
                        },
                        "messages": [
                            {"role": "system", "text": system_prompt},
                            {"role": "user", "text": user_prompt}
                        ]
                    }
                    
                    headers = {
                        "Authorization": f"Api-Key {Config.YANDEX_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    
                    resp = requests.post(
                        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                        headers=headers,
                        json=data,
                        timeout=30
                    )
                    
                    if resp.status_code == 200:
                        result = resp.json()
                        response_text = result['result']['alternatives'][0]['message']['text'].strip()
                        logger.info(f"✅ Получен ответ от YandexGPT для сравнения {comparison_id}")
                        
                        # Парсим JSON из ответа
                        import re
                        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                        if json_match:
                            risk_analysis = json.loads(json_match.group())
                            logger.info(f"✅ Анализ рисков успешно распарсен для сравнения {comparison_id}")
                        else:
                            # Если не удалось распарсить JSON, создаем простой анализ
                            logger.warning(f"⚠️ Не удалось распарсить JSON ответ от YandexGPT для сравнения {comparison_id}")
                            risk_analysis = {
                                'summary': 'Изменения проанализированы',
                                'overall_risk': 'MEDIUM' if total_changes > 5 else 'LOW',
                                'key_warnings': ['Рекомендуется внимательно изучить все изменения'],
                                'changes_analysis': []
                            }
                    else:
                        logger.warning(f"⚠️ Ошибка YandexGPT при анализе изменений: {resp.status_code} - {resp.text[:200]}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось получить анализ рисков от AI: {e}")
            
            # Сохраняем результаты
            comparison.comparison_result_json = json.dumps({
                'changes': changes,
                'statistics': {
                    'total_changes': total_changes,
                    'added_count': len(changes['added']),
                    'removed_count': len(changes['removed']),
                    'modified_count': len(changes['modified']),
                    'unchanged_count': len(changes['unchanged'])
                },
                'diff': diff[:1000]  # Ограничиваем размер
            }, ensure_ascii=False)
            
            if risk_analysis:
                comparison.risk_analysis_json = json.dumps(risk_analysis, ensure_ascii=False)
            
            # Генерируем HTML отчет
            report_path = DocumentComparator.generate_comparison_report(comparison_id, changes, risk_analysis, 
                                                                         comparison.original_filename, 
                                                                         comparison.modified_filename)
            if report_path:
                comparison.report_path = report_path
            
            comparison.status = 'completed'
            comparison.completed_at = datetime.now().isoformat()
            db.session.commit()
            
            logger.info(f"✅ Сравнение {comparison_id} завершено. Изменений: {total_changes}")
            return comparison.to_dict(), None
            
        except Exception as e:
            logger.error(f"❌ Ошибка сравнения документов {comparison_id}: {e}")
            if comparison:
                comparison.status = 'failed'
                comparison.error_message = str(e)
                db.session.commit()
            return None, str(e)
    
    @staticmethod
    def generate_comparison_report(comparison_id, changes, risk_analysis, original_filename, modified_filename):
        """Генерирует HTML отчет о сравнении"""
        try:
            reports_dir = os.path.join('static', 'reports', 'comparisons')
            os.makedirs(reports_dir, exist_ok=True)
            
            report_filename = f'comparison_{comparison_id}_report.html'
            report_path = os.path.join(reports_dir, report_filename)
            
            html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчет о сравнении документов</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        h1 {{ color: #333; border-bottom: 2px solid #4361ee; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .added {{ background-color: #d4edda; padding: 5px; margin: 5px 0; border-left: 4px solid #28a745; }}
        .removed {{ background-color: #f8d7da; padding: 5px; margin: 5px 0; border-left: 4px solid #dc3545; text-decoration: line-through; }}
        .modified {{ background-color: #fff3cd; padding: 5px; margin: 5px 0; border-left: 4px solid #ffc107; }}
        .statistics {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .risk-high {{ color: #dc3545; font-weight: bold; }}
        .risk-medium {{ color: #ffc107; font-weight: bold; }}
        .risk-low {{ color: #28a745; }}
    </style>
</head>
<body>
    <h1>📊 Отчет о сравнении документов</h1>
    <p><strong>Оригинальный документ:</strong> {original_filename}</p>
    <p><strong>Измененный документ:</strong> {modified_filename}</p>
    <p><strong>Дата сравнения:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="statistics">
        <h2>Статистика изменений</h2>
        <p>Всего изменений: <strong>{len(changes['added']) + len(changes['removed']) + len(changes['modified'])}</strong></p>
        <p>Добавлено: <strong>{len(changes['added'])}</strong> фрагментов</p>
        <p>Удалено: <strong>{len(changes['removed'])}</strong> фрагментов</p>
        <p>Изменено: <strong>{len(changes['modified'])}</strong> фрагментов</p>
    </div>
"""
            
            # Добавляем анализ рисков, если есть
            if risk_analysis:
                html_content += """
    <h2>Анализ рисков изменений</h2>
"""
                if isinstance(risk_analysis, dict):
                    if 'summary' in risk_analysis:
                        html_content += f"<p><strong>Резюме:</strong> {risk_analysis['summary']}</p>"
                    if 'overall_risk' in risk_analysis:
                        risk_class = 'risk-high' if risk_analysis['overall_risk'] in ['CRITICAL', 'HIGH'] else 'risk-medium' if risk_analysis['overall_risk'] == 'MEDIUM' else 'risk-low'
                        html_content += f"<p><strong>Общий уровень риска:</strong> <span class=\"{risk_class}\">{risk_analysis['overall_risk']}</span></p>"
            
            # Добавляем список изменений
            html_content += """
    <h2>Детальные изменения</h2>
"""
            
            if changes['added']:
                html_content += "<h3>Добавленные фрагменты:</h3>"
                for change in changes['added'][:20]:  # Ограничиваем для читаемости
                    html_content += f'<div class="added">+ {change}</div>'
            
            if changes['removed']:
                html_content += "<h3>Удаленные фрагменты:</h3>"
                for change in changes['removed'][:20]:
                    html_content += f'<div class="removed">- {change}</div>'
            
            if changes['modified']:
                html_content += "<h3>Измененные фрагменты:</h3>"
                for change in changes['modified'][:10]:
                    html_content += f'<div class="modified"><strong>Было:</strong> {change.get("original", "")[:200]}<br><strong>Стало:</strong> {change.get("modified", "")[:200]}</div>'
            
            html_content += """
</body>
</html>
"""
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"✅ Отчет о сравнении создан: {report_path}")
            return f'static/reports/comparisons/{report_filename}'
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания отчета: {e}")
            return None
    
    @staticmethod
    def get_user_comparisons(user_id):
        """Получить все сравнения пользователя"""
        try:
            comparisons = DocumentComparison.query.filter_by(user_id=user_id).order_by(
                DocumentComparison.created_at.desc()
            ).all()
            return [c.to_dict() for c in comparisons]
        except Exception as e:
            logger.error(f"❌ Ошибка получения сравнений: {e}")
            return []
    
    @staticmethod
    def get_comparison(comparison_id, user_id):
        """Получить конкретное сравнение"""
        try:
            comparison = DocumentComparison.query.get(comparison_id)
            if not comparison:
                return None, "Сравнение не найдено"
            if comparison.user_id != user_id:
                return None, "Доступ запрещен"
            return comparison.to_dict(), None
        except Exception as e:
            logger.error(f"❌ Ошибка получения сравнения: {e}")
            return None, str(e)

