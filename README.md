# SkinCare Advisor Chat

AI-агент для персональных консультаций по уходу за кожей на основе RAG + LLM.

## Описание

Веб-приложение с чат-интерфейсом, где AI-агент задаёт уточняющие вопросы о типе кожи, а затем предоставляет персональные рекомендации на основе базы знаний (RAG система с ChromaDB).

**Для кого:** люди, интересующиеся правильным уходом за кожей.

## Команда

- **pshqd** (ML Backend + Тимлид) — Flask API, RAG система, LM Studio интеграция
- **Участник 2** (Knowledge Base + DevOps) — Markdown база знаний, Docker
- **Участник 3** (Frontend) — HTML/CSS/JS интерфейс чата

## Стек технологий

### Backend

- Python 3.11+ (управление через uv)
- Flask — веб-фреймворк
- Flask-CORS — поддержка CORS
- ChromaDB — векторная база данных для RAG
- sentence-transformers — генерация эмбеддингов (`intfloat/multilingual-e5-small`)
- LM Studio — локальный LLM (совместимый с OpenAI API)
- python-frontmatter — парсинг YAML-метаданных MD-файлов
- langchain-text-splitters — нарезка текста по заголовкам

### Frontend

- -

### DevOps

- Docker + docker-compose
- Git/GitHub (ветки `main` / `dev`)

## Зависимости

Полный список зависимостей — в файле `app/requirements.txt`.

Основные пакеты:

```text
flask>=3.0.0
flask-cors>=4.0.0
chromadb>=0.4.22
sentence-transformers>=2.3.1
requests>=2.31.0
python-frontmatter>=1.1.0
langchain-text-splitters>=0.2.0
```

## Установка и запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/pshqd/beauty-routine-advisor.git
cd beauty-routine-advisor/app
```

### 2. Установить пакет в режиме разработки

```bash
pip install -e .
```

### 3. Проиндексировать базу знаний

```bash
python init_kb.py
```

### 4. Запустить LM Studio

Запустить LM Studio, загрузить любую модель и включить Local Server на порту `1234`.

### 5. Запустить сервер

```bash
python app.py
```

Приложение будет доступно по адресу: `http://localhost:5000`

## Тестирование

```bash
pip install -e ".[dev]"
pytest -v
```

## Документация

Документация генерируется через Sphinx:

```bash
cd docs/sphinx
make html
```

Открыть: `docs/sphinx/_build/html/index.html`

## Установка dev зависимостей

```bash
uv sync --extra dev
```

## Открыть документацию

```bash
cd ../docs/sphinx
make html
open _build/html/index.html
```
