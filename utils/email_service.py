"""Сервис для отправки email"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
import logging

logger = logging.getLogger(__name__)

def send_email(to_email, subject, html_content, text_content=None):
    """
    Отправляет email через SMTP
    
    Требует переменные окружения:
    - SMTP_HOST (например, smtp.gmail.com)
    - SMTP_PORT (например, 587)
    - SMTP_USER (email отправителя)
    - SMTP_PASSWORD (пароль от email)
    - FROM_EMAIL (email отправителя для отображения)
    """
    try:
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('FROM_EMAIL', smtp_user or 'noreply@docscan-ai.ru')
        
        if not smtp_user or not smtp_password:
            logger.warning("⚠️ SMTP настройки не заданы. Email не будет отправлен.")
            logger.info(f"📧 Письмо НЕ отправлено (для отладки): {to_email}, тема: {subject}")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        # Текстовая версия
        if text_content:
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(part1)
        
        # HTML версия
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part2)
        
        # Отправка
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info(f"✅ Email отправлен: {to_email}, тема: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки email: {e}")
        return False

def send_verification_email(email, verification_token, user_id):
    """Отправляет email для верификации"""
    base_url = os.getenv('BASE_URL', 'https://docscan-ai.ru')
    verification_url = f"{base_url}/verify-email/{verification_token}"
    
    subject = "Подтвердите ваш email - DocScan AI"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #4361ee, #7209b7); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #4361ee; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 DocScan AI</h1>
                <p>Подтверждение регистрации</p>
            </div>
            <div class="content">
                <p>Здравствуйте!</p>
                <p>Благодарим за регистрацию на DocScan AI. Для завершения регистрации и активации аккаунта, пожалуйста, подтвердите ваш email адрес.</p>
                
                <div style="text-align: center;">
                    <a href="{verification_url}" class="button">Подтвердить email</a>
                </div>
                
                <p>Или скопируйте и вставьте эту ссылку в браузер:</p>
                <p style="word-break: break-all; background: white; padding: 10px; border-radius: 5px; font-size: 12px;">{verification_url}</p>
                
                <p>Если вы не регистрировались на DocScan AI, просто проигнорируйте это письмо.</p>
                
                <p>С уважением,<br>Команда DocScan AI</p>
            </div>
            <div class="footer">
                <p>© 2025 DocScan AI. Все права защищены.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    DocScan AI - Подтверждение регистрации
    
    Здравствуйте!
    
    Благодарим за регистрацию на DocScan AI. Для завершения регистрации, пожалуйста, перейдите по ссылке:
    
    {verification_url}
    
    Если вы не регистрировались на DocScan AI, просто проигнорируйте это письмо.
    
    С уважением,
    Команда DocScan AI
    """
    
    return send_email(email, subject, html_content, text_content)

def send_password_reset_email(email, reset_token, user_id):
    """Отправляет email для сброса пароля"""
    base_url = os.getenv('BASE_URL', 'https://docscan-ai.ru')
    reset_url = f"{base_url}/reset-password/{reset_token}"
    
    subject = "Сброс пароля - DocScan AI"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #4361ee, #7209b7); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #4361ee; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 DocScan AI</h1>
                <p>Сброс пароля</p>
            </div>
            <div class="content">
                <p>Здравствуйте!</p>
                <p>Вы запросили сброс пароля для вашего аккаунта на DocScan AI.</p>
                
                <div style="text-align: center;">
                    <a href="{reset_url}" class="button">Сбросить пароль</a>
                </div>
                
                <p>Или скопируйте и вставьте эту ссылку в браузер:</p>
                <p style="word-break: break-all; background: white; padding: 10px; border-radius: 5px; font-size: 12px;">{reset_url}</p>
                
                <div class="warning">
                    <strong>⚠️ Внимание:</strong> Эта ссылка действительна в течение 24 часов. Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.
                </div>
                
                <p>С уважением,<br>Команда DocScan AI</p>
            </div>
            <div class="footer">
                <p>© 2025 DocScan AI. Все права защищены.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    DocScan AI - Сброс пароля
    
    Здравствуйте!
    
    Вы запросили сброс пароля для вашего аккаунта на DocScan AI.
    
    Перейдите по ссылке для сброса пароля:
    {reset_url}
    
    Эта ссылка действительна в течение 24 часов.
    
    Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.
    
    С уважением,
    Команда DocScan AI
    """
    
    return send_email(email, subject, html_content, text_content)


def personalize_email_content(html_content, user_data):
    """
    Персонализирует содержимое письма, заменяя переменные
    
    Доступные переменные:
    - {email} - email пользователя
    - {user_id} - ID пользователя
    - {plan} - тариф пользователя
    - {plan_name} - название тарифа
    """
    replacements = {
        '{email}': user_data.get('email', ''),
        '{user_id}': user_data.get('user_id', ''),
        '{plan}': user_data.get('plan', 'free'),
        '{plan_name}': user_data.get('plan_name', 'Бесплатный')
    }
    
    personalized = html_content
    for placeholder, value in replacements.items():
        personalized = personalized.replace(placeholder, str(value))
    
    return personalized


def send_campaign_email(campaign, recipient, user_manager):
    """
    Отправляет одно письмо из рассылки
    
    Args:
        campaign: объект EmailCampaign
        recipient: словарь с данными получателя (user_id, email, plan)
        user_manager: экземпляр SQLiteUserManager для работы с БД
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    from datetime import datetime
    from config import PLANS
    
    try:
        # Персонализируем содержимое
        user_data = {
            'email': recipient['email'],
            'user_id': recipient.get('user_id', ''),
            'plan': recipient.get('plan', 'free'),
            'plan_name': PLANS.get(recipient.get('plan', 'free'), {}).get('name', 'Бесплатный')
        }
        
        html_content = personalize_email_content(campaign.html_content, user_data)
        text_content = None
        if campaign.text_content:
            text_content = personalize_email_content(campaign.text_content, user_data)
        
        # Отправляем письмо
        success = send_email(
            to_email=recipient['email'],
            subject=campaign.subject,
            html_content=html_content,
            text_content=text_content
        )
        
        # Создаем запись об отправке
        email_send = user_manager.create_email_send(
            campaign_id=campaign.id,
            user_id=recipient.get('user_id'),
            email=recipient['email'],
            status='sent' if success else 'failed'
        )
        
        if not success:
            # Обновляем статус с ошибкой
            user_manager.update_email_send_status(
                email_send_id=email_send.id,
                status='failed',
                error_message='Ошибка отправки email'
            )
            return False, 'Ошибка отправки email'
        
        return True, None
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки письма из рассылки {campaign.id} получателю {recipient.get('email')}: {e}")
        # Создаем запись об ошибке
        try:
            email_send = user_manager.create_email_send(
                campaign_id=campaign.id,
                user_id=recipient.get('user_id'),
                email=recipient.get('email', 'unknown'),
                status='failed'
            )
            user_manager.update_email_send_status(
                email_send_id=email_send.id,
                status='failed',
                error_message=str(e)
            )
        except:
            pass
        
        return False, str(e)


def send_email_campaign(campaign_id, user_manager, batch_size=10, delay_between_batches=1):
    """
    Отправляет email-рассылку получателям
    
    Args:
        campaign_id: ID рассылки
        user_manager: экземпляр SQLiteUserManager
        batch_size: размер батча для отправки (по умолчанию 10 писем за раз)
        delay_between_batches: задержка между батчами в секундах
    
    Returns:
        dict: статистика отправки
    """
    import time
    from datetime import datetime
    
    campaign = user_manager.get_email_campaign(campaign_id)
    if not campaign:
        logger.error(f"❌ Рассылка {campaign_id} не найдена")
        return {'success': False, 'error': 'Рассылка не найдена'}
    
    if campaign.status == 'sent':
        logger.warning(f"⚠️ Рассылка {campaign_id} уже отправлена")
        return {'success': False, 'error': 'Рассылка уже отправлена'}
    
    # Обновляем статус рассылки на "отправляется"
    campaign.status = 'sending'
    user_manager.db.session.commit()
    
    try:
        # Получаем список получателей
        recipients = user_manager.get_recipients_for_campaign(campaign.recipient_filter)
        
        if not recipients:
            campaign.status = 'draft'
            user_manager.db.session.commit()
            logger.warning(f"⚠️ Нет получателей для рассылки {campaign_id}")
            return {'success': False, 'error': 'Нет получателей для рассылки'}
        
        logger.info(f"📧 Начинаем отправку рассылки {campaign.name} ({campaign_id}) получателям: {len(recipients)}")
        
        # Отправляем письма батчами
        sent_count = 0
        failed_count = 0
        
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            
            for recipient in batch:
                success, error = send_campaign_email(campaign, recipient, user_manager)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            
            # Задержка между батчами (чтобы не перегружать SMTP-сервер)
            if i + batch_size < len(recipients):
                time.sleep(delay_between_batches)
        
        # Обновляем статус рассылки на "отправлено"
        campaign.status = 'sent'
        campaign.sent_at = datetime.now().isoformat()
        user_manager.db.session.commit()
        
        logger.info(f"✅ Рассылка {campaign.name} ({campaign_id}) завершена: отправлено {sent_count}, ошибок {failed_count}")
        
        return {
            'success': True,
            'total': len(recipients),
            'sent': sent_count,
            'failed': failed_count
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки рассылки {campaign_id}: {e}")
        campaign.status = 'draft'  # Возвращаем статус в черновик при ошибке
        user_manager.db.session.commit()
        return {'success': False, 'error': str(e)}

