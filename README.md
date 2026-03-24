# 💆‍♀️ SkinCare Advisor Chat

AI-агент для персональных консультаций по уходу за кожей.

## 🎯 Описание

Веб-приложение с чат-интерфейсом, где AI-агент задает уточняющие вопросы

о типе кожи и проблемах, затем предоставляет персональные рекомендации

на основе базы знаний (RAG система).

## 👥 Команда

- **pshqd** (ML Backend + Тимлид) - Flask API, RAG система, LM Studio
- **Участник 2** (Knowledge Base + DevOps) - Markdown файлы, Docker
- **Участник 3** (Frontend)

## 🛠 Стек технологий

### Backend

- Python 3.11+ (управление через uv)
- Flask — веб-фреймворк
- ChromaDB — векторная база данных
- sentence-transformers — эмбеддинги
- LM Studio — локальный LLM

### Frontend

- pass

### DevOps

- Docker + docker-compose
- Git/GitHub

## 📦 Установка и запуск

```bash
cd backend

# Установка зависимостей через uv
uv sync

# Индексация базы знаний (после создания MD файлов)  
uv run python init_kb.py

# Запуск Flask сервера
uv run python app.py
```

## Сборка для практической работы №2

| Цель                           | setup.py (старый)       | pyproject.toml (новый)          |
| ------------------------------ | ----------------------- | ------------------------------- |
| Установить зависимости + пакет | python setup.py install | pip install .                   |
| Dev-режим (editable)           | python setup.py develop | pip install -e .                |
| Только зависимости             | —                       | pip install -r requirements.txt |
