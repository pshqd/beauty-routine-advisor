"""
Настройка логирования для приложения.
"""

import logging
import sys


def setup_logger(name: str) -> logging.Logger:
    """
    Настраивает и возвращает logger для модуля.
    
    Args:
        name (str): Имя модуля (обычно __name__)
    
    Returns:
        logging.Logger: Настроенный logger
    """
    logger = logging.getLogger(name)
    
    # Если уже настроен, возвращаем как есть
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    try:
        file_handler = logging.FileHandler('app.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Не удалось создать файл логов: {e}")
    
    return logger
