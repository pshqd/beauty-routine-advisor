"""
SkinCare Advisor - Main Application
Главный модуль Flask приложения.

Автор: Участник 1 (ML Backend Engineer)
Дата: 14 февраля 2026
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime

from config import Config
from utils.logger import setup_logger
from services.llm_service import LLMService

# ===== ИНИЦИАЛИЗАЦИЯ =====

app = Flask(__name__)
app.config.from_object(Config)

# CORS для frontend
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Логирование
logger = setup_logger(__name__)

# Сервисы
llm_service = LLMService()

# ===== FRONTEND ROUTES =====

@app.route('/')
def index():
    """Главная страница приложения."""
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    """Заглушка для favicon."""
    return '', 204


# ===== API ROUTES =====

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Проверка работоспособности API.
    
    Returns:
        JSON: Статус API
    """
    return jsonify({
        "status": "ok",
        "message": "SkinCare Advisor API is running",
        "timestamp": datetime.now().isoformat(),
        "version": app.config['VERSION']
    }), 200


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Основной endpoint для диалога с AI-агентом.
    
    Request JSON:
        {
            "message": str,
            "conversation_history": list (optional)
        }
    
    Returns:
        JSON: Ответ от AI-агента
    """
    try:
        # Валидация
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field"}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        conversation_history = data.get('conversation_history', [])
        
        logger.info(f"📩 Получено сообщение: {user_message[:50]}...")
        
        # Вызов сервиса LLM
        response = llm_service.generate_response(
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Ошибка в /api/chat: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e) if app.debug else None
        }), 500


# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    """Обработчик 404 ошибки."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Обработчик 500 ошибки."""
    logger.error(f"500 ошибка: {error}")
    return jsonify({"error": "Internal server error"}), 500


# ===== MAIN =====

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🚀 Запуск SkinCare Advisor API")
    logger.info(f"📍 URL: http://localhost:{app.config['PORT']}")
    logger.info(f"🔧 Debug: {app.config['DEBUG']}")
    logger.info("=" * 60)
    
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
