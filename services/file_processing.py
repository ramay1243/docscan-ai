import PyPDF2
import docx
import requests
import tempfile
import os
import base64
import logging
from config import Config

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path):
    """Извлекает текст из PDF файла"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        logger.info(f"✅ Извлечен текст из PDF: {len(text)} символов")
    except Exception as e:
        error_msg = f"Ошибка чтения PDF: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return error_msg
    return text

def extract_text_from_docx(file_path):
    """Извлекает текст из DOCX файла"""
    text = ""
    try:
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        logger.info(f"✅ Извлечен текст из DOCX: {len(text)} символов")
    except Exception as e:
        error_msg = f"Ошибка чтения DOCX: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return error_msg
    return text

def extract_text_from_txt(file_path):
    """Извлекает текст из TXT файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        logger.info(f"✅ Извлечен текст из TXT: {len(text)} символов")
        return text
    except Exception as e:
        error_msg = f"Ошибка чтения TXT: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return error_msg

def extract_text_from_image(file_path):
    """Извлекает текст с фото через Yandex Vision API"""
    # Проверяем наличие API ключей
    if not Config.YANDEX_API_KEY or not Config.YANDEX_FOLDER_ID:
        error_msg = "❌ API ключи Yandex Cloud не настроены"
        logger.error(error_msg)
        return error_msg
    
    try:
        logger.info("🖼️ Начинаем распознавание фото...")
        
        # Кодируем изображение в base64
        with open(file_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        headers = {
            "Authorization": f"Api-Key {Config.YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "folderId": Config.YANDEX_FOLDER_ID,
            "analyzeSpecs": [{
                "content": image_data,
                 "features": [{
                    "type": "TEXT_DETECTION",
                    "text_detection_config": {
                        "language_codes": ["ru", "en"],
                        "model": "page"
                    }
                }]
            }]
        }
        
        response = requests.post(
            "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze",
            headers=headers,
            json=data,
            timeout=30
        )
        
        logger.info(f"📊 Ответ Vision API: статус {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Проверяем наличие textDetection в ответе
            if ('results' in result and len(result['results']) > 0 and
                'results' in result['results'][0] and len(result['results'][0]['results']) > 0 and
                'textDetection' in result['results'][0]['results'][0]):
                
                # Извлекаем весь распознанный текст
                text_blocks = []
                for page in result['results'][0]['results'][0]['textDetection']['pages']:
                    for block in page['blocks']:
                        for line in block['lines']:
                            line_text = ' '.join([word['text'] for word in line['words']])
                            text_blocks.append(line_text)
                
                recognized_text = '\n'.join(text_blocks)
                logger.info(f"✅ Распознано {len(recognized_text)} символов с фото")
                return recognized_text
            else:
                error_msg = "❌ В ответе API нет textDetection"
                logger.error(error_msg)
                return error_msg
        else:
            error_msg = f"❌ Ошибка Vision API: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return error_msg
            
    except Exception as e:
        error_msg = f"❌ Ошибка распознавания: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return error_msg

def extract_text_from_file(file_path, filename):
    """Основная функция извлечения текста из файла"""
    filename_lower = filename.lower()
    
    if filename_lower.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif filename_lower.endswith('.docx'):
        return extract_text_from_docx(file_path)
    elif filename_lower.endswith('.txt'):
        return extract_text_from_txt(file_path)
    elif filename_lower.endswith(('.jpg', '.jpeg', '.png', '.webp')):
        return extract_text_from_image(file_path)
    else:
        error_msg = "Неподдерживаемый формат файла"
        logger.error(f"❌ {error_msg}")
        return error_msg

def validate_file(file):
    """Проверяет файл перед обработкой"""
    if not file or file.filename == '':
        return False, "Файл не выбран"
    
    # Проверка типа файла
    valid_extensions = ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.webp']
    if not any(file.filename.lower().endswith(ext) for ext in valid_extensions):
        return False, "Неподдерживаемый формат файла. Используйте PDF, DOCX, TXT, JPG, PNG"
    
    # Проверка размера (10MB)
    if file.size > 10 * 1024 * 1024:
        return False, "Файл слишком большой. Максимальный размер: 10MB"
    
    return True, "Файл валиден"
