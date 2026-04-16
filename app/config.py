"""
Конфигурация приложения.
Все настройки проекта в одном месте.
"""

import os
from pathlib import Path 
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent  

load_dotenv()

class Config:
    """Базовая конфигурация приложения."""
    
    VERSION = "0.1.0"
    DEBUG = True
    HOST = "0.0.0.0"
    PORT = 8080
    
    LM_STUDIO_URL = os.getenv(
        "LM_STUDIO_URL", 
        "http://localhost:1234/v1/chat/completions"
    )
    LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "local-model")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gigachat")  # lm_studio | gigachat | openrouter

    GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS", "") 
    GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")  # или _CORP
    GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat 2")

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct")
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    GENERATION_CONFIG = {
        "temperature": 0.7,
        "max_tokens": 500,
        "top_p": 0.9,
        "timeout": 30  # секунды
    }
    
    # ===== RAG НАСТРОЙКИ  =====
    KNOWLEDGE_BASE_PATH = BASE_DIR / "knowledge_base"
    EMBEDDINGS_DB_PATH = BASE_DIR / "embeddings_db"
    EMBEDDING_MODEL = "deepvk/USER-base"   
    TOP_K_RESULTS = 2  # Количество релевантных секций из RAG
    COLLECTION_KB = "skincare_kb" 
    FAISS_INDEX_PATH = BASE_DIR / "embeddings_db"
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
