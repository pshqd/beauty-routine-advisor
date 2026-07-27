"""
SkinCare Advisor - Main Application
Главный модуль Flask приложения.
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import time

from config import Config
from utils.logger import setup_logger, RequestLogger
from utils.metrics import metrics
from services.llm_service import LLMService

# ===== ИНИЦИАЛИЗАЦИЯ =====

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, resources={r"/api/*": {"origins": "*"}})

logger = setup_logger(__name__)
llm_service = LLMService()


# ===== MIDDLEWARE =====

@app.before_request
def _before_request():
    request._start_time = time.perf_counter()


@app.after_request
def _after_request(response):
    latency_ms = round((time.perf_counter() - request._start_time) * 1000, 2)
    endpoint = request.endpoint or "unknown"

    metrics.inc("http_requests_total")
    metrics.inc(f"http_requests_{response.status_code}")
    metrics.observe("http_latency_ms", latency_ms)

    logger.info(
        f"{request.method} {request.path} → {response.status_code} [{latency_ms}ms]",
        extra={
            "event": "http_request",
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "latency_ms": latency_ms,
            "endpoint": endpoint,
        }
    )
    return response


# ===== FRONTEND ROUTES =====

@app.route("/")
def index():
    """  Главная страница приложения."""
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return "", 204


# ===== API ROUTES =====


@app.route("/api/health", methods=["GET"])
def health_check():
    """Проверка работоспособности API."""
    return (
        jsonify({
            "status": "ok",
            "message": "SkinCare Advisor API is running",
            "timestamp": datetime.now().isoformat(),
            "version": app.config["VERSION"],
        }),
        200,
    )


@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """
    Runtime-метрики приложения.

    Returns:
        JSON: {
            "uptime_seconds": float,
            "counters": {"http_requests_total": int, "chat_requests_total": int, ...},
            "histograms": {"http_latency_ms": {"mean": ..., "p95": ..., ...}, ...}
        }
    """
    return jsonify(metrics.snapshot()), 200


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Основной endpoint для диалога с AI-агентом.

    Request JSON:
        {"message": str, "conversation_history": list (optional)}

    Returns:
        JSON: Ответ от AI-агента
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Missing 'message' field"}), 400

        user_message = data["message"].strip()
        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        conversation_history = data.get("conversation_history", [])

        metrics.inc("chat_requests_total")

        with RequestLogger(
            logger,
            "POST /api/chat",
            message_len=len(user_message),
        ) as rl:
            response = llm_service.generate_response(
                user_message=user_message,
                conversation_history=conversation_history,
            )
            rl.set_extra(
                sources_count=len(response.get("sources", [])),
                response_len=len(response.get("response", "")),
            )

        metrics.inc("chat_requests_success")
        return jsonify(response), 200

    except Exception as e:
        metrics.inc("chat_requests_error")
        logger.error(f"Ошибка в /api/chat: {str(e)}", exc_info=True)

        if "402" in str(e):
            return jsonify({"response": "💳 Закончились кредиты. Попробуйте позже.", "sources": []}), 200
        if "404" in str(e):
            return jsonify({"response": "⚙️ Модель недоступна.", "sources": []}), 200
        if "429" in str(e) or "403" in str(e):
            return jsonify({"response": "⏳ Сервер перегружен. Попробуйте через 15 секунд.", "sources": []}), 200

        return jsonify({"error": "Internal server error", "details": str(e) if app.debug else None}), 500


# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 ошибка: {error}")
    return jsonify({"error": "Internal server error"}), 500


# ===== MAIN =====

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 Запуск SkinCare Advisor API")
    logger.info(f"📍 URL: http://localhost:{app.config['PORT']}")
    logger.info(f"🔧 Debug: {app.config['DEBUG']}")
    logger.info("=" * 60)

    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
