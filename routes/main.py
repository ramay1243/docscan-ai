from flask import Blueprint, render_template, request, jsonify
from utils.logger import RussianLogger
import logging

logger = logging.getLogger(__name__)

# Создаем Blueprint для главных маршрутов
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Главная страница с интерфейсом"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔍</text></svg>">
    <title>DocScan - AI анализ документов и договоров за 60 секунд</title>
    <meta name="description" content="Бесплатный анализ документов с AI. Проверка договоров на риски, выявление ошибок с помощью YandexGPT. Юридический анализ за 1 минуту">
    <meta name="keywords" content="анализ документов, проверка договоров, AI анализ, YandexGPT, юридический анализ, анализ рисков, проверка документов">
    <meta name="robots" content="index, follow">
    <meta name="author" content="DocScan">
    <style>
            * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; display: flex; justify-content: center; align-items: center; }
            .container { background: white; border-radius: 20px; padding: 40px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); max-width: 1000px; width: 100%; }
            .header { text-align: center; margin-bottom: 40px; }
            .logo { font-size: 3em; margin-bottom: 10px; }
            h1 { color: #2d3748; margin-bottom: 10px; font-size: 2.2em; }
            .subtitle { color: #718096; font-size: 1.2em; }
            .user-info { background: #edf2f7; padding: 15px; border-radius: 10px; margin: 20px 0; text-align: center; }
            .upload-zone { border: 3px dashed #cbd5e0; border-radius: 15px; padding: 60px 30px; text-align: center; margin: 30px 0; transition: all 0.3s ease; background: #f7fafc; cursor: pointer; }
            .upload-zone:hover { border-color: #667eea; background: #edf2f7; }
            .upload-icon { font-size: 4em; color: #667eea; margin-bottom: 20px; }
            .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 15px 40px; border-radius: 50px; font-size: 1.1em; cursor: pointer; transition: transform 0.2s ease; margin: 10px; }
            .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102,126,234,0.3); }
            .btn:disabled { background: #a0aec0; cursor: not-allowed; transform: none; box-shadow: none; }
            .file-info { background: #edf2f7; padding: 15px; border-radius: 10px; margin: 20px 0; }
            .loading { display: none; text-align: center; margin: 20px 0; }
            .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 20px; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .result { background: #f8fafc; border-radius: 15px; padding: 30px; margin-top: 30px; display: none; }
            .risk-item { background: white; padding: 15px; margin: 10px 0; border-radius: 10px; border-left: 4px solid #e53e3e; }
            .success-item { background: white; padding: 15px; margin: 10px 0; border-radius: 10px; border-left: 4px solid #48bb78; }
            .summary { background: #e6fffa; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #38a169; }
                    /* New Professional Sections */
            .section { padding: 80px 0; }
            .section-white { background: white; }
            .section-title { text-align: center; font-size: 2.5em; font-weight: 700; margin-bottom: 60px; color: #2d3748; }
            .steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 40px; margin-top: 40px; }
            .step { text-align: center; padding: 40px 20px; border-radius: 15px; background: #f7fafc; }
            .step-icon { font-size: 4em; margin-bottom: 20px; }
            .step h3 { font-size: 1.5em; font-weight: 600; margin-bottom: 15px; color: #2d3748; }
            .step p { color: #718096; line-height: 1.6; }
            
            .doc-types { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 40px; }
            .doc-type { background: #f7fafc; padding: 25px; border-radius: 12px; text-align: center; border-left: 4px solid #667eea; }
            .doc-type-icon { font-size: 2.5em; margin-bottom: 15px; }
            
            .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 30px; margin-top: 40px; }
            .pricing-card { background: white; padding: 40px 30px; border-radius: 20px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.1); border: 2px solid #e2e8f0; }
            .pricing-card.featured { border-color: #667eea; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .pricing-card.featured .price { color: white; }
            .pricing-card.featured .btn { background: white; color: #667eea; }
            .plan-name { font-size: 1.4em; font-weight: 700; margin-bottom: 15px; }
            .price { font-size: 2.5em; font-weight: 700; margin-bottom: 20px; color: #667eea; }
            .features { list-style: none; margin-bottom: 30px; text-align: left; }
            .features li { padding: 8px 0; border-bottom: 1px solid #e2e8f0; }
            .features li:last-child { border-bottom: none; }

                    /* FAQ Styles */
        .faq-container { max-width: 700px; margin: 0 auto; }
        .faq-item { margin-bottom: 15px; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .faq-question { background: white; padding: 20px 25px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-weight: 600; transition: background 0.3s; }
        .faq-question:hover { background: #f7fafc; }
        .faq-answer { background: white; padding: 0 25px; max-height: 0; overflow: hidden; transition: all 0.3s ease; }
        .faq-answer.open { padding: 20px 25px; max-height: 500px; }
        .faq-icon { font-size: 1.2em; font-weight: bold; transition: transform 0.3s; }
        .faq-item.active .faq-icon { transform: rotate(45deg); }
        
        /* Стили для умного анализа */
.risk-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
    margin: 2px;
}

.risk-critical { background: #fed7d7; color: #c53030; }
.risk-high { background: #feebc8; color: #dd6b20; }
.risk-medium { background: #fefcbf; color: #d69e2e; }
.risk-low { background: #c6f6d5; color: #38a169; }
.risk-info { background: #bee3f8; color: #3182ce; }

.expert-section {
    background: white;
    padding: 20px;
    margin: 15px 0;
    border-radius: 12px;
    border-left: 4px solid #667eea;
}

.recommendation-card {
    background: #f0fff4;
    padding: 15px;
    margin: 10px 0;
    border-radius: 8px;
    border-left: 4px solid #48bb78;
}

.alternative-card {
    background: #edf2f7;
    padding: 15px;
    margin: 10px 0;
    border-radius: 8px;
    border-left: 4px solid #4299e1;
}

.executive-summary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 25px;
    border-radius: 15px;
    margin: 20px 0;
}

.risk-meter {
    height: 8px;
    background: #e2e8f0;
    border-radius: 4px;
    margin: 10px 0;
    overflow: hidden;
}

.risk-meter-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
}
/* Бургер-меню с тремя полосками */
        .burger-menu {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
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
            background: #667eea;
            transform: scale(1.1);
        }

        .burger-line {
            width: 20px;
            height: 2px;
            background: #2d3748;
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
            color: #2d3748;
            transition: all 0.2s ease;
            border-bottom: 1px solid #f7fafc;
        }

        .menu-dropdown a:hover {
            background: #667eea;
            color: white;
        }

        .menu-dropdown a:last-child {
            border-bottom: none;
        }

        .menu-dropdown.show {
            display: block;
        }
        </style>
    </head>
    <body>
    <!-- Бургер-меню -->
    <div class="burger-menu">
        <div class="burger-icon" onclick="toggleMenu()">
            <div class="burger-line"></div>
            <div class="burger-line"></div>
            <div class="burger-line"></div>
        </div>
        <div class="menu-dropdown" id="menuDropdown">
            <a href="/articles">📚 Статьи</a>
            <a href="/contact">📞 Контакты</a>
        </div>
    </div>

    <div class="container">
    <div class="header">
        <div class="logo">🔍</div>
        <h1>DocScan - AI анализ документов</h1>
        <p class="subtitle" style="font-size: 1.3em; line-height: 1.5; max-width: 800px; margin: 20px auto 0 auto;">
            <strong>Проверяйте договоры, контракты и юридические документы на риски за 60 секунд</strong><br>
            🤖 YandexGPT анализирует текст и находит скрытые проблемы до того, как они станут дорогостоящими ошибками
        </p>
    </div>

            <div class="user-info" id="userInfo">
                <strong>👤 Ваш ID:</strong> <span id="userId">Загрузка...</span><br>
                <strong>📊 Анализов сегодня:</strong> <span id="usageInfo">0/1</span><br>
            </div>

            <div class="upload-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
                <div class="upload-icon">📄</div>
                <p><strong>Нажмите чтобы выбрать документ</strong></p>
                <p style="color: #718096; margin-top: 15px;">
    PDF, DOCX, TXT 
    <span style="color: #e53e3e; font-weight: bold;">• ФОТО (только для платных тарифов)</span>
    (до 10MB)
</p>
            </div>

            <input type="file" id="fileInput" style="display: none;" accept=".pdf,.docx,.txt,.jpg,.jpeg,.png,.webp" onchange="handleFileSelect(event)">
            
            <div class="file-info" id="fileInfo" style="display: none;">
                <strong>Выбран файл:</strong> <span id="fileName"></span>
            </div>

            <button class="btn" id="analyzeBtn" onclick="analyzeDocument()" disabled>Начать анализ</button>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Анализируем документ...</p>
            </div>

            <div class="result" id="result">
                <h3>✅ Анализ завершен</h3>
                <div id="resultContent"></div>
            </div>

            <div class="plans" style="margin-top: 40px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h3>💎 Выберите тариф</h3>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                    <div style="background: white; padding: 25px; border-radius: 15px; border: 2px solid #e53e3e; text-align: center;">
                        <div style="font-size: 1.3em; font-weight: bold; margin-bottom: 10px; color: #e53e3e;">Бесплатный</div>
                        <div style="font-size: 2em; font-weight: bold; color: #e53e3e; margin-bottom: 15px;">0₽</div>
                        <ul style="list-style: none; margin-bottom: 20px; text-align: left;">
                            <li style="padding: 5px 0;">✅ 1 анализ в день</li>
                            <li style="padding: 5px 0;">✅ AI-анализ YandexGPT</li>
                            <li style="padding: 5px 0;">✅ Все форматы файлов</li>
                        </ul>
                        <button class="btn" disabled style="background: #e53e3e;">Текущий тариф</button>
                    </div>
                    
                    <div style="background: #f0fff4; padding: 25px; border-radius: 15px; border: 2px solid #38a169; text-align: center;">
                        <div style="font-size: 1.3em; font-weight: bold; margin-bottom: 10px; color: #38a169;">Базовый</div>
                        <div style="font-size: 2em; font-weight: bold; color: #38a169; margin-bottom: 15px;">199₽/мес</div>
                        <ul style="list-style: none; margin-bottom: 20px; text-align: left;">
                            <li style="padding: 5px 0;">🚀 10 анализов в день</li>
                            <li style="padding: 5px 0;">🚀 Приоритетный AI-анализ</li>
                            <li style="padding: 5px 0;">🚀 Быстрая обработка</li>
                            <li style="padding: 5px 0;">📸 Распознавание фото документов</li>
                        </ul>
                        <button class="btn" onclick="buyPlan('basic')" style="background: #38a169;">Купить за 199₽</button>
                    </div>
                </div>
            </div>

        <script>
            let selectedFile = null;
            let currentUserId = null;

            // Загружаем или создаем ID пользователя
            function loadUser() {
                let savedId = localStorage.getItem('docscan_user_id');
                if (!savedId) {
                    // Создаем нового пользователя
                    fetch('/api/create-user', { method: 'POST' })
                        .then(r => r.json())
                        .then(data => {
                            if (data.success) {
                                currentUserId = data.user_id;
                                localStorage.setItem('docscan_user_id', currentUserId);
                                updateUserInfo();
                            }
                        });
                } else {
                    currentUserId = savedId;
                    updateUserInfo();
                }
            }

            function updateUserInfo() {
                if (!currentUserId) return;
                
                document.getElementById('userId').textContent = currentUserId;
                
                // Загружаем информацию об использовании
                fetch(`/api/usage?user_id=${currentUserId}`)
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('usageInfo').textContent = 
                            `${data.used_today}/${data.daily_limit}`;
                    });
            }

            function copyUserId() {
                navigator.clipboard.writeText(currentUserId);
                alert('ID скопирован: ' + currentUserId);
            }

            function generateNewId() {
                if (confirm('Создать новый ID? Текущая статистика будет сброшена.')) {
                    fetch('/api/create-user', { method: 'POST' })
                        .then(r => r.json())
                        .then(data => {
                            if (data.success) {
                                currentUserId = data.user_id;
                                localStorage.setItem('docscan_user_id', currentUserId);
                                updateUserInfo();
                                alert('Новый ID создан: ' + currentUserId);
                            }
                        });
                }
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
                if (!selectedFile || !currentUserId) return;

                document.getElementById('loading').style.display = 'block';
                document.getElementById('analyzeBtn').disabled = true;

                try {
                    const formData = new FormData();
                    formData.append('file', selectedFile);
                    formData.append('user_id', currentUserId);

                    const response = await fetch('/api/analyze', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();

                    document.getElementById('loading').style.display = 'none';

                    if (data.success) {
                        showResult(data);
                        updateUserInfo(); // Обновляем статистику
                    } else {
                        alert('Ошибка: ' + data.error);
                        document.getElementById('analyzeBtn').disabled = false;
                    }

                } catch (error) {
                    document.getElementById('loading').style.display = 'none';
                    
                    if (error.message.includes('402')) {
                        alert('❌ Бесплатный лимит исчерпан!\\n\\nСегодня вы использовали 1/1 бесплатный анализ.\\n\\n💎 Перейдите на платный тариф для продолжения.');
                    } else {
                        alert('Ошибка соединения: ' + error.message);
                    }
                    
                    document.getElementById('analyzeBtn').disabled = false;
                }
            }

            function showResult(data) {
    const resultDiv = document.getElementById('result');
    const resultContent = document.getElementById('resultContent');
    
    resultContent.innerHTML = createSmartAnalysisHTML(data);
    resultDiv.style.display = 'block';
    resultDiv.scrollIntoView({ behavior: 'smooth' });
}

function createSmartAnalysisHTML(data) {
    const analysis = data.result;
    
    return `
        <!-- Заголовок и сводка -->
        <div class="executive-summary">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="margin: 0; color: white;">${analysis.document_type_name}</h3>
                    <p style="margin: 5px 0; opacity: 0.9;">${analysis.executive_summary.risk_icon} ${analysis.executive_summary.risk_description}</p>
                </div>
                <div style="text-align: right;">
                    <div class="risk-badge risk-${analysis.executive_summary.risk_level.toLowerCase()}" 
                         style="font-size: 16px; padding: 8px 16px;">
                        ${analysis.executive_summary.risk_level}
                    </div>
                </div>
            </div>
            
            <div class="risk-meter">
                <div class="risk-meter-fill" style="width: ${getRiskMeterWidth(analysis.executive_summary.risk_level)}%; 
                     background: ${analysis.executive_summary.risk_color};">
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 15px;">
                ${analysis.executive_summary.quick_facts.map(fact => 
                    `<div style="text-align: center; background: rgba(255,255,255,0.2); padding: 8px; border-radius: 6px;">
                        ${fact}
                    </div>`
                ).join('')}
            </div>
            
            <div style="margin-top: 15px; padding: 12px; background: rgba(255,255,255,0.1); border-radius: 8px;">
                <strong>💡 Решение:</strong> ${analysis.executive_summary.decision_support}
            </div>
        </div>

        <!-- Экспертная оценка -->
        <div class="expert-section">
            <h4>🧑‍⚖️ Юридическая экспертиза</h4>
            <p>${analysis.expert_analysis.legal_expertise}</p>
        </div>

        <div class="expert-section">
            <h4>💰 Финансовый анализ</h4>
            <p>${analysis.expert_analysis.financial_analysis}</p>
        </div>

        <div class="expert-section">
            <h4>⚙️ Операционные риски</h4>
            <p>${analysis.expert_analysis.operational_risks}</p>
        </div>

        <div class="expert-section">
            <h4>🎯 Стратегическая оценка</h4>
            <p>${analysis.expert_analysis.strategic_assessment}</p>
        </div>

        <!-- Детальные риски -->
        <div class="expert-section">
            <h4>⚠️ Ключевые риски</h4>
            <div style="margin: 10px 0;">
                <strong>Статистика:</strong> ${analysis.risk_analysis.risk_summary}
            </div>
            ${analysis.risk_analysis.key_risks.map(risk => `
                <div style="background: ${risk.color}20; padding: 12px; margin: 8px 0; border-radius: 8px; border-left: 4px solid ${risk.color};">
                    <div style="display: flex; justify-content: between; align-items: center;">
                        <span class="risk-badge risk-${risk.level.toLowerCase()}">
                            ${risk.icon} ${risk.level}
                        </span>
                        <strong style="flex-grow: 1; margin-left: 10px;">${risk.title}</strong>
                    </div>
                    <p style="margin: 8px 0 0 0; color: #4a5568;">${risk.description}</p>
                </div>
            `).join('')}
        </div>

        <!-- Практические рекомендации -->
        <div class="expert-section">
            <h4>✅ Практические рекомендации</h4>
            ${analysis.recommendations.practical_actions.map(rec => `
                <div class="recommendation-card">
                    <div style="display: flex; justify-content: between; margin-bottom: 8px;">
                        <strong>📝 ${rec.action}</strong>
                        <span style="background: #48bb78; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">
                            ${rec.urgency}
                        </span>
                    </div>
                    <p style="margin: 0; color: #2d3748;"><strong>Эффект:</strong> ${rec.effect}</p>
                </div>
            `).join('')}
        </div>

        <!-- Альтернативные решения -->
        ${analysis.recommendations.alternative_solutions && analysis.recommendations.alternative_solutions.length > 0 ? `
        <div class="expert-section">
            <h4>🔄 Альтернативные решения</h4>
            ${analysis.recommendations.alternative_solutions.map(sol => `
                <div class="alternative-card">
                    <strong>💡 ${sol.solution}</strong>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px;">
                        <div style="background: #c6f6d5; padding: 8px; border-radius: 6px;">
                            <strong>👍 Преимущества:</strong><br>${sol.advantages}
                        </div>
                        <div style="background: #fed7d7; padding: 8px; border-radius: 6px;">
                            <strong>👎 Недостатки:</strong><br>${sol.disadvantages}
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
        ` : ''}

        <!-- Приоритетные действия -->
        ${analysis.recommendations.priority_actions && analysis.recommendations.priority_actions.length > 0 ? `
        <div class="expert-section" style="border-left-color: #e53e3e;">
            <h4>🚀 Приоритетные действия</h4>
            ${analysis.recommendations.priority_actions.map(action => `
                <div style="background: #fed7d7; padding: 12px; margin: 8px 0; border-radius: 8px;">
                    <strong>🔴 ${action.action}</strong>
                    <p style="margin: 5px 0 0 0;">${action.effect}</p>
                </div>
            `).join('')}
        </div>
        ` : ''}
    `;
}

function getRiskMeterWidth(riskLevel) {
    const levels = { 'CRITICAL': 100, 'HIGH': 75, 'MEDIUM': 50, 'LOW': 25, 'INFO': 10 };
    return levels[riskLevel] || 50;
}

            // Загружаем пользователя при старте
        loadUser();

                    // FAQ Accordion
            function toggleFAQ(number) {
                const answer = document.getElementById('faq-answer-' + number);
                const item = answer.parentElement;
                
                // Close all other FAQs
                document.querySelectorAll('.faq-answer').forEach(faq => {
                    if (faq.id !== 'faq-answer-' + number) {
                        faq.classList.remove('open');
                        faq.parentElement.classList.remove('active');
                    }
                });
                
                // Toggle current FAQ
                answer.classList.toggle('open');
                item.classList.toggle('active');
            }

        // 🔐 ФУНКЦИЯ ДЛЯ ПОКУПКИ ТАРИФОВ
        async function buyPlan(planType) {
            if (!currentUserId) {
                alert('Сначала загрузите страницу');
                return;
            }
            
            try {
                const response = await fetch('/payments/create-payment', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user_id: currentUserId,
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
        }
        // Функции для бургер-меню
            function toggleMenu() {
                const dropdown = document.getElementById('menuDropdown');
                dropdown.classList.toggle('show');
            }

            // Закрывать меню при клике вне его
            document.addEventListener('click', function(event) {
                const menu = document.querySelector('.burger-menu');
                const dropdown = document.getElementById('menuDropdown');
                
                if (!menu.contains(event.target)) {
                    dropdown.classList.remove('show');
                }
            });

    </script>
                                              <!-- How it Works Section -->
            <div style="background: white; padding: 80px 0; text-align: center;">
                <div style="max-width: 1000px; margin: 0 auto; padding: 0 20px;">
                    <h2 style="font-size: 2.5em; margin-bottom: 60px; color: #2d3748;">Как это работает?</h2>
                    <div style="display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;">
                        <div class="step">
                            <div class="step-icon">📄</div>
                            <h3>Загрузите документ</h3>
                            <p>Загрузите договор в формате PDF, Word или текстовый файл</p>
                        </div>
                        <div class="step">
                            <div class="step-icon">🤖</div>
                            <h3>AI анализирует риски</h3>
                            <p>YandexGPT проверяет каждую строку документа на потенциальные риски</p>
                        </div>
                        <div class="step">
                            <div class="step-icon">📊</div>
                            <h3>Получите отчет</h3>
                            <p>Получите понятный список рисков и конкретные рекомендации</p>
                        </div>
                    </div>
                </div>
            </div>

                       <!-- Document Types Carousel -->
<div style="background: #f7fafc; padding: 60px 0;">
    <div style="max-width: 1000px; margin: 0 auto; padding: 0 20px;">
        <h3 style="text-align: center; margin-bottom: 40px; font-size: 1.8em; color: #2d3748;">
            Какие документы можно проверить?
        </h3>
        
        <!-- Упрощенная карусель -->
        <div class="simple-carousel">
            <div class="carousel-wrapper">
                <div class="carousel-items" id="carouselItems">
                    <!-- Элементы будут добавлены через JS -->
                </div>
            </div>
            <div class="carousel-controls">
                <button class="carousel-control prev" onclick="scrollCarousel(-300)">‹</button>
                <button class="carousel-control next" onclick="scrollCarousel(300)">›</button>
            </div>
        </div>
        
        <p style="text-align: center; margin-top: 30px; color: #718096; font-size: 1.1em;">
            <strong>И любые другие текстовые документы!</strong> AI анализирует суть, а не формат.
        </p>
    </div>
</div>

<style>
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
    border-left: 4px solid #667eea;
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
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
}

.carousel-icon {
    font-size: 2.5em;
    margin-bottom: 15px;
}

.carousel-card h4 {
    margin: 0;
    font-size: 1em;
    color: #2d3748;
    font-weight: 600;
    text-align: center;
}

.carousel-controls {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 20px;
}

.carousel-control {
    background: #667eea;
    color: white;
    border: none;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    font-size: 1.5em;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
}

.carousel-control:hover {
    background: #5a67d8;
    transform: scale(1.1);
}

@media (max-width: 768px) {
    .carousel-item {
        width: 160px;
    }
    
    .carousel-card {
        height: 130px;
        padding: 20px 10px;
    }
}
</style>

<script>
// Данные для карусели
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

// Инициализация карусели
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

// Прокрутка карусели
function scrollCarousel(distance) {
    const container = document.getElementById('carouselItems');
    container.scrollLeft += distance;
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', initCarousel);
</script>
            <!-- FAQ Section -->
            <div style="background: #f7fafc; padding: 80px 0;">
                <div style="max-width: 800px; margin: 0 auto; padding: 0 20px;">
                    <h2 style="text-align: center; font-size: 2.5em; margin-bottom: 60px; color: #2d3748;">Частые вопросы</h2>
                    
                    <div class="faq-container">
                        <!-- Question 1 -->
                        <div class="faq-item">
                            <div class="faq-question" onclick="toggleFAQ(1)">
                                <span>🤔 Какой максимальный размер файла?</span>
                                <span class="faq-icon">+</span>
                            </div>
                            <div class="faq-answer" id="faq-answer-1">
                                <p>Максимальный размер файла - 10MB. Поддерживаются форматы: PDF, DOCX, TXT.</p>
                            </div>
                        </div>
                        
                        <!-- Question 2 -->
                        <div class="faq-item">
                            <div class="faq-question" onclick="toggleFAQ(2)">
                                <span>💰 Сколько стоит анализ?</span>
                                <span class="faq-icon">+</span>
                            </div>
                            <div class="faq-answer" id="faq-answer-2">
                                <p>1 анализ в день - бесплатно. Платные тарифы: Базовый (10 анализов в день) - 199₽/мес, Премиум (50 анализов) - 399₽/мес.</p>
                            </div>
                        </div>
                        
                        <!-- Question 3 -->
                        <div class="faq-item">
                            <div class="faq-question" onclick="toggleFAQ(3)">
                                <span>🔒 Конфиденциальны ли мои документы?</span>
                                <span class="faq-icon">+</span>
                            </div>
                            <div class="faq-answer" id="faq-answer-3">
                                <p>Да! Документы не сохраняются на наших серверах. После анализа файлы автоматически удаляются. Текст передается в Yandex Cloud API по защищенному соединению.</p>
                            </div>
                        </div>
                        
                        <!-- Question 4 -->
                        <div class="faq-item">
                            <div class="faq-question" onclick="toggleFAQ(4)">
                                <span>⏱️ Сколько времени занимает анализ?</span>
                                <span class="faq-icon">+</span>
                            </div>
                            <div class="faq-answer" id="faq-answer-4">
                                <p>Обычно анализ занимает 30-60 секунд. Скорость зависит от размера документа и загрузки сервера YandexGPT.</p>
                            </div>
                        </div>
                        
                        <!-- Question 5 -->
                        <div class="faq-item">
                            <div class="faq-question" onclick="toggleFAQ(5)">
                                <span>🤖 Насколько точен AI-анализ?</span>
                                <span class="faq-icon">+</span>
                            </div>
                            <div class="faq-answer" id="faq-answer-5">
                                <p>YandexGPT хорошо справляется с выявлением типовых рисков в договорах. Однако это инструмент для первичной проверки - для важных документов рекомендуем консультацию с юристом.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
        <!-- ФУТЕР -->
        <div style="width: 100%; text-align: center; padding: 30px 0; color: #718096; border-top: 1px solid #e2e8f0; margin-top: 50px; background: white;">
            <div style="max-width: 1000px; margin: 0 auto; padding: 0 20px;">
                <div style="margin-bottom: 15px;">
                    <a href="/terms" style="color: #718096; text-decoration: none; margin: 0 15px; font-size: 14px;">Пользовательское соглашение</a>
                    <a href="/privacy" style="color: #718096; text-decoration: none; margin: 0 15px; font-size: 14px;">Политика конфиденциальности</a>
                    <a href="/offer" style="color: #718096; text-decoration: none; margin: 0 15px; font-size: 14px;">Публичная оферта</a>
                    <a href="mailto:docscanhelp@gmail.com?subject=Вопрос по DocScan" style="color: #718096; text-decoration: none; margin: 0 15px; font-size: 14px;" target="_blank">Техподдержка</a>
                </div>
                <div style="font-size: 14px;">
                    © 2025 DocScan. Все права защищены.
                </div>
            </div>
        </div>

    </body>
</html>
    """

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
    """Sitemap для SEO"""
    base_url = "https://docscan-ekjj.onrender.com"
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{base_url}/</loc>
        <lastmod>2024-11-22</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{base_url}/terms</loc>
        <lastmod>2024-11-22</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
    <url>
        <loc>{base_url}/privacy</loc>
        <lastmod>2024-11-22</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
    <url>
        <loc>{base_url}/offer</loc>
        <lastmod>2024-11-22</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
</urlset>''', 200, {'Content-Type': 'application/xml'}

@main_bp.route('/robots.txt')
def robots():
    """Robots.txt для SEO"""
    return """User-agent: *
Allow: /
Disallow: /admin
Disallow: /admin-login

Sitemap: https://docscan-ekjj.onrender.com/sitemap.xml""", 200, {'Content-Type': 'text/plain'}

@main_bp.route('/articles')
def articles():
    """Страница со списком всех статей"""
    return render_template('articles.html')

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


