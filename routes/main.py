from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from utils.logger import RussianLogger
import logging
from flask import send_file

logger = logging.getLogger(__name__)

# Создаем Blueprint для главных маршрутов
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Главная страница с интерфейсом"""
    return '''
<!DOCTYPE html>
<html lang="ru"> 
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Улучшенный заголовок -->
    <title>DocScan AI: Проверка договоров онлайн бесплатно с ИИ | Анализ документов за 60 секунд</title>
    
    <!-- Оптимизированное описание -->
    <meta name="description" content="Проверка документов онлайн бесплатно с ИИ. Проверка договоров онлайн, анализ документов за 60 секунд. Автоматическая проверка документов, договоров, справок на риски. Попробуйте сейчас без регистрации!">
    
    <!-- Расширенные ключевые слова -->
    <meta name="keywords" content="проверка документов онлайн, проверка документов онлайн бесплатно, проверка договоров онлайн, анализ документов ИИ, бесплатная проверка договоров, автоматическая проверка документов, проверка документов с ИИ, проверка документов в электронном виде, проверка документов бесплатно, проверка документов на подлинность, нейросеть для проверки документов, проверка договоров аренды, анализ договора с искусственным интеллектом, проверка юридических рисков, расшифровка документов, проверка договоров бесплатно, ИИ для анализа договоров">
    
    <!-- Canonical URL -->
    <link rel="canonical" href="https://docscan-ai.ru">
    
    <!-- Open Graph -->
    <meta property="og:title" content="Проверка договоров онлайн бесплатно: 1 анализ | DocScan AI">
    <meta property="og:description" content="Анализируйте договоры с ИИ за 60 секунд. Находите скрытые юридические риски. Первый анализ — бесплатно после регистрации!">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://docscan-ai.ru">
    <meta property="og:image" content="https://docscan-ai.ru/static/og-main.jpg">
    <meta property="og:locale" content="ru_RU">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="1 анализ договоров бесплатно | DocScan AI">
    <meta name="twitter:description" content="Проверьте договор с ИИ за 60 секунд. Анализ юридических рисков онлайн.">
    
    <!-- Favicon -->
    <link rel="icon" href="/static/favicon.ico" type="image/x-icon">
    
    <!-- Preconnect для шрифтов -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary: #4361ee;
            --primary-dark: #3a56d4;
            --secondary: #7209b7;
            --accent: #f72585;
            --success: #4cc9f0;
            --warning: #f8961e;
            --danger: #f94144;
            --light: #f8f9fa;
            --dark: #212529;
            --gray: #6c757d;
            --border: #e9ecef;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: var(--dark);
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        /* Header */
        .main-header {
            background: white;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
            text-decoration: none;
        }
        
        .logo-icon {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }
        
        .nav-links {
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .nav-link {
            color: var(--gray);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
            position: relative;
            font-size: 0.9rem;
            white-space: nowrap;
        }
        
        .nav-link:hover {
            color: var(--primary);
        }
        
        .nav-link.active {
            color: var(--primary);
        }
        
        .nav-link.active::after {
            content: '';
            position: absolute;
            bottom: -5px;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--primary);
            border-radius: 2px;
        }
        
        .cta-button {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            padding: 10px 20px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 15px rgba(67, 97, 238, 0.3);
            font-size: 0.85rem;
        }
        
        .cta-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(67, 97, 238, 0.4);
        }
        
        /* Hero Section */
        .hero-section {
            padding: 80px 0;
            background: white;
            border-radius: 0 0 30px 30px;
            margin-bottom: 40px;
            position: relative;
            overflow: hidden;
        }
        
        .hero-content {
            max-width: 800px;
            text-align: center;
            margin: 0 auto;
            position: relative;
            z-index: 2;
        }
        
        .hero-badge {
            display: inline-block;
            background: linear-gradient(135deg, var(--success), #4cc9f0);
            color: white;
            padding: 8px 20px;
            border-radius: 50px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 20px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }
        
        .hero-title {
            font-size: 3.5rem;
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 20px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .hero-subtitle {
            font-size: 1.2rem;
            color: var(--gray);
            margin-bottom: 40px;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        
        /* Upload Section */
        .upload-section {
            background: white;
            padding: 60px;
            border-radius: 30px;
            margin: 40px 0;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
        }
        
        .upload-zone {
            border: 3px dashed var(--border);
            border-radius: 20px;
            padding: 60px;
            text-align: center;
            margin: 30px 0;
            transition: all 0.3s ease;
            background: var(--light);
            cursor: pointer;
        }
        
        .upload-zone:hover {
            border-color: var(--primary);
            background: rgba(67, 97, 238, 0.05);
        }
        
        .upload-icon {
            font-size: 4rem;
            margin-bottom: 20px;
            color: var(--primary);
        }
        
        .file-info {
            background: var(--light);
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            display: none;
            border-left: 4px solid var(--primary);
        }
        
        .user-info {
            background: var(--light);
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            text-align: center;
            border: 2px solid var(--border);
        }
        
        /* Loading */
        .loading {
            display: none;
            text-align: center;
            margin: 40px 0;
        }
        
        .spinner {
            border: 4px solid var(--border);
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Result Section */
        .result {
            background: white;
            border-radius: 20px;
            padding: 40px;
            margin-top: 40px;
            display: none;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
        }
        
        /* Risk Badges */
        .risk-badge {
            display: inline-block;
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin: 3px;
        }
        
        .risk-critical { background: #fed7d7; color: #c53030; }
        .risk-high { background: #feebc8; color: #dd6b20; }
        .risk-medium { background: #fefcbf; color: #d69e2e; }
        .risk-low { background: #c6f6d5; color: #38a169; }
        .risk-info { background: #bee3f8; color: #3182ce; }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin: 40px 0;
        }
        
        .stat-card {
            background: var(--light);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            border: 2px solid var(--border);
            transition: transform 0.3s, border-color 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            border-color: var(--primary);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary);
            display: block;
            margin-bottom: 5px;
        }
        
        /* Features */
        .section-title {
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 60px;
            color: var(--dark);
        }
        
        .section-subtitle {
            text-align: center;
            color: var(--gray);
            font-size: 1.1rem;
            max-width: 700px;
            margin: 0 auto 40px;
        }
        
        /* Центрирование заголовков секций */
        .container h2 {
            text-align: center;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin: 40px 0;
        }
        
        .feature-card {
            background: white;
            padding: 35px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            transition: transform 0.3s, box-shadow 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .feature-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 60px rgba(0,0,0,0.12);
        }
        
        .feature-icon {
            width: 60px;
            height: 60px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 20px;
        }
        
        .feature-icon.upload { background: linear-gradient(135deg, #4361ee, #3a56d4); color: white; }
        .feature-icon.ai { background: linear-gradient(135deg, #4cc9f0, #3aa8d4); color: white; }
        .feature-icon.results { background: linear-gradient(135deg, #f8961e, #e0871a); color: white; }
        .feature-icon.security { background: linear-gradient(135deg, #7209b7, #6409a5); color: white; }
        
        /* Process Steps */
        .process-steps {
            display: flex;
            justify-content: space-between;
            margin: 60px 0;
            position: relative;
        }
        
        .process-steps::before {
            content: '';
            position: absolute;
            top: 40px;
            left: 10%;
            right: 10%;
            height: 2px;
            background: var(--border);
            z-index: 1;
        }
        
        .step {
            flex: 1;
            text-align: center;
            position: relative;
            z-index: 2;
            padding: 0 15px;
        }
        
        .step-number {
            width: 80px;
            height: 80px;
            background: white;
            border: 3px solid var(--primary);
            color: var(--primary);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            font-weight: 700;
            margin: 0 auto 20px;
            position: relative;
        }
        
        /* Pricing */
        .pricing-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
            margin: 40px 0;
        }
        
        .pricing-card {
            background: white;
            padding: 40px 30px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            border: 2px solid var(--border);
            transition: transform 0.3s;
        }
        
        .pricing-card:hover {
            transform: translateY(-10px);
        }
        
        .pricing-card.featured {
            border-color: var(--primary);
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
        }
        
        .pricing-card.featured .price {
            color: white;
        }
        
        .plan-name {
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 15px;
        }
        
        .price {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 20px;
            color: var(--primary);
        }
        
        .features {
            list-style: none;
            margin-bottom: 30px;
            text-align: left;
        }
        
        .features li {
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
        }
        
        .features li:last-child {
            border-bottom: none;
        }
        
        /* FAQ */
        .faq-section {
            margin: 80px 0;
        }
        
        .container.faq-section {
            padding: 0 !important;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .container.faq-section h2 {
            width: 100%;
            text-align: center;
            padding: 0 20px;
        }
        
        .faq-wrapper {
            max-width: 900px;
            margin: 0 auto;
            width: 100%;
            padding: 0 20px;
            box-sizing: border-box;
        }
        
        .faq-item {
            background: white;
            border-radius: 15px;
            margin-bottom: 15px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
        }
        
        .faq-question {
            padding: 25px;
            font-weight: 600;
            font-size: 1.1rem;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: var(--dark);
        }
        
        .faq-answer {
            padding: 0 25px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s, padding 0.3s;
        }
        
        .faq-answer.open {
            padding: 0 25px 25px;
            max-height: 500px;
        }
        
        /* CTA Section */
        .cta-section {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            padding: 80px 0;
            border-radius: 30px;
            text-align: center;
            margin: 80px 0;
            position: relative;
            overflow: hidden;
        }
        
        .cta-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 20px;
        }
        
        /* Footer */
        .main-footer {
            background: var(--dark);
            color: white;
            padding: 60px 0 30px;
            margin-top: 80px;
        }
        
        .footer-content {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 40px;
            margin-bottom: 40px;
        }
        
        .footer-links {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .footer-link {
            color: rgba(255,255,255,0.7);
            text-decoration: none;
            transition: color 0.3s;
        }
        
        .footer-link:hover {
            color: white;
        }
        
        .copyright {
            text-align: center;
            padding-top: 30px;
            border-top: 1px solid rgba(255,255,255,0.1);
            color: rgba(255,255,255,0.5);
        }
        
        /* Document Types Carousel */
        .simple-carousel {
            position: relative;
            max-width: 900px;
            margin: 0 auto;
        }
        
        .carousel-wrapper {
            overflow: hidden;
            border-radius: 15px;
        }
        
        .carousel-items {
            display: flex;
            gap: 20px;
            padding: 10px;
            transition: transform 0.3s ease;
            overflow-x: auto;
            scroll-behavior: smooth;
            -ms-overflow-style: none;
            scrollbar-width: none;
        }
        
        .carousel-items::-webkit-scrollbar {
            display: none;
        }
        
        .carousel-item {
            flex: 0 0 auto;
            width: 200px;
        }
        
        .carousel-card {
            background: white;
            padding: 25px 15px;
            border-radius: 12px;
            text-align: center;
            border-left: 4px solid var(--primary);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            height: 150px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .carousel-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(67, 97, 238, 0.15);
        }
        
        .carousel-icon {
            font-size: 2.5rem;
            margin-bottom: 15px;
        }
        
        .carousel-controls {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 20px;
        }
        
        .carousel-control {
            background: var(--primary);
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            font-size: 1.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .carousel-control:hover {
            background: var(--primary-dark);
            transform: scale(1.1);
        }
        
        /* Burger Menu */
        .burger-menu {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            display: none;
        }
        
        .burger-icon {
            background: white;
            padding: 15px 12px;
            border-radius: 50%;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            cursor: pointer;
            transition: all 0.3s ease;
            width: 50px;
            height: 50px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 4px;
        }
        
        .burger-icon:hover {
            background: var(--primary);
            transform: scale(1.1);
        }
        
        .burger-line {
            width: 20px;
            height: 2px;
            background: var(--dark);
            transition: all 0.3s ease;
        }
        
        .burger-icon:hover .burger-line {
            background: white;
        }
        
        .menu-dropdown {
            display: none;
            position: absolute;
            top: 60px;
            right: 0;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            padding: 15px 0;
            min-width: 200px;
            animation: slideDown 0.3s ease;
        }
        
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .menu-dropdown a {
            display: block;
            padding: 12px 20px;
            text-decoration: none;
            color: var(--dark);
            transition: all 0.2s ease;
            border-bottom: 1px solid var(--border);
        }
        
        .menu-dropdown a:hover {
            background: var(--primary);
            color: white;
        }
        
        .menu-dropdown a:last-child {
            border-bottom: none;
        }
        
        #mobileAuthButtons, #mobileUserMenu {
            border-top: 1px solid var(--border);
            margin-top: 10px;
            padding-top: 10px;
        }
        
        #mobileAuthButtons a, #mobileUserMenu a {
            display: block;
        }
        
        .menu-dropdown.show {
            display: block;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .hero-title { font-size: 2.5rem; }
            .section-title { font-size: 2rem; }
            .process-steps { flex-direction: column; gap: 40px; }
            .process-steps::before { display: none; }
            .nav-links { display: none; }
            .burger-menu { display: block; }
            .upload-zone { padding: 40px 20px; }
            .upload-section { padding: 30px 20px; }
        }
        
        /* Рекламный баннер */
        .ad-banner {
            position: fixed;
            left: 20px;
            bottom: 20px;
            width: 240px;
            max-width: calc(100vw - 40px);
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
            z-index: 9999;
            overflow: hidden;
            transition: transform 0.3s ease, opacity 0.3s ease;
            animation: slideInLeft 0.5s ease-out;
        }
        
        .ad-banner.hidden {
            display: none;
        }
        
        @keyframes slideInLeft {
            from {
                transform: translateX(-100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .ad-banner-close {
            position: absolute;
            top: 8px;
            right: 8px;
            width: 26px;
            height: 26px;
            background: rgba(255, 255, 255, 0.95);
            border: 2px solid rgba(0, 0, 0, 0.2);
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: bold;
            color: #333;
            transition: all 0.3s ease;
            z-index: 10;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            line-height: 1;
        }
        
        .ad-banner-close:hover {
            background: #fff;
            border-color: rgba(0, 0, 0, 0.4);
            color: #000;
            transform: rotate(90deg) scale(1.1);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        }
        
        .ad-banner-link {
            display: block;
            text-decoration: none;
            color: inherit;
            cursor: pointer;
        }
        
        .ad-banner-image {
            width: 100%;
            height: 130px;
            object-fit: cover;
            display: block;
        }
        
        .ad-banner-content {
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .ad-banner-title {
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 6px;
            line-height: 1.3;
        }
        
        .ad-banner-description {
            font-size: 11px;
            opacity: 0.95;
            line-height: 1.4;
        }
        
        .ad-banner-telegram-icon {
            display: inline-block;
            width: 16px;
            height: 16px;
            margin-right: 4px;
            vertical-align: middle;
        }
        
        @media (max-width: 768px) {
            .ad-banner {
                width: 220px;
                left: 10px;
                bottom: 10px;
            }
            
            .ad-banner-image {
                height: 110px;
            }
            
            .ad-banner-content {
                padding: 10px;
            }
            
            .ad-banner-title {
                font-size: 12px;
            }
            
            .ad-banner-description {
                font-size: 10px;
            }
        }
    </style>
    
    <!-- Yandex.RTB -->
    <script>window.yaContextCb=window.yaContextCb||[]</script>
    <script src="https://yandex.ru/ads/system/context.js" async></script>
</head>
<body>
    <!-- Header -->
    <header class="main-header">
        <div class="container">
            <div class="header-content">
                <a href="/" class="logo">
                    <div class="logo-icon">🤖</div>
                    DocScan AI
                </a>
                
                <nav class="nav-links">
                    <a href="/" class="nav-link active">Главная</a>
                    <a href="/analiz-dokumentov" class="nav-link">Анализ документов</a>
                    <a href="/calculator-penalty" class="nav-link">Калькулятор</a>
                    <a href="/mobile-app" class="nav-link">Мобильное приложение</a>
                    <a href="/articles" class="nav-link">Статьи</a>
                    <a href="/faq" class="nav-link">FAQ</a>
                    <a href="/contact" class="nav-link">Контакты</a>
                    <span id="authButtons" style="display: flex; gap: 10px; align-items: center;">
                        <a href="/login" class="nav-link">Войти</a>
                        <a href="/register" class="cta-button">Регистрация</a>
                    </span>
                    <span id="userMenu" style="display: none; gap: 10px; align-items: center;">
                        <a href="/cabinet" class="nav-link">Личный кабинет</a>
                        <a href="/logout" class="cta-button">Выход</a>
                    </span>
                </nav>
                
            </div>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="hero-section">
        <div class="container">
            <div class="hero-content">
                <span class="hero-badge">🤖 Искусственный интеллект</span>
                <h1>Проверка договоров онлайн бесплатно с ИИ за 60 секунд</h1>
                <p class="hero-subtitle">
                    Проверяйте договоры, контракты и юридические документы на риски с помощью искусственного интеллекта. 
                    Находите скрытые проблемы до того, как они станут дорогостоящими ошибками.
                </p>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <span class="stat-number">60</span>
                        <span>секунд на анализ</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">99%</span>
                        <span>точность проверки</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">25+</span>
                        <span>типов документов</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">50+</span>
                        <span>параметров риска</span>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <!-- Yandex.RTB R-A-18680294-1 -->
    <div style="text-align: center; margin: 30px auto; max-width: 1200px; padding: 0 20px;">
        <div id="yandex_rtb_R-A-18680294-1"></div>
        <script>
        window.yaContextCb.push(() => {
            Ya.Context.AdvManager.render({
                "blockId": "R-A-18680294-1",
                "renderTo": "yandex_rtb_R-A-18680294-1"
            })
        })
        </script>
    </div>
    
    <!-- Интерактивный демо-анализ -->
    <section class="container">
        <div style="text-align: center; margin: 40px auto; padding: 30px; background: linear-gradient(135deg, #f0f7ff 0%, #e3f2fd 100%); border-radius: 15px; max-width: 1000px;">
            <h3 style="color: var(--primary); margin-bottom: 20px; font-size: 1.8rem;">🎯 Посмотрите, как работает анализ</h3>
            <p style="margin-bottom: 25px; color: #555; max-width: 700px; margin-left: auto; margin-right: auto; font-size: 1.1rem; line-height: 1.6;">
                Нажмите кнопку ниже, чтобы увидеть пример анализа типичного договора аренды. Без загрузки файлов.
            </p>
            
            <!-- ОДНА кнопка здесь -->
            <button onclick="showDemoAnalysis()" 
                    id="demoButton"
                    style="background: var(--primary); color: white; border: none; padding: 15px 40px; border-radius: 10px; cursor: pointer; font-size: 1.1rem; font-weight: 600; display: inline-flex; align-items: center; gap: 10px; margin-bottom: 20px;">
                <span>▶️</span> Показать демо-анализ
            </button>
            
            <div id="demoAnalysisResult" style="display: none; margin-top: 30px; text-align: left;">
                <div style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.08);">
                    <h4 style="color: var(--primary); margin-bottom: 25px; border-bottom: 2px solid #f0f7ff; padding-bottom: 15px; font-size: 1.5rem;">📄 Анализ договора аренды помещения</h4>
                    
                    <div style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 30px; justify-content: center;">
                        <!-- Колонка 1: Безопасные -->
                        <div style="flex: 1; min-width: 300px; background: #e8f5e9; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50;">
                            <h5 style="color: #2E7D32; margin-bottom: 15px; font-size: 1.2rem; display: flex; align-items: center; gap: 8px;">
                                <span>✅</span> Безопасные пункты
                            </h5>
                            <ul style="margin: 0; padding-left: 20px; font-size: 1rem; line-height: 1.7;">
                                <li style="margin-bottom: 10px;"><strong>Пункт 2.1:</strong> Четкие сроки действия договора</li>
                                <li style="margin-bottom: 10px;"><strong>Пункт 3.2:</strong> Определенная сумма арендной платы</li>
                                <li><strong>Пункт 4.3:</strong> Права и обязанности сторон</li>
                            </ul>
                        </div>
                        
                        <!-- Колонка 2: Внимание -->
                        <div style="flex: 1; min-width: 300px; background: #fff3e0; padding: 20px; border-radius: 10px; border-left: 5px solid #FF9800;">
                            <h5 style="color: #EF6C00; margin-bottom: 15px; font-size: 1.2rem; display: flex; align-items: center; gap: 8px;">
                                <span>⚠️</span> Требуют внимания
                            </h5>
                            <ul style="margin: 0; padding-left: 20px; font-size: 1rem; line-height: 1.7;">
                                <li style="margin-bottom: 10px;"><strong>Пункт 5.1:</strong> Нечеткая процедура оплаты</li>
                                <li><strong>Пункт 6.3:</strong> Расплывчатые условия расторжения</li>
                            </ul>
                        </div>
                        
                        <!-- Колонка 3: Опасные -->
                        <div style="flex: 1; min-width: 300px; background: #ffebee; padding: 20px; border-radius: 10px; border-left: 5px solid #F44336;">
                            <h5 style="color: #C62828; margin-bottom: 15px; font-size: 1.2rem; display: flex; align-items: center; gap: 8px;">
                                <span>❌</span> Опасные пункты
                            </h5>
                            <ul style="margin: 0; padding-left: 20px; font-size: 1rem; line-height: 1.7;">
                                <li style="margin-bottom: 10px;"><strong>Пункт 7.2:</strong> Одностороннее изменение условий арендодателем</li>
                                <li><strong>Пункт 8.4:</strong> Отсутствие ответственности за скрытые дефекты помещения</li>
                            </ul>
                        </div>
                    </div>
                    
                    <!-- Рекомендация -->
                    <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin-top: 20px;">
                        <p style="margin: 0; color: #666; font-size: 1.05rem; line-height: 1.6;">
                            <strong style="color: var(--primary);">💡 Рекомендация:</strong> Перед подписанием договора обсудите пункты 7.2 и 8.4 с арендодателем. 
                            Уточните процедуру оплаты в пункте 5.1.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <script>
    function showDemoAnalysis() {
        const demoResult = document.getElementById('demoAnalysisResult');
        const button = document.getElementById('demoButton');
        
        if (demoResult.style.display === 'none' || !demoResult.style.display) {
            demoResult.style.display = 'block';
            demoResult.style.opacity = '0';
            demoResult.style.transition = 'opacity 0.5s';
            setTimeout(() => { demoResult.style.opacity = '1'; }, 10);
            
            button.innerHTML = '<span>▼</span> Скрыть демо-анализ';
            demoResult.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            demoResult.style.display = 'none';
            button.innerHTML = '<span>▶️</span> Показать демо-анализ';
        }
    }
    </script>

    <!-- Upload Section -->
    <section class="upload-section" id="upload">
        <div class="container">
            <div class="user-info" id="userInfo">
                <div style="display: flex; justify-content: center; gap: 30px; margin-bottom: 20px; flex-wrap: wrap;">
                    <div id="userIdBlock" style="display: none;">
                        <strong>👤 Ваш ID:</strong> <span id="userId">Загрузка...</span>
                    </div>
                    <div>
                        <strong>📊 Анализов сегодня:</strong> <span id="usageInfo">0/1</span>
                    </div>
                </div>
                <div id="copyIdButton" style="display: none;">
                    <button onclick="copyUserId()" class="cta-button" style="padding: 8px 20px; font-size: 0.9rem; margin: 5px;">
                        📋 Копировать ID
                    </button>
                </div>
            </div>
            
            <div class="upload-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
                <div class="upload-icon">📄</div>
                <p><strong>Нажмите чтобы выбрать документ</strong></p>
                <p style="color: var(--gray); margin-top: 15px;">
                    PDF, DOCX, TXT 
                    <span style="color: var(--danger); font-weight: bold;">• ФОТО (только для платных тарифов)</span>
                    (до 10MB)
                </p>
            </div>

            <input type="file" id="fileInput" style="display: none;" accept=".pdf,.docx,.txt,.jpg,.jpeg,.png,.webp" onchange="handleFileSelect(event)">
            
            <div class="file-info" id="fileInfo">
                <strong>Выбран файл:</strong> <span id="fileName"></span>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <button class="cta-button" id="analyzeBtn" onclick="analyzeDocument()" disabled style="padding: 16px 40px; font-size: 1.1rem;">
                    🤖 Начать анализ
                </button>
            </div>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Анализируем документ...</p>
            </div>

            <div class="result" id="result">
                <h3 style="color: var(--primary); margin-bottom: 20px;">✅ Анализ завершен</h3>
                <div id="resultContent"></div>
            </div>
        </div>
    </section>
    <!-- SEO текст для продвижения -->
    <section class="container">
        <div class="seo-text" style="max-width: 800px; margin: 0 auto 50px; padding: 30px; background: var(--card-bg); border-radius: 20px; box-shadow: var(--shadow);">
            <h2 style="color: var(--primary); margin-bottom: 20px; font-size: 1.8rem;">Проверка документов онлайн бесплатно с искусственным интеллектом</h2>
            <p style="font-size: 1.1rem; line-height: 1.6; margin-bottom: 20px;">Сервис <strong>DocScan AI</strong> предлагает <strong>проверку документов онлайн бесплатно</strong> с помощью искусственного интеллекта. Наша система автоматически проверяет документы, договоры, справки на юридические, финансовые и операционные риски за 60 секунд.</p>
            
            <h3 style="color: var(--dark); margin: 25px 0 15px; font-size: 1.4rem;">Проверка документов онлайн бесплатно</h3>
            <p style="font-size: 1.1rem; line-height: 1.6; margin-bottom: 20px;">Получите <strong>1 бесплатный анализ документов</strong> после регистрации. <strong>Проверка документов онлайн</strong> доступна 24/7. Проверьте договор аренды, трудовой договор, договор поставки или любой другой документ. Для профессионального использования доступен тариф с неограниченным количеством проверок.</p>
            
            <h3 style="color: var(--dark); margin: 25px 0 15px; font-size: 1.4rem;">Ключевые возможности проверки документов:</h3>
            <ul style="font-size: 1.1rem; line-height: 1.8; padding-left: 20px;">
                <li><strong>Проверка документов онлайн</strong> - работает 24/7, без регистрации</li>
                <li><strong>Автоматическая проверка документов</strong> - ИИ анализирует весь документ</li>
                <li><strong>Проверка договоров онлайн</strong> - договоры аренды, трудовые, ГПХ, поставки</li>
                <li><strong>Анализ юридических рисков</strong> - выявление опасных пунктов</li>
                <li><strong>Финансовый аудит</strong> - проверка расчетов и условий оплаты</li>
                <li><strong>Проверка документов в электронном виде</strong> - PDF, DOCX, TXT</li>
                <li><strong>Проверка документов бесплатно</strong> - 1 анализ после регистрации</li>
                <li><strong>Распознавание фото документов</strong> на платных тарифах</li>
            </ul>
            
            <div style="margin-top: 30px; padding: 20px; background: rgba(0, 123, 255, 0.1); border-radius: 10px; border-left: 4px solid var(--primary);">
                <p style="margin: 0; font-size: 1.1rem;"><strong>Популярные запросы:</strong> проверка документов онлайн, проверка документов онлайн бесплатно, проверка договоров онлайн, автоматическая проверка документов, проверка документов с ИИ, проверка документов в электронном виде, проверка документов бесплатно, анализ договора аренды, проверка трудового договора, юридическая проверка документов, ИИ анализ договоров.</p>
            </div>
            
            <div style="margin-top: 25px; text-align: center;">
                <a href="/proverka-dokumentov-onlayn" style="display: inline-block; background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; padding: 14px 28px; border-radius: 50px; text-decoration: none; font-weight: 600; font-size: 1.05rem; transition: all 0.3s; box-shadow: 0 4px 15px rgba(67, 97, 238, 0.3);" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 25px rgba(67, 97, 238, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(67, 97, 238, 0.3)'">
                    📄 Узнать больше о проверке документов онлайн
                </a>
            </div>
        </div>
    </section>

    <!-- How It Works -->
    <section class="container">
        <h2>Как это работает?</h2>
        
        <div class="process-steps">
            <div class="step">
                <div class="step-number">1</div>
                <h3>Загрузите документ</h3>
                <p>Загрузите договор в формате PDF, Word или текстовый файл</p>
            </div>
            
            <div class="step">
                <div class="step-number">2</div>
                <h3>ИИ анализирует риски</h3>
                <p>Искусственный интеллект проверяет каждую строку на потенциальные риски</p>
            </div>
            
            <div class="step">
                <div class="step-number">3</div>
                <h3>Получите отчет</h3>
                <p>Детальный анализ с рекомендациями по исправлению. Все за 60 секунд</p>
            </div>
        </div>
    </section>

    <!-- Features -->
    <section class="container">
        <h2>Почему DocScan AI?</h2>
        
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon upload">📄</div>
                <h3>Простая загрузка</h3>
                <p>Загружайте документы в любом формате: PDF, DOCX, TXT или даже фото. Поддержка до 10MB</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon ai">🤖</div>
                <h3>Мощный ИИ-анализ</h3>
                <p>Искусственный интеллект анализирует текст по 50+ параметрам риска</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon results">📊</div>
                <h3>Понятные результаты</h3>
                <p>Детальный отчет с цветовой индикацией рисков и конкретными рекомендациями</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon security">🔒</div>
                <h3>Полная конфиденциальность</h3>
                <p>Документы автоматически удаляются после анализа. Мы не храним ваши файлы</p>
            </div>
        </div>
    </section>

    <!-- Document Types -->
    <div style="background: var(--light); padding: 60px 0;">
        <div class="container">
            <h2>Какие документы можно проверить?</h2>
            
            <div class="simple-carousel">
                <div class="carousel-wrapper">
                    <div class="carousel-items" id="carouselItems"></div>
                </div>
                <div class="carousel-controls">
                    <button class="carousel-control prev" onclick="scrollCarousel(-300)">‹</button>
                    <button class="carousel-control next" onclick="scrollCarousel(300)">›</button>
                </div>
            </div>
            
            <p style="text-align: center; margin-top: 30px; color: var(--gray); font-size: 1.1rem;">
                <strong>И любые другие текстовые документы!</strong> ИИ анализирует суть, а не формат.
            </p>
        </div>
    </div>

    <!-- Pricing -->
    <section class="container">
        <h2>Выберите тариф</h2>
        <p class="section-subtitle">
            Начните с бесплатного анализа, переходите на платные тарифы по мере роста потребностей
        </p>
        
        <div class="pricing-grid">
            <div class="pricing-card">
                <div class="plan-name" style="color: var(--danger);">Бесплатный</div>
                <div class="price" style="color: var(--danger);">0₽</div>
                <ul class="features">
                    <li>✅ 1 анализ бесплатно (после регистрации)</li>
                    <li>✅ Базовый AI-анализ</li>
                    <li>✅ Основные форматы файлов</li>
                    <li>✅ PDF, DOCX, TXT</li>
                </ul>
                <button class="cta-button" disabled style="background: var(--danger);">Текущий тариф</button>
            </div>
            
            <div class="pricing-card featured">
                <div class="plan-name">Базовый</div>
                <div class="price">490₽/мес</div>
                <ul class="features">
                    <li>🚀 Неограниченное количество анализов</li>
                    <li>🚀 Приоритетный AI-анализ</li>
                    <li>🚀 Быстрая обработка</li>
                    <li>📸 Распознавание фото документов</li>
                    <li>⚡ Приоритетная поддержка</li>
                </ul>
                <button class="cta-button" onclick="buyPlan('basic')" style="background: white; color: var(--primary);">Купить за 490₽</button>
            </div>
            
    </section>

    <!-- FAQ -->
    <section class="container faq-section">
        <h2>Частые вопросы</h2>
        
        <div class="faq-wrapper">
        <div class="faq-item">
            <div class="faq-question" onclick="toggleFAQ(1)">
                <span>🤔 Какой максимальный размер файла?</span>
                <span>+</span>
            </div>
            <div class="faq-answer" id="faq-1">
                <p>Максимальный размер файла - 10MB. Поддерживаются форматы: PDF, DOCX, TXT.</p>
            </div>
        </div>
        
        <div class="faq-item">
            <div class="faq-question" onclick="toggleFAQ(2)">
                <span>💰 Сколько стоит анализ?</span>
                <span>+</span>
            </div>
            <div class="faq-answer" id="faq-2">
                <p>1 анализ бесплатно (для зарегистрированных пользователей). Платные тарифы: Базовый (Неограниченное количество анализов) - 490₽/мес.</p>
            </div>
        </div>
        
        <div class="faq-item">
            <div class="faq-question" onclick="toggleFAQ(3)">
                <span>🔒 Конфиденциальны ли мои документы?</span>
                <span>+</span>
            </div>
            <div class="faq-answer" id="faq-3">
                <p>Да! Документы не сохраняются на наших серверах. После анализа файлы автоматически удаляются. Текст передается по защищенному соединению.</p>
            </div>
        </div>
        
        <div class="faq-item">
            <div class="faq-question" onclick="toggleFAQ(4)">
                <span>⏱️ Сколько времени занимает анализ?</span>
                <span>+</span>
            </div>
            <div class="faq-answer" id="faq-4">
                <p>Обычно анализ занимает 30-60 секунд. Скорость зависит от размера документа и загрузки сервера.</p>
            </div>
        </div>
        
        <div class="faq-item">
            <div class="faq-question" onclick="toggleFAQ(5)">
                <span>🤖 Насколько точен AI-анализ?</span>
                <span>+</span>
            </div>
            <div class="faq-answer" id="faq-5">
                <p>ИИ хорошо справляется с выявлением типовых рисков в договорах. Однако это инструмент для первичной проверки - для важных документов рекомендуем консультацию с юристом.</p>
            </div>
        </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
        <div class="container">
            <h2 class="cta-title">Начните анализ документов прямо сейчас</h2>
                <p style="font-size: 1.2rem; opacity: 0.9; max-width: 600px; margin: 0 auto 40px;">
                Загрузите документ и получите анализ рисков через 60 секунд. 
                1 анализ бесплатно после регистрации.
            </p>
            <a href="#upload" class="cta-button" style="background: white; color: var(--primary); padding: 18px 50px; font-size: 1.2rem;">
                🚀 Начать бесплатный анализ
            </a>
        </div>
    </section>

    <!-- Burger Menu (Mobile) -->
    <div class="burger-menu">
        <div class="burger-icon" onclick="toggleMenu()">
            <div class="burger-line"></div>
            <div class="burger-line"></div>
            <div class="burger-line"></div>
        </div>
        <div class="menu-dropdown" id="menuDropdown">
            <a href="/">🏠 Главная</a>
            <a href="/analiz-dokumentov">📄 Анализ документов</a>
            <a href="/calculator-penalty">🧮 Калькулятор</a>
            <a href="/mobile-app">📱 Приложение</a>
            <a href="/articles">📚 Статьи</a>
            <a href="/faq">❓ FAQ</a>
            <a href="/contact">📞 Контакты</a>
            <div id="mobileAuthButtons">
                <a href="/login">🔐 Войти</a>
                <a href="/register" style="background: var(--primary); color: white; font-weight: 600;">📝 Регистрация</a>
            </div>
            <div id="mobileUserMenu" style="display: none;">
                <a href="/cabinet">👤 Личный кабинет</a>
                <a href="/logout" style="color: var(--danger);">🚪 Выход</a>
            </div>
            <a href="https://t.me/docscan_ai" target="_blank">📢 Telegram</a>
        </div>
    </div>

    <!-- Footer -->
    <footer class="main-footer">
        <div class="container">
            <div class="footer-content">
                <div>
                    <a href="/" class="logo" style="color: white; margin-bottom: 20px;">
                        <div class="logo-icon">🤖</div>
                        DocScan AI
                    </a>
                    <p style="opacity: 0.7; max-width: 300px;">
                        Проверка документов онлайн бесплатно с ИИ. Автоматическая проверка документов и договоров с искусственным интеллектом за 60 секунд.
                    </p>
                </div>
                
                <div>
                    <h4 style="margin-bottom: 20px;">Сервисы</h4>
                    <div class="footer-links">
                        <a href="/proverka-dokumentov-onlayn" class="footer-link">Проверка документов онлайн</a>
                        <a href="/analiz-dokumentov" class="footer-link">Анализ документов</a>
                        <a href="/proverka-dogovorov" class="footer-link">Проверка договоров</a>
                        <a href="/articles" class="footer-link">База знаний</a>
                        <a href="/calculator-penalty" class="footer-link">Калькулятор неустойки</a>
                        <a href="/mobile-app" class="footer-link">📱 Приложение</a>
                        <a href="/contact" class="footer-link">Техподдержка</a>
                        <a href="/faq" class="footer-link">FAQ</a>
                    </div>
                </div>
                
                <div>
                    <h4 style="margin-bottom: 20px;">Документы</h4>
                    <div class="footer-links">
                        <a href="/terms" class="footer-link">Пользовательское соглашение</a>
                        <a href="/privacy" class="footer-link">Политика конфиденциальности</a>
                        <a href="/offer" class="footer-link">Публичная оферта</a>
                    </div>
                </div>
                
                <div>
                    <h4 style="margin-bottom: 20px;">Контакты</h4>
                    <div class="footer-links">
                        <a href="mailto:docscanhelp@gmail.com" class="footer-link">docscanhelp@gmail.com</a>
                        <a href="https://t.me/docscan_ai" class="footer-link">Telegram: @docscan_ai</a>
                    </div>
                </div>
            </div>
            
            <div class="copyright">
                © 2025 DocScan AI. Все права защищены.
            </div>
        </div>
    </footer>

    <script>
        let selectedFile = null;
        let currentUserId = null;
        
        // Document types for carousel
        const documentTypes = [
            { icon: '📝', name: 'Договоры аренды' },
            { icon: '💼', name: 'Трудовые контракты' },
            { icon: '🏠', name: 'Договоры купли-продажи' },
            { icon: '⚖️', name: 'Юридические соглашения' },
            { icon: '📊', name: 'Коммерческие предложения' },
            { icon: '📑', name: 'Деловая переписка' },
            { icon: '📋', name: 'Публичные оферты' },
            { icon: '🔧', name: 'Технические задания' }
        ];
        
        // Initialize carousel
        function initCarousel() {
            const container = document.getElementById('carouselItems');
            documentTypes.forEach(doc => {
                const item = document.createElement('div');
                item.className = 'carousel-item';
                item.innerHTML = `
                    <div class="carousel-card">
                        <div class="carousel-icon">${doc.icon}</div>
                        <h4>${doc.name}</h4>
                    </div>
                `;
                container.appendChild(item);
            });
        }
        
        // Scroll carousel
        function scrollCarousel(distance) {
            const container = document.getElementById('carouselItems');
            container.scrollLeft += distance;
        }
        
        // НОВАЯ ЛОГИКА: Получаем user_id только из сессии (для зарегистрированных)
        // Для незарегистрированных user_id не используется
        async function loadUser() {
            // Проверяем авторизацию через /api/check-auth
            try {
                const authResponse = await fetch('/api/check-auth', { credentials: 'include' });
                const authData = await authResponse.json();
                
                if (authData.authenticated && authData.user_id) {
                    // Пользователь авторизован - используем user_id из сессии
                    currentUserId = authData.user_id;
                    updateUserInfo();
                } else {
                    // Пользователь не авторизован - скрываем блок с user_id
                    currentUserId = null;
                    updateUserInfoForGuest();
                }
            } catch (error) {
                console.error('Ошибка проверки авторизации:', error);
                currentUserId = null;
                updateUserInfoForGuest();
            }
        }
        
        function updateUserInfo() {
            if (!currentUserId) {
                updateUserInfoForGuest();
                return;
            }
            
            // Для зарегистрированных - показываем user_id и статистику
            const userIdElement = document.getElementById('userId');
            const userIdBlock = document.getElementById('userIdBlock');
            const copyIdButton = document.getElementById('copyIdButton');
            
            if (userIdElement) {
                userIdElement.textContent = currentUserId;
            }
            if (userIdBlock) {
                userIdBlock.style.display = 'block';
            }
            if (copyIdButton) {
                copyIdButton.style.display = 'block';
            }
            
            fetch('/api/usage', { credentials: 'include' })
                .then(r => r.json())
                .then(data => {
                    const usageInfo = document.getElementById('usageInfo');
                    if (usageInfo) {
                        usageInfo.textContent = `${data.used_today}/${data.daily_limit}`;
                    }
                })
                .catch(err => console.error('Ошибка получения статистики:', err));
        }
        
        function updateUserInfoForGuest() {
            // Для незарегистрированных - скрываем user_id, показываем только статистику использования
            const userIdBlock = document.getElementById('userIdBlock');
            const copyIdButton = document.getElementById('copyIdButton');
            
            if (userIdBlock) {
                userIdBlock.style.display = 'none';
            }
            if (copyIdButton) {
                copyIdButton.style.display = 'none';
            }
            
            // Получаем статистику для незарегистрированных
            fetch('/api/usage', { credentials: 'include' })
                .then(r => r.json())
                .then(data => {
                    const usageInfo = document.getElementById('usageInfo');
                    if (usageInfo) {
                        usageInfo.textContent = `${data.used_today}/${data.daily_limit}`;
                    }
                })
                .catch(err => console.error('Ошибка получения статистики:', err));
        }
        
        function copyUserId() {
            if (!currentUserId) {
                alert('ID доступен только для зарегистрированных пользователей');
                return;
            }
            navigator.clipboard.writeText(currentUserId);
            alert('ID скопирован: ' + currentUserId);
        }
        
        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            if (!file.name.match(/\\.(pdf|docx|txt|jpg|jpeg|png|webp)$/i)) {
                alert('Пожалуйста, выберите файл в формате PDF, DOCX, TXT, JPG или PNG');
                return;
            }
            
            if (file.size > 10 * 1024 * 1024) {
                alert('Файл слишком большой. Максимальный размер: 10MB');
                return;
            }
            
            selectedFile = file;
            document.getElementById('fileName').textContent = file.name;
            document.getElementById('fileInfo').style.display = 'block';
            document.getElementById('analyzeBtn').disabled = false;
        }
        
        async function analyzeDocument() {
            if (!selectedFile) return;
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('analyzeBtn').disabled = true;
            
            try {
                const formData = new FormData();
                formData.append('file', selectedFile);
                // НОВАЯ ЛОГИКА: user_id НЕ отправляем для незарегистрированных
                // Сервер сам определит авторизацию через сессию
                // Если пользователь авторизован, user_id будет в сессии на сервере
                
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    credentials: 'include', // Важно для отправки сессии
                    body: formData
                });
                
                const data = await response.json();
                
                document.getElementById('loading').style.display = 'none';
                
                if (data.success) {
                    showResult(data);
                    // Обновляем статистику
                    if (currentUserId) {
                        updateUserInfo();
                    } else {
                        updateUserInfoForGuest();
                    }
                } else {
                    // Проверяем требуется ли регистрация
                    if (data.registration_required || response.status === 403) {
                        showRegistrationModal();
                    } else {
                        alert('Ошибка: ' + data.error);
                    }
                    document.getElementById('analyzeBtn').disabled = false;
                }
                
            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                
                if (error.message.includes('403')) {
                    showRegistrationModal();
                } else if (error.message.includes('402')) {
                    alert('❌ Бесплатный лимит исчерпан!\\n\\n💎 Зарегистрируйтесь и перейдите на платный тариф для продолжения.');
                } else {
                    alert('Ошибка соединения: ' + error.message);
                }
                
                document.getElementById('analyzeBtn').disabled = false;
            }
        }
        
        function showRegistrationModal() {
            if (confirm('Вы использовали 1 бесплатный анализ. Для продолжения необходимо зарегистрироваться. Перейти к регистрации?')) {
                window.location.href = '/register';
            }
        }
        
        // Проверяем авторизацию при загрузке
        async function checkAuth() {
            try {
                const response = await fetch('/api/check-auth', {
                    credentials: 'include'
                });
                const data = await response.json();
                
                const authButtons = document.getElementById('authButtons');
                const userMenu = document.getElementById('userMenu');
                const mobileAuth = document.getElementById('mobileAuthButtons');
                const mobileUser = document.getElementById('mobileUserMenu');
                
                if (data.authenticated) {
                    if (authButtons) authButtons.style.display = 'none';
                    if (userMenu) userMenu.style.display = 'flex';
                    if (mobileAuth) mobileAuth.style.display = 'none';
                    if (mobileUser) mobileUser.style.display = 'block';
                } else {
                    if (authButtons) authButtons.style.display = 'flex';
                    if (userMenu) userMenu.style.display = 'none';
                    if (mobileAuth) mobileAuth.style.display = 'block';
                    if (mobileUser) mobileUser.style.display = 'none';
                }
            } catch (error) {
                // Ошибка проверки - оставляем кнопки по умолчанию
                console.error('Auth check error:', error);
            }
        }
        
        // Сохраняем данные анализа для скачивания
        let currentAnalysisData = null;
        
        function showResult(data) {
            const resultDiv = document.getElementById('result');
            const resultContent = document.getElementById('resultContent');
            
            // Сохраняем данные анализа для скачивания
            currentAnalysisData = data;
            
            resultContent.innerHTML = createSmartAnalysisHTML(data);
            resultDiv.style.display = 'block';
            resultDiv.scrollIntoView({ behavior: 'smooth' });
        }
        
        async function downloadAnalysis(event) {
            if (!currentAnalysisData) {
                alert('Ошибка: данные анализа не найдены');
                return;
            }
            
            try {
                // Показываем индикатор загрузки
                const button = event ? event.target : document.querySelector('button[onclick*="downloadAnalysis"]');
                const originalText = button.innerHTML;
                button.disabled = true;
                button.innerHTML = '⏳ Генерация PDF...';
                
                // Отправляем запрос на сервер
                const response = await fetch('/api/download-analysis', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include',
                    body: JSON.stringify({
                        analysis: currentAnalysisData.result,
                        filename: currentAnalysisData.filename || 'document.pdf'
                    })
                });
                
                if (response.ok) {
                    // Получаем PDF файл
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `analysis_${currentAnalysisData.filename || 'document'}_${new Date().toISOString().split('T')[0]}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    button.innerHTML = '✅ Скачано!';
                    setTimeout(() => {
                        button.innerHTML = originalText;
                        button.disabled = false;
                    }, 2000);
                } else {
                    const error = await response.json();
                    alert('Ошибка при генерации PDF: ' + (error.error || 'Неизвестная ошибка'));
                    button.innerHTML = originalText;
                    button.disabled = false;
                }
            } catch (error) {
                console.error('Ошибка скачивания:', error);
                alert('Ошибка соединения: ' + error.message);
                event.target.disabled = false;
                event.target.innerHTML = '📥 Скачать анализ в PDF';
            }
        }
        
        function createSmartAnalysisHTML(data) {
            const analysis = data.result;
            const isAuthenticated = analysis.is_authenticated || false;
            const isGuest = analysis.is_guest || !isAuthenticated;
            
            // CSS стили для адаптивности
            const mobileStyles = `
                <style>
                    @media (max-width: 768px) {
                        .analysis-block { padding: 20px !important; margin: 15px 0 !important; }
                        .analysis-block h3, .analysis-block h4 { font-size: 1.2rem !important; }
                        .analysis-block h5 { font-size: 1rem !important; }
                        .analysis-icon { width: 40px !important; height: 40px !important; font-size: 1.2rem !important; }
                        .risk-stats-grid { grid-template-columns: 1fr !important; gap: 10px !important; }
                        .expert-section { padding: 20px !important; margin: 15px 0 !important; }
                        .registration-buttons { flex-direction: column !important; }
                        .registration-buttons a { width: 100% !important; text-align: center !important; }
                    }
                </style>
            `;
            
            // Призыв к регистрации для гостей
            const registrationPrompt = isGuest ? `
                <div class="analysis-block" style="background: linear-gradient(135deg, #f72585 0%, #7209b7 100%); color: white; padding: 30px; border-radius: 20px; margin: 20px 0; box-shadow: 0 10px 40px rgba(247, 37, 133, 0.3); text-align: center; position: relative; overflow: hidden; width: 100%; max-width: 100%;">
                    <div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
                    <div style="position: absolute; bottom: -30px; left: -30px; width: 150px; height: 150px; background: rgba(255,255,255,0.05); border-radius: 50%;"></div>
                    <div style="position: relative; z-index: 2;">
                        <div style="font-size: 3rem; margin-bottom: 15px;">🔒</div>
                        <h3 style="margin: 0 0 15px 0; color: white; font-size: 1.5rem; font-weight: 700;">Это краткий анализ</h3>
                        <p style="margin: 0 0 25px 0; opacity: 0.95; font-size: 1.1rem; line-height: 1.6;">
                            Для получения <strong>расширенного анализа</strong> с детальными рекомендациями, практическими действиями и полной экспертизой <strong>зарегистрируйтесь</strong> или <strong>войдите</strong> на сайт
                        </p>
                        <div class="registration-buttons" style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
                            <a href="/register" style="background: white; color: #7209b7; padding: 14px 30px; border-radius: 50px; text-decoration: none; font-weight: 700; font-size: 1rem; transition: transform 0.3s; display: inline-block; box-shadow: 0 4px 15px rgba(0,0,0,0.2);" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                                📝 Зарегистрироваться
                            </a>
                            <a href="/login" style="background: rgba(255,255,255,0.2); color: white; padding: 14px 30px; border-radius: 50px; text-decoration: none; font-weight: 700; font-size: 1rem; transition: transform 0.3s; display: inline-block; border: 2px solid white;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                                🔐 Войти
                            </a>
                        </div>
                        <div style="margin-top: 20px; font-size: 0.9rem; opacity: 0.8;">
                            ✨ Регистрация займет 1 минуту • 1 бесплатный анализ в день
                        </div>
                    </div>
                </div>
            ` : '';
            
            // Основной блок с информацией о документе
            const mainHeader = `
                <div class="analysis-block" style="background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; padding: 30px; border-radius: 15px; margin: 20px 0; box-shadow: 0 8px 30px rgba(67, 97, 238, 0.2); width: 100%; max-width: 100%;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                        <div style="flex: 1; min-width: 200px;">
                            <h3 style="margin: 0; color: white; font-size: 1.4rem; font-weight: 700;">${analysis.document_type_name}</h3>
                            <p style="margin: 5px 0; opacity: 0.95; font-size: 1rem;">${analysis.executive_summary.risk_icon} ${analysis.executive_summary.risk_description}</p>
                        </div>
                        <div style="text-align: right;">
                            <div class="risk-badge risk-${analysis.executive_summary.risk_level.toLowerCase()}" 
                                 style="font-size: 16px; padding: 10px 20px; font-weight: 700; white-space: nowrap;">
                                ${analysis.executive_summary.risk_level}
                            </div>
                        </div>
                    </div>
                    
                    <div style="margin-top: 15px; padding: 15px; background: rgba(255,255,255,0.15); border-radius: 10px; backdrop-filter: blur(10px);">
                        <strong style="font-size: 1.05rem;">💡 Решение:</strong> 
                        <span style="opacity: 0.95;">${analysis.executive_summary.decision_support}</span>
                    </div>
                </div>
            `;
            
            // Экспертиза (разная для гостей и зарегистрированных)
            const expertAnalysis = isGuest ? `
                <div class="analysis-block expert-section" style="background: white; padding: 30px; border-radius: 15px; margin: 20px 0; border-left: 5px solid var(--primary); box-shadow: 0 5px 20px rgba(0,0,0,0.08); width: 100%; max-width: 100%;">
                    <h4 style="color: var(--primary); margin-bottom: 20px; font-size: 1.3rem; display: flex; align-items: center; gap: 10px; font-weight: 700;">
                        <span>📋</span> Краткая экспертиза
                    </h4>
                    <p style="color: #4a5568; line-height: 1.8; margin: 0; font-size: 1.05rem;">${analysis.expert_analysis.legal_expertise}</p>
                    ${analysis.expert_analysis.financial_analysis ? `
                        <div style="margin-top: 20px; padding: 18px; background: #f8f9fa; border-radius: 10px; border-left: 4px solid #4cc9f0;">
                            <p style="margin: 0; color: #6c757d; font-size: 1rem; line-height: 1.6;">${analysis.expert_analysis.financial_analysis}</p>
                        </div>
                    ` : ''}
                </div>
            ` : `
                <!-- Визуализация статистики рисков или сообщение об отсутствии рисков -->
                ${analysis.risk_analysis && analysis.risk_analysis.risk_statistics
                    ? (
                        (analysis.risk_analysis.risk_statistics.total || 0) > 0
                        ? `
                <div class="analysis-block" style="background: white; padding: 30px; border-radius: 15px; margin: 20px 0; box-shadow: 0 5px 25px rgba(0,0,0,0.1); width: 100%; max-width: 100%;">
                    <h4 style="color: var(--dark); margin-bottom: 25px; font-size: 1.4rem; font-weight: 700; display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 1.8rem;">📊</span> Статистика рисков
                    </h4>
                    <div class="risk-stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 25px;">
                        ${analysis.risk_analysis.risk_statistics.CRITICAL > 0 ? `
                        <div style="background: linear-gradient(135deg, #fed7d7 0%, #fc8181 100%); padding: 20px; border-radius: 12px; text-align: center; border: 2px solid #c53030;">
                            <div style="font-size: 2.5rem; font-weight: 700; color: #c53030; margin-bottom: 8px;">${analysis.risk_analysis.risk_statistics.CRITICAL}</div>
                            <div style="color: #7f1d1d; font-weight: 600; font-size: 0.95rem;">Критических</div>
                        </div>
                        ` : ''}
                        ${analysis.risk_analysis.risk_statistics.HIGH > 0 ? `
                        <div style="background: linear-gradient(135deg, #feebc8 0%, #f6ad55 100%); padding: 20px; border-radius: 12px; text-align: center; border: 2px solid #d69e2e;">
                            <div style="font-size: 2.5rem; font-weight: 700; color: #d69e2e; margin-bottom: 8px;">${analysis.risk_analysis.risk_statistics.HIGH}</div>
                            <div style="color: #744210; font-weight: 600; font-size: 0.95rem;">Высоких</div>
                        </div>
                        ` : ''}
                        ${analysis.risk_analysis.risk_statistics.MEDIUM > 0 ? `
                        <div style="background: linear-gradient(135deg, #fefcbf 0%, #faf089 100%); padding: 20px; border-radius: 12px; text-align: center; border: 2px solid #d69e2e;">
                            <div style="font-size: 2.5rem; font-weight: 700; color: #d69e2e; margin-bottom: 8px;">${analysis.risk_analysis.risk_statistics.MEDIUM}</div>
                            <div style="color: #744210; font-weight: 600; font-size: 0.95rem;">Средних</div>
                        </div>
                        ` : ''}
                        ${analysis.risk_analysis.risk_statistics.LOW > 0 ? `
                        <div style="background: linear-gradient(135deg, #c6f6d5 0%, #68d391 100%); padding: 20px; border-radius: 12px; text-align: center; border: 2px solid #38a169;">
                            <div style="font-size: 2.5rem; font-weight: 700; color: #38a169; margin-bottom: 8px;">${analysis.risk_analysis.risk_statistics.LOW}</div>
                            <div style="color: #22543d; font-weight: 600; font-size: 0.95rem;">Низких</div>
                        </div>
                        ` : ''}
                        <div style="background: linear-gradient(135deg, #e6f3ff 0%, #bee3f8 100%); padding: 20px; border-radius: 12px; text-align: center; border: 2px solid var(--primary);">
                            <div style="font-size: 2.5rem; font-weight: 700; color: var(--primary); margin-bottom: 8px;">${analysis.risk_analysis.risk_statistics.total || 0}</div>
                            <div style="color: #2c5282; font-weight: 600; font-size: 0.95rem;">Всего рисков</div>
                        </div>
                    </div>
                </div>
                        `
                        : `
                <div class="analysis-block" style="background: #f0fff4; padding: 24px; border-radius: 15px; margin: 20px 0; border-left: 5px solid #38a169; box-shadow: 0 4px 18px rgba(0,0,0,0.06); width: 100%; max-width: 100%;">
                    <h4 style="color: #22543d; margin-bottom: 12px; font-size: 1.3rem; font-weight: 700; display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.6rem;">✅</span> Существенных рисков не выявлено
                    </h4>
                    <p style="margin: 0; color: #2f855a; font-size: 1rem; line-height: 1.6;">
                        По результатам анализа в документе не обнаружено критических или высоких юридических и финансовых рисков.
                        Тем не менее рекомендуется внимательно ознакомиться с договором и учесть общие рекомендации по улучшению условий.
                    </p>
                </div>
                        `
                    )
                    : ''
                }
                
                <!-- Юридическая экспертиза -->
                <div class="analysis-block expert-section" style="background: white; padding: 30px; border-radius: 15px; margin: 20px 0; border-left: 5px solid var(--primary); box-shadow: 0 5px 25px rgba(0,0,0,0.1); width: 100%; max-width: 100%;">
                    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                        <div class="analysis-icon" style="width: 60px; height: 60px; background: linear-gradient(135deg, var(--primary), var(--primary-dark)); border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 2rem; flex-shrink: 0;">🧑‍⚖️</div>
                        <h4 style="color: var(--primary); margin: 0; font-size: 1.4rem; font-weight: 700;">Юридическая экспертиза</h4>
                    </div>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 12px; margin-top: 15px;">
                        <p style="color: #4a5568; line-height: 1.8; margin: 0; font-size: 1.05rem; text-align: justify;">${analysis.expert_analysis.legal_expertise}</p>
                    </div>
                </div>
                
                <!-- Финансовый анализ -->
                <div class="analysis-block expert-section" style="background: white; padding: 30px; border-radius: 15px; margin: 20px 0; border-left: 5px solid #4cc9f0; box-shadow: 0 5px 25px rgba(0,0,0,0.1); width: 100%; max-width: 100%;">
                    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                        <div class="analysis-icon" style="width: 60px; height: 60px; background: linear-gradient(135deg, #4cc9f0, #38a169); border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 2rem; flex-shrink: 0;">💰</div>
                        <h4 style="color: #4cc9f0; margin: 0; font-size: 1.4rem; font-weight: 700;">Финансовый анализ</h4>
                    </div>
                    <div style="background: #f0f9ff; padding: 20px; border-radius: 12px; margin-top: 15px;">
                        <p style="color: #4a5568; line-height: 1.8; margin: 0; font-size: 1.05rem; text-align: justify;">${analysis.expert_analysis.financial_analysis}</p>
                    </div>
                </div>
                
                ${analysis.expert_analysis.operational_risks ? `
                <!-- Операционные риски -->
                <div class="analysis-block expert-section" style="background: white; padding: 30px; border-radius: 15px; margin: 20px 0; border-left: 5px solid var(--warning); box-shadow: 0 5px 25px rgba(0,0,0,0.1); width: 100%; max-width: 100%;">
                    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                        <div class="analysis-icon" style="width: 60px; height: 60px; background: linear-gradient(135deg, var(--warning), #f94144); border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 2rem; flex-shrink: 0;">⚙️</div>
                        <h4 style="color: var(--warning); margin: 0; font-size: 1.4rem; font-weight: 700;">Операционные риски</h4>
                    </div>
                    <div style="background: #fffaf0; padding: 20px; border-radius: 12px; margin-top: 15px;">
                        <p style="color: #4a5568; line-height: 1.8; margin: 0; font-size: 1.05rem; text-align: justify;">${analysis.expert_analysis.operational_risks}</p>
                    </div>
                </div>
                ` : ''}
                
                ${analysis.expert_analysis.strategic_assessment ? `
                <!-- Стратегическая оценка -->
                <div class="analysis-block expert-section" style="background: white; padding: 30px; border-radius: 15px; margin: 20px 0; border-left: 5px solid var(--secondary); box-shadow: 0 5px 25px rgba(0,0,0,0.1); width: 100%; max-width: 100%;">
                    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                        <div class="analysis-icon" style="width: 60px; height: 60px; background: linear-gradient(135deg, var(--secondary), var(--primary)); border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 2rem; flex-shrink: 0;">🎯</div>
                        <h4 style="color: var(--secondary); margin: 0; font-size: 1.4rem; font-weight: 700;">Стратегическая оценка</h4>
                    </div>
                    <div style="background: #faf5ff; padding: 20px; border-radius: 12px; margin-top: 15px;">
                        <p style="color: #4a5568; line-height: 1.8; margin: 0; font-size: 1.05rem; text-align: justify;">${analysis.expert_analysis.strategic_assessment}</p>
                    </div>
                </div>
                ` : ''}
            `;
            
            // Риски (разные для гостей и зарегистрированных)
            const risksSection = `
                <div class="analysis-block" style="background: white; padding: 30px; border-radius: 15px; margin: 20px 0; border-left: 5px solid var(--warning); box-shadow: 0 5px 25px rgba(0,0,0,0.1); width: 100%; max-width: 100%;">
                    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 25px;">
                        <div class="analysis-icon" style="width: 60px; height: 60px; background: linear-gradient(135deg, var(--warning), #f94144); border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 2rem; flex-shrink: 0;">⚠️</div>
                        <h4 style="color: var(--warning); margin: 0; font-size: 1.4rem; font-weight: 700;">${isGuest ? 'Основные риски' : 'Детальный анализ рисков'}</h4>
                    </div>
                    ${!isGuest ? `
                    <div style="margin: 20px 0; padding: 20px; background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%); border-radius: 12px; border: 2px solid #fc8181;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <strong style="color: #c53030; font-size: 1.1rem;">📊 Сводка по рискам:</strong>
                        </div>
                        <p style="margin: 0; color: #7f1d1d; font-size: 1.05rem; line-height: 1.7;">${analysis.risk_analysis.risk_summary}</p>
                    </div>
                    ` : `
                    <div style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 10px;">
                        <strong style="color: var(--dark);">📊 Статистика:</strong> 
                        <span style="color: #6c757d;">${analysis.risk_analysis.risk_summary}</span>
                    </div>
                    `}
                    ${(analysis.risk_analysis.key_risks || []).map((risk, index) => `
                        <div style="background: ${risk.color}15; padding: 22px; margin: 15px 0; border-radius: 12px; border-left: 5px solid ${risk.color}; box-shadow: 0 3px 12px rgba(0,0,0,0.08); transition: all 0.3s; width: 100%;" onmouseover="this.style.transform='translateX(5px)'; this.style.boxShadow='0 5px 20px rgba(0,0,0,0.12)'" onmouseout="this.style.transform='translateX(0)'; this.style.boxShadow='0 3px 12px rgba(0,0,0,0.08)'">
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap;">
                                <span class="risk-badge risk-${risk.level.toLowerCase()}" style="font-size: 14px; padding: 8px 16px; font-weight: 700; white-space: nowrap;">
                                    ${risk.icon} ${risk.level}
                                </span>
                                <strong style="flex: 1; margin-left: 0; color: var(--dark); font-size: 1.1rem; min-width: 200px;">${risk.title}</strong>
                            </div>
                            <div style="background: rgba(255,255,255,0.7); padding: 15px; border-radius: 8px; margin-top: 10px;">
                                <p style="margin: 0; color: #4a5568; line-height: 1.7; font-size: 1.05rem; text-align: justify;">${risk.description}</p>
                            </div>
                        </div>
                    `).join('')}
                    ${isGuest && (analysis.risk_analysis.key_risks || []).length < (analysis.risk_analysis.risk_statistics?.total || 0) ? `
                        <div style="margin-top: 20px; padding: 20px; background: linear-gradient(135deg, #f0f7ff 0%, #e3f2fd 100%); border-radius: 12px; text-align: center; border: 2px dashed var(--primary);">
                            <p style="margin: 0; color: var(--primary); font-weight: 600; font-size: 1.05rem;">
                                🔒 Для просмотра всех ${analysis.risk_analysis.risk_statistics.total} рисков зарегистрируйтесь на сайте
                            </p>
                        </div>
                    ` : ''}
                </div>
            `;
            
            // Рекомендации (только для зарегистрированных)
            const recommendationsSection = !isGuest && analysis.recommendations && typeof analysis.recommendations === 'object' ? `
                <div class="analysis-block" style="background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%); padding: 35px; border-radius: 15px; margin: 20px 0; border-left: 5px solid #38a169; box-shadow: 0 5px 25px rgba(56, 161, 105, 0.15); width: 100%; max-width: 100%;">
                    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 30px;">
                        <div class="analysis-icon" style="width: 60px; height: 60px; background: linear-gradient(135deg, #38a169, #2f855a); border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 2rem; flex-shrink: 0;">💡</div>
                        <h4 style="color: #2f855a; margin: 0; font-size: 1.4rem; font-weight: 700;">Практические рекомендации и действия</h4>
                    </div>
                    
                    ${analysis.recommendations.practical_actions && analysis.recommendations.practical_actions.length > 0 ? `
                        <div style="margin-bottom: 30px;">
                            <h5 style="color: #2f855a; margin-bottom: 20px; font-size: 1.2rem; font-weight: 700; display: flex; align-items: center; gap: 10px;">
                                <span>📋</span> Рекомендуемые действия
                            </h5>
                            <div style="display: flex; flex-direction: column; gap: 15px;">
                                ${analysis.recommendations.practical_actions.map((action, index) => `
                                    <div style="background: white; padding: 22px; border-radius: 12px; border-left: 5px solid #38a169; box-shadow: 0 3px 12px rgba(0,0,0,0.08); width: 100%; transition: all 0.3s;" onmouseover="this.style.transform='translateX(5px)'; this.style.boxShadow='0 5px 20px rgba(56, 161, 105, 0.2)'" onmouseout="this.style.transform='translateX(0)'; this.style.boxShadow='0 3px 12px rgba(0,0,0,0.08)'">
                                        <div style="display: flex; align-items: start; gap: 15px;">
                                            <div style="width: 35px; height: 35px; background: linear-gradient(135deg, #38a169, #2f855a); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 1.1rem; flex-shrink: 0;">${index + 1}</div>
                                            <div style="flex: 1;">
                                                ${typeof action === 'object' ? `
                                                    <strong style="color: var(--dark); display: block; margin-bottom: 8px; font-size: 1.1rem;">${action.title || action.action || 'Рекомендация'}</strong>
                                                    <p style="margin: 0; color: #4a5568; line-height: 1.7; font-size: 1.05rem; text-align: justify;">${action.description || action.reason || ''}</p>
                                                ` : `<p style="margin: 0; color: #4a5568; line-height: 1.7; font-size: 1.05rem; text-align: justify;">${action}</p>`}
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${analysis.recommendations.priority_actions && analysis.recommendations.priority_actions.length > 0 ? `
                        <div style="margin-top: 25px; padding: 25px; background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); border-radius: 12px; border-left: 5px solid #f8961e; box-shadow: 0 3px 12px rgba(248, 150, 30, 0.2);">
                            <h5 style="color: #f8961e; margin-bottom: 18px; font-size: 1.2rem; font-weight: 700; display: flex; align-items: center; gap: 10px;">
                                <span>🚨</span> Срочные действия
                            </h5>
                            <ul style="margin: 0; padding-left: 25px; color: #4a5568; line-height: 1.9; font-size: 1.05rem;">
                                ${analysis.recommendations.priority_actions.map(action => `
                                    <li style="margin-bottom: 10px;">${typeof action === 'object' ? (action.title || action.action || 'Действие') : action}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${analysis.recommendations.alternative_solutions && analysis.recommendations.alternative_solutions.length > 0 ? `
                        <div style="margin-top: 25px; padding: 25px; background: linear-gradient(135deg, #e6f3ff 0%, #cce7ff 100%); border-radius: 12px; border-left: 5px solid var(--primary);">
                            <h5 style="color: var(--primary); margin-bottom: 18px; font-size: 1.2rem; font-weight: 700; display: flex; align-items: center; gap: 10px;">
                                <span>🔄</span> Альтернативные решения
                            </h5>
                            <ul style="margin: 0; padding-left: 25px; color: #4a5568; line-height: 1.9; font-size: 1.05rem;">
                                ${analysis.recommendations.alternative_solutions.map(solution => `
                                    <li style="margin-bottom: 10px;">${typeof solution === 'object' ? (solution.title || solution.solution || 'Решение') : solution}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            ` : '';
            
            // Кнопка скачивания (только для зарегистрированных)
            const downloadButton = !isGuest ? `
                <div class="analysis-block" style="background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%); padding: 30px; border-radius: 15px; margin: 30px 0; text-align: center; box-shadow: 0 8px 30px rgba(67, 97, 238, 0.3); width: 100%; max-width: 100%;">
                    <div style="color: white;">
                        <div style="font-size: 3rem; margin-bottom: 15px;">📥</div>
                        <h3 style="margin: 0 0 15px 0; color: white; font-size: 1.5rem; font-weight: 700;">Сохранить анализ</h3>
                        <p style="margin: 0 0 25px 0; opacity: 0.95; font-size: 1.1rem; line-height: 1.6;">
                            Скачайте полный отчет анализа в формате PDF для сохранения, печати или отправки юристу
                        </p>
                        <button onclick="downloadAnalysis(event)" style="background: white; color: var(--primary); padding: 16px 40px; border-radius: 50px; text-decoration: none; font-weight: 700; font-size: 1.1rem; border: none; cursor: pointer; transition: all 0.3s; box-shadow: 0 4px 15px rgba(0,0,0,0.2);" onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 20px rgba(0,0,0,0.3)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(0,0,0,0.2)'">
                            📥 Скачать анализ в PDF
                        </button>
                        <div style="margin-top: 15px; font-size: 0.9rem; opacity: 0.8;">
                            ✨ PDF включает все разделы анализа, риски и рекомендации
                        </div>
                    </div>
                </div>
            ` : '';
            
            return mobileStyles + registrationPrompt + mainHeader + expertAnalysis + risksSection + recommendationsSection + downloadButton;
        }
        
        // FAQ Toggle
        function toggleFAQ(id) {
            const answer = document.getElementById(`faq-${id}`);
            const isOpen = answer.classList.contains('open');
            
            document.querySelectorAll('.faq-answer').forEach(faq => {
                faq.classList.remove('open');
            });
            
            if (!isOpen) {
                answer.classList.add('open');
            }
        }
        
        // Buy plan
        async function buyPlan(planType) {
            // Проверяем авторизацию
            try {
                const authResponse = await fetch('/api/check-auth', {
                    credentials: 'include',
                    cache: 'no-cache'
                });
                
                const authData = await authResponse.json();
                
                if (!authData.authenticated) {
                    // Пользователь не авторизован - предлагаем войти/зарегистрироваться
                    if (confirm('Для покупки тарифа необходимо войти в аккаунт или зарегистрироваться. Перейти к регистрации?')) {
                        window.location.href = '/register';
                    }
                    return;
                }
            
                // Пользователь авторизован - продолжаем покупку
                if (!currentUserId) {
                    currentUserId = authData.user_id;
                }
                
                try {
                    const response = await fetch('/payments/create-payment', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        credentials: 'include',
                        body: JSON.stringify({
                            user_id: currentUserId || authData.user_id,
                            plan: planType
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        window.location.href = result.payment_url;
                    } else {
                        alert('Ошибка: ' + result.error);
                    }
                    
                } catch (error) {
                    alert('Ошибка соединения: ' + error.message);
                }
            } catch (error) {
                console.error('Ошибка проверки авторизации:', error);
                alert('Ошибка проверки авторизации. Пожалуйста, войдите в аккаунт.');
            }
        }
        
        // Burger menu toggle
        function toggleMenu() {
            const dropdown = document.getElementById('menuDropdown');
            dropdown.classList.toggle('show');
        }
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            const menu = document.querySelector('.burger-menu');
            const dropdown = document.getElementById('menuDropdown');
            
            if (!menu.contains(event.target)) {
                dropdown.classList.remove('show');
            }
        });
        
        // Управление рекламным баннером
        function closeAdBanner() {
            const banner = document.getElementById('adBanner');
            if (banner) {
                banner.classList.add('hidden');
                // Не сохраняем в localStorage - баннер будет показываться при каждом обновлении страницы
            }
        }
        
        function trackAdClick() {
            // Можно добавить аналитику кликов по баннеру
            if (typeof ym !== 'undefined') {
                ym(105562312, 'reachGoal', 'ad_banner_click');
            }
        }
        
        // Проверяем состояние баннера при загрузке
        function initAdBanner() {
            const banner = document.getElementById('adBanner');
            if (!banner) return;
            
            // Баннер всегда показывается при загрузке страницы
            // Не проверяем localStorage - баннер появляется при каждом обновлении
            banner.classList.remove('hidden');
        }
        
        // Initialize on load
        document.addEventListener('DOMContentLoaded', function() {
            loadUser();
            initCarousel();
            checkAuth();
            initAdBanner();
        });
    </script>
    
    <!-- Schema.org Structured Data -->
    <script type="application/ld+json">
    [
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "DocScan AI",
            "url": "https://docscan-ai.ru",
            "logo": "https://docscan-ai.ru/static/favicon.ico",
            "description": "Автоматический анализ документов с искусственным интеллектом. Проверка договоров на юридические и финансовые риски за 60 секунд.",
            "contactPoint": {
                "@type": "ContactPoint",
                "email": "docscanhelp@gmail.com",
                "contactType": "customer support",
                "availableLanguage": "Russian"
            },
            "sameAs": [
                "https://t.me/docscan_ai"
            ]
        },
        {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "DocScan AI",
            "applicationCategory": "BusinessApplication",
            "operatingSystem": "Web Browser",
            "description": "Автоматический анализ документов с искусственным интеллектом. Проверка договоров на юридические и финансовые риски за 60 секунд.",
            "url": "https://docscan-ai.ru",
            "author": {
                "@type": "Organization",
                "name": "DocScan AI"
            },
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "RUB"
            },
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.8",
                "ratingCount": "157"
            }
        },
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": "Какой максимальный размер файла?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Максимальный размер файла - 10MB. Поддерживаются форматы: PDF, DOCX, TXT."
                    }
                },
                {
                    "@type": "Question",
                    "name": "Сколько стоит анализ документов?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "1 анализ бесплатно (для зарегистрированных пользователей). Платные тарифы: Базовый (Неограниченное количество анализов) - 490₽/мес."
                    }
                },
                {
                    "@type": "Question",
                    "name": "Конфиденциальны ли мои документы?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Да! Документы не сохраняются на наших серверах. После анализа файлы автоматически удаляются. Текст передается в API по защищенному соединению."
                    }
                },
                {
                    "@type": "Question",
                    "name": "Сколько времени занимает анализ документа?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Обычно анализ занимает 30-60 секунд. Скорость зависит от размера документа и загрузки сервера."
                    }
                },
                {
                    "@type": "Question",
                    "name": "Насколько точен AI-анализ?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "ИИ хорошо справляется с выявлением типовых рисков в договорах. Однако это инструмент для первичной проверки - для важных документов рекомендуем консультацию с юристом."
                    }
                }
            ]
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Главная",
                    "item": "https://docscan-ai.ru"
                }
            ]
        }
    ]
    </script>
    
    <!-- Yandex.Metrika -->
    <script type="text/javascript">
        (function(m,e,t,r,i,k,a){
            m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
            m[i].l=1*new Date();
            for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
            k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
        })(window, document,'script','https://mc.yandex.ru/metrika/tag.js','ym');
ym(105562312, 'init', {clickmap:true, trackLinks:true, accurateTrackBounce:true, webvisor:true});
    </script>
    <noscript><div><img src="https://mc.yandex.ru/watch/105562312" style="position:absolute; left:-9999px;" alt="" /></div></noscript>

    <!-- Рекламный баннер -->
    <div id="adBanner" class="ad-banner">
        <button class="ad-banner-close" onclick="closeAdBanner()" aria-label="Закрыть баннер">×</button>
        <a href="https://t.me/BirzhaAuditbot" target="_blank" class="ad-banner-link" onclick="trackAdClick()">
            <img src="/static/ad-banner-image.jpg" alt="Биржа Аудитории" class="ad-banner-image" onerror="this.style.display='none'">
            <div class="ad-banner-content">
                <div class="ad-banner-title">
                    📢 Биржа Аудитории
                </div>
                <div class="ad-banner-description">
                    Для взаимного обмена подписчиками<br>
                    Получайте реальных подписчиков
                </div>
            </div>
        </a>
    </div>
    
    <!-- Yandex.RTB R-A-18680294-2 (floorAd для мобильных) -->
    <script>
    window.yaContextCb.push(() => {
        Ya.Context.AdvManager.render({
            "blockId": "R-A-18680294-2",
            "type": "floorAd",
            "platform": "touch"
        })
    })
    </script>    
    <!-- Yandex.RTB R-A-18680294-3 (floorAd для десктопа) -->
    <script>
    window.yaContextCb.push(() => {
        Ya.Context.AdvManager.render({
            "blockId": "R-A-18680294-3",
            "type": "floorAd",
            "platform": "desktop"
        })
    })
    </script>

</body>
</html>
    '''

# ... (остальные функции routes остаются БЕЗ ИЗМЕНЕНИЙ)
@main_bp.route('/terms')
def terms():
    """Страница пользовательского соглашения"""
    RussianLogger.log_page_view("Пользовательское соглашение")
    return render_template('terms.html')

@main_bp.route('/privacy')
def privacy():
    """Страница политики конфиденциальности"""
    RussianLogger.log_page_view("Политика конфиденциальности")
    return render_template('privacy.html')

@main_bp.route('/offer')
def offer():
    """Страница публичной оферты"""
    RussianLogger.log_page_view("Публичная оферта")
    return render_template('offer.html')

@main_bp.route('/sitemap.xml')
def sitemap():
    """Sitemap для SEO с динамическими датами"""
    from datetime import datetime
    base_url = "https://docscan-ai.ru"
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Приоритетные страницы (обновляются часто)
    priority_pages = [
        ('/', 'daily', '1.0'),
        ('/analiz-dokumentov', 'weekly', '0.9'),
        ('/proverka-dogovorov', 'weekly', '0.9'),
        ('/articles', 'weekly', '0.9'),
        ('/faq', 'monthly', '0.8'),
        ('/calculator-penalty', 'monthly', '0.8'),
        ('/mobile-app', 'weekly', '0.8'),
    ]
    
    # Статьи (обновляются реже)
    articles = [
        '/articles/about',
        '/articles/guide',
        '/articles/tech',
        '/articles/rent',
        '/articles/labor',
        '/articles/tax',
        '/articles/business-protection',
        '/articles/freelance-gph',
        '/articles/ipoteka-2025',
    ]
    
    # Дополнительные страницы
    additional_pages = [
        ('/riski-dogovora-zayma', 'weekly', '0.9'),
        ('/avtokredit-skrytye-usloviya', 'monthly', '0.8'),
        ('/ii-dlya-proverki-dogovorov-onlayn-besplatno', 'monthly', '0.8'),
        ('/medicinskie-dokumenty-analiz', 'monthly', '0.8'),
        ('/contact', 'monthly', '0.7'),
    ]
    
    # Служебные страницы (низкий приоритет)
    service_pages = [
        ('/terms', 'yearly', '0.3'),
        ('/privacy', 'yearly', '0.3'),
        ('/offer', 'yearly', '0.3'),
    ]
    
    sitemap_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'''
    
    # Приоритетные страницы
    for url, changefreq, priority in priority_pages:
        sitemap_xml += f'''
    <url>
        <loc>{base_url}{url}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>{changefreq}</changefreq>
        <priority>{priority}</priority>
    </url>'''
    
    # Статьи
    for article in articles:
        sitemap_xml += f'''
    <url>
        <loc>{base_url}{article}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>'''
    
    # Дополнительные страницы
    for url, changefreq, priority in additional_pages:
        sitemap_xml += f'''
    <url>
        <loc>{base_url}{url}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>{changefreq}</changefreq>
        <priority>{priority}</priority>
    </url>'''
    
    # Служебные страницы
    for url, changefreq, priority in service_pages:
        sitemap_xml += f'''
    <url>
        <loc>{base_url}{url}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>{changefreq}</changefreq>
        <priority>{priority}</priority>
    </url>'''
    
    sitemap_xml += '''
</urlset>'''
    
    return sitemap_xml, 200, {'Content-Type': 'application/xml'}

@main_bp.route('/robots.txt')
def robots():
    """Robots.txt для SEO"""
    return """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /admin-login

# Дополнительные запреты, если нужны:
# Disallow: /cabinet/
# Disallow: /api/

Sitemap: https://docscan-ai.ru/sitemap.xml""", 200, {'Content-Type': 'text/plain'}

@main_bp.route('/articles')
def articles():
    """Страница со списком всех статей"""
    from app import app
    
    # Получаем опубликованные статьи из БД
    articles_list = app.user_manager.get_published_articles(limit=100)
    
    return render_template('articles.html', articles=articles_list)

@main_bp.route('/articles/<slug>')
def article_detail(slug):
    """Страница отдельной статьи"""
    from app import app
    from flask import abort
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Получаем опубликованную статью по slug
    article = app.user_manager.get_published_article_by_slug(slug)
    
    if not article:
        logger.warning(f"❌ Статья не найдена или не опубликована: slug={slug}")
        abort(404)
    
    # Получаем список всех опубликованных статей для навигации
    all_articles = app.user_manager.get_published_articles(limit=50)
    
    # Находим текущую статью в списке для навигации (предыдущая/следующая)
    current_index = next((i for i, a in enumerate(all_articles) if a.get('id') == article.id), None)
    prev_article = all_articles[current_index - 1] if current_index is not None and current_index > 0 else None
    next_article = all_articles[current_index + 1] if current_index is not None and current_index < len(all_articles) - 1 else None
    
    logger.info(f"✅ Просмотр статьи: {article.title} (slug: {slug})")
    
    return render_template('article_detail.html', 
                         article=article.to_dict(),
                         prev_article=prev_article,
                         next_article=next_article)

@main_bp.route('/articles/about')
def article_about():
    """Статья 'О проекте'"""
    return render_template('article_about.html')

@main_bp.route('/articles/guide')
def article_guide():
    """Статья 'Как пользоваться сервисом'"""
    return render_template('article_guide.html')

@main_bp.route('/articles/tech')
def article_tech():
    """Статья 'Технологии и AI'"""
    return render_template('article_tech.html')

@main_bp.route('/contact')
def contact():
    """Страница контактов"""
    return render_template('contact.html')
    
@main_bp.route('/articles/rent')
def article_rent():
    """Статья 'Как проверить договор аренды'"""
    return render_template('article_rent.html')
    
@main_bp.route('/articles/labor')
def article_labor():
    """Статья 'Топ-5 ошибок в трудовых договорах'"""
    return render_template('article_labor.html')
    
@main_bp.route('/articles/tax')
def article_tax():
    """Статья 'Финансовые риски в договорах'"""
    return render_template('article_tax.html')

@main_bp.route('/articles/nalogovaya-proverka')
def article_nalogovaya_proverka():
    """Статья 'Документ налоговой проверки'"""
    return render_template('article_nalogovaya-proverka.html')
    
@main_bp.route('/articles/business_protection')
def redirect_business_protection():
    """Редирект со старого URL (с подчёркиванием) на новый (с дефисом)"""
    return redirect('/articles/business-protection', code=301)
    
@main_bp.route('/articles/business-protection')
def article_business_protection():
    return render_template('article_business_protection.html')
    
@main_bp.route('/articles/freelance-gph')
def article_freelance_gph():
    return render_template('article_freelance_gph.html')

@main_bp.route('/articles/article_freelance_gph')
def redirect_article_freelance():
    """Редирект со старого URL на новый"""
    return redirect('/articles/freelance-gph', code=301)

@main_bp.route('/analiz-dokumentov')
def analiz_dokumentov():
    return render_template('analiz-dokumentov.html')
    
@main_bp.route('/proverka-dogovorov')
def proverka_dogovorov():
    """Страница проверки договоров"""
    return render_template('proverka-dogovorov.html')

@main_bp.route('/proverka-dokumentov-onlayn')
def proverka_dokumentov_onlayn():
    """Страница проверки документов онлайн"""
    return render_template('proverka-dokumentov-onlayn.html')

@main_bp.route('/riski-dogovora-zayma')
def riski_dogovora_zayma():
    """Страница с статьей о рисках договора займа"""
    return render_template('riski-dogovora-zayma.html')
    
@main_bp.route('/avtokredit-skrytye-usloviya')
def avtokredit_skrytye_usloviya():
    """Статья про скрытые условия в автокредитах"""
    return render_template('avtokredit-skrytye-usloviya.html')
    
@main_bp.route('/ii-dlya-proverki-dogovorov-onlayn-besplatno')
def ii_dlya_proverki_dogovorov():
    return render_template('ii-dlya-proverki-dogovorov-onlayn-besplatno.html')

@main_bp.route('/medicinskie-dokumenty-analiz')
def medicinskie_dokumenty_analiz():
    return render_template('medicinskie-dokumenty-analiz.html')
    
@main_bp.route('/faq')
def faq_page():
    return render_template('faq.html')
    
@main_bp.route('/articles/rent-check')
def redirect_rent_check():
    return redirect('/articles/rent', code=301)
    
@main_bp.route('/=')
def redirect_root_equals():
    """Редирект странного URL на главную"""
    return redirect('/', code=301)
    
@main_bp.route('/articles/ipoteka-2025')
def article_ipoteka():
    return render_template('article_ipoteka_2025.html')
    
@main_bp.route('/calculator-penalty')
def calculator_penalty():
    """Страница калькулятора неустойки"""
    return render_template('calculator_penalty.html')

@main_bp.route('/mobile-app')
def mobile_app_page():
    return render_template('mobile_app.html')
    
@main_bp.route('/telderi5f932e1d02880a7a361463d87d31d143.txt')
def telderi_verification():
    return "Telderi", 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
@main_bp.route('/send-telegram', methods=['POST'])
def send_telegram():
    """Отправка сообщения в Telegram"""
    import requests
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    data = request.json
    
    # Новый токен бота
    bot_token = "8112079604:AAHzzoB53c7FIo-fs4gvpWUzAdmtW1YF9Z8"
    
    # Функция для получения chat_id из последних обновлений (автоматически)
    def get_chat_id_from_updates(bot_token):
        """Получает chat_id из последних обновлений бота"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                updates = response.json()
                if updates.get('ok') and updates.get('result'):
                    # Берем chat_id из последнего сообщения
                    for update in reversed(updates['result']):
                        if 'message' in update:
                            chat_id = update['message']['chat']['id']
                            logger.info(f"✅ Найден chat_id из обновлений: {chat_id}")
                            return str(chat_id)
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения chat_id: {e}")
            return None
    
    # Автоматически получаем chat_id из обновлений бота
    chat_id = get_chat_id_from_updates(bot_token)
    
    # Если не удалось получить, пробуем из переменной окружения (для обратной совместимости)
    if not chat_id:
        import os
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Если все еще не найден, возвращаем ошибку с инструкцией
    if not chat_id:
        logger.error("❌ chat_id не найден. Нужно чтобы кто-то написал боту /start")
        return jsonify({
            'success': False, 
            'error': 'Бот не настроен. Пожалуйста, напишите боту @helpdocscanbot команду /start, затем повторите отправку формы.'
        }), 400
    
    # Формируем текст сообщения
    subject_names = {
        'technical': 'Техническая проблема',
        'billing': 'Вопросы по оплате',
        'feature': 'Предложение по улучшению',
        'partnership': 'Сотрудничество',
        'other': 'Другое'
    }
    
    subject_display = subject_names.get(data.get('subject', ''), data.get('subject', 'Не указано'))
    
    text = f"""
📨 *НОВОЕ СООБЩЕНИЕ С САЙТА*

*👤 Имя:* {data.get('name', 'Не указано')}
*📧 Email:* {data.get('email', 'Не указано')}
*🎯 Тема:* {subject_display}

*💬 Сообщение:*
{data.get('message', 'Пустое сообщение')}
    """
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ Сообщение успешно отправлено в Telegram (chat_id: {chat_id})")
            return jsonify({'success': True})
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('description', 'Ошибка отправки в Telegram')
            logger.error(f"❌ Ошибка отправки в Telegram: {response.status_code} - {error_msg}")
            return jsonify({'success': False, 'error': f'Ошибка отправки: {error_msg}'}), response.status_code
            
    except Exception as e:
        logger.error(f"❌ Исключение при отправке в Telegram: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/favicon.ico')
def favicon():
    """Отдает фавикон для браузеров и поисковых систем"""
    return send_file('static/favicon.ico', mimetype='image/x-icon')
