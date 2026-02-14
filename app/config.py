"""
Конфигурация приложения.
Все настройки проекта в одном месте.
"""

import os


class Config:
    """Базовая конфигурация приложения."""
    
    VERSION = "0.1.0"
    DEBUG = True
    HOST = "0.0.0.0"
    PORT = 5000
    
    LM_STUDIO_URL = os.getenv(
        "LM_STUDIO_URL", 
        "http://localhost:1234/v1/chat/completions"
    )
    LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "local-model")
    
    GENERATION_CONFIG = {
        "temperature": 0.7,
        "max_tokens": 500,
        "top_p": 0.9,
        "timeout": 30  # секунды
    }
    
    # ===== RAG НАСТРОЙКИ (для Недели 2) =====
    KNOWLEDGE_BASE_PATH = "knowledge_base"
    EMBEDDINGS_DB_PATH = "embeddings_db"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    TOP_K_RESULTS = 2  # Количество релевантных секций из RAG
    
    # ===== ЛОГИРОВАНИЕ =====
    LOG_LEVEL = "INFO"
    LOG_FILE = "app.log"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class DevelopmentConfig(Config):
    """Конфигурация для разработки."""
    DEBUG = True


class ProductionConfig(Config):
    """Конфигурация для продакшена."""
    DEBUG = False
    LOG_LEVEL = "WARNING"


# Выбор конфигурации по переменной окружения
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
