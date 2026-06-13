# SkinCare Advisor

AI-консультант по уходу за кожей на основе RAG-архитектуры. Отвечает на вопросы о типах кожи, уходовых рутинах и косметических ингредиентах, опираясь на внутреннюю базу знаний в Markdown и локальный FAISS-индекс.

## Стек

| Слой | Технология |
|---|---|
| Backend | Flask + Flask-CORS |
| LLM | GigaChat / OpenRouter / LM Studio (через единый provider abstraction) |
| Embeddings | `ai-forever/FRIDA` |
| Vector Store | FAISS через LangChain |
| Chunking | `MarkdownHeaderTextSplitter` + `RecursiveCharacterTextSplitter` |
| Knowledge Base | Markdown + YAML frontmatter через `python-frontmatter` |
| Тесты | pytest + pytest-cov |
| Линтер | flake8 |
| Форматтер | black |
| Документация | Sphinx + autodoc |
| Пакетный менеджер | uv |

## Возможности

- Ответы с опорой на внутреннюю базу знаний, а не только на LLM.
- Хранение знаний в Markdown-файлах с YAML frontmatter.
- Разбиение документов на смысловые чанки по заголовкам `#`, `##`, `###`.
- Индексация в локальный FAISS-индекс для быстрого retrieval.
- Возврат источников RAG в ответе API.
- Поддержка нескольких LLM-провайдеров (GigaChat, OpenRouter, LM Studio) через единый сервисный слой.
- Пост-фильтрация результатов retrieval по `skin_type` из метаданных.

## Структура проекта

```text
beauty-routine-advisor/
├── Makefile
├── README.md
├── Dockerfile
├── docker-compose.yml
└── app/
    ├── app.py                  # Flask-приложение, маршруты
    ├── config.py               # Конфигурация через классы Dev/Prod
    ├── init_kb.py              # Скрипт индексации knowledge base
    ├── .env.example            # Шаблон переменных окружения
    ├── pyproject.toml          # Зависимости проекта
    ├── services/
    │   ├── llm_service.py      # Оркестратор: RAG → промпт → LLM
    │   ├── rag_service.py      # FAISS поиск + пост-фильтрация
    │   └── providers/
    │       ├── base.py         # Абстрактный провайдер
    │       ├── openrouter.py   # OpenRouter API
    │       └── gigachat.py     # Sber GigaChat API
    ├── knowledge_base/
    │   └── skincare_kb/        # Markdown-документы базы знаний
    ├── embeddings_db/          # FAISS-индекс (генерируется при init-kb)
    ├── notebooks/              # EDA и eval-ноутбуки
    ├── artifacts/              # CSV и JSON с метриками retrieval
    ├── templates/
    │   └── index.html          # Frontend чата
    ├── static/
    │   ├── css/style.css
    │   └── js/chat.js
    ├── tests/                  # pytest-тесты
    ├── utils/
    │   └── logger.py           # Настройка структурированного логирования
    └── docs/
        └── sphinx/             # Sphinx-документация (make docs)
```

Рабочая часть проекта находится в каталоге `app/`, а `Makefile` лежит в корне и запускает команды относительно этой структуры.

## Быстрый старт

### Клонирование

```bash
git clone https://github.com/pshqd/beauty-routine-advisor.git
cd beauty-routine-advisor
```

### Установка зависимостей

```bash
make install
```

Команда устанавливает зависимости через `uv`. Для dev-инструментов (pytest, flake8, black):

```bash
make install-dev
```

### Настройка `.env`

Скопируй шаблон и заполни нужные переменные:

```bash
cp app/.env.example app/.env
```

Минимальный набор для запуска с GigaChat:

```env
LLM_PROVIDER=gigachat
GIGACHAT_CREDENTIALS=your_base64_credentials
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_MODEL=GigaChat 2
```

Для OpenRouter:

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=google/gemma-3-27b-it:free
```

Для локального LM Studio:

```env
LLM_PROVIDER=lm_studio
LM_STUDIO_URL=http://localhost:1234/v1/chat/completions
LM_STUDIO_MODEL=local-model
```

Дополнительные параметры (необязательны, есть дефолты в `config.py`):

```env
HOST=0.0.0.0
PORT=8080
DEBUG=true
VERSION=0.1.0
```

> ⚠️ Никогда не коммить `app/.env` — он в `.gitignore`. В репо хранится только `app/.env.example`.

### Индексация knowledge base

```bash
make init-kb
```

Команда запускает `app/init_kb.py`: читает Markdown-документы из `app/knowledge_base/skincare_kb/`, извлекает YAML frontmatter, режет текст на чанки по заголовкам и строит FAISS-индекс в `app/embeddings_db/`. Модель эмбеддингов — `ai-forever/FRIDA`.

### Запуск приложения

```bash
make run
```

Сервер запускается на `http://localhost:8080`. Flask dev-режим с autoreload включён.

После запуска:

- Веб-чат: `http://localhost:8080/`
- Health check: `http://localhost:8080/api/health`
- API chat: `http://localhost:8080/api/chat` (POST)

### Запуск в Docker

```bash
docker build -t skincare-advisor .
docker run -p 8080:8080 --env-file app/.env skincare-advisor
```

Или через docker-compose:

```bash
docker-compose up --build
```

## Make-команды

### Разработка

```bash
make install        # установка зависимостей через uv
make install-dev    # установка dev-зависимостей
make run            # запуск Flask backend на порту 8080
make init-kb        # переиндексация knowledge base в FAISS
```

### Тесты

```bash
make test           # быстрый запуск тестов
make test-v         # запуск тестов с подробным выводом
make test-cov       # запуск тестов с coverage-отчётом
```

### Качество кода

```bash
make lint           # проверка кода через flake8
make format         # форматирование через black
make format-check   # проверка форматирования без изменений
make check          # CI-команда: lint + format-check
```

### Документация

```bash
make docs           # сборка Sphinx HTML-документации
make docs-clean     # очистка собранной документации
```

После сборки документация доступна в `app/docs/sphinx/build/html/index.html`.

### Очистка

```bash
make clean          # удаляет __pycache__, .pyc, .pytest_cache, .coverage
```

## API

### `GET /api/health`

Проверка статуса backend.

Пример ответа:

```json
{
  "status": "ok",
  "message": "SkinCare Advisor API is running",
  "timestamp": "2026-06-13T18:00:00",
  "version": "0.1.0"
}
```

### `POST /api/chat`

Основной endpoint чата. Принимает сообщение пользователя и опциональную историю диалога. Внутри выполняет RAG-поиск по FAISS-индексу, формирует контекстный промпт и обращается к сконфигурированному LLM-провайдеру.

Запрос:

```json
{
  "message": "У меня жирная кожа и акне, что делать?",
  "conversation_history": []
}
```

Ответ:

```json
{
  "response": "## Уход за жирной кожей\n\n- Используйте мягкое очищение\n- Не пересушивайте кожу\n- Добавьте SPF\n",
  "sources": [
    "02_oily_skin.md › Утренний уход",
    "01_acne_and_post_acne.md › Базовые рекомендации"
  ]
}
```

Коды ответа: `200` (успех), `400` (нет поля `message` или пустое тело), `500` (внутренняя ошибка).

Примеры curl:

```bash
# Health check
curl http://localhost:8080/api/health

# Запрос к чату
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Как ухаживать за сухой кожей?"}'
```

## Конфигурация

Все параметры задаются через переменные окружения в `app/.env`. Логика разбита на классы:

- `Config` — базовые дефолты
- `DevelopmentConfig` — `DEBUG=True`
- `ProductionConfig` — `DEBUG=False`, `LOG_LEVEL=WARNING`

Ключевые параметры RAG из `config.py`:

| Параметр | Дефолт | Описание |
|---|---|---|
| `EMBEDDING_MODEL` | `ai-forever/FRIDA` | Модель эмбеддингов (HuggingFace) |
| `TOP_K_RESULTS` | `3` | Количество чанков из retrieval |
| `FAISS_INDEX_PATH` | `app/embeddings_db` | Путь к FAISS-индексу |
| `LLM_PROVIDER` | `gigachat` | Активный провайдер |

## Формат knowledge base

Каждый Markdown-файл должен содержать YAML frontmatter: индексатор извлекает метаданные и режет документ по заголовкам.

```yaml
---
title: Уход за жирной кожей
category: skincare_by_type
subcategory: skin_types
skin_type: oily
skin_concern: acne
tags:
  - oily-skin
  - acne
  - sebum
lang: ru
version: 1
---

# Жирная кожа

Краткое описание темы.

## Основные признаки

...

## Утренний уход

...
```

`MarkdownHeaderTextSplitter` использует заголовки как границы смысловых блоков. Поле `skin_type` в frontmatter используется для пост-фильтрации в `RAGService.search()`.

## Retrieval и качество

Метрики retrieval (`Hit@K`, `Recall@K`, `MRR@K`) вычисляются по фиксированному тест-сету в ноутбуках `app/notebooks/`. Результаты сохраняются в `app/artifacts/`:

- `retrieval_eval.csv` — результаты по каждому запросу
- `retrieval_metrics_summary.json` — агрегированные метрики
- графики и примеры ответов

## Сценарий демонстрации

1. Запустить сервис: `make run` (или `docker-compose up --build`)
2. Открыть веб-чат: `http://localhost:8080/`
3. Проверить health endpoint: `curl http://localhost:8080/api/health`
4. Ввести запрос с указанием типа кожи: _«У меня жирная кожа и акне, что добавить в уход?»_
5. Показать, что в ответе возвращаются `sources` — конкретные разделы из knowledge base
6. При необходимости сменить провайдер через `.env` (переменная `LLM_PROVIDER`) и перезапустить

## Учебный проект

Проект разработан как учебный backend с RAG-архитектурой для консультаций по уходу за кожей в рамках программы ДПО «Инженерия искусственного интеллекта» РТУ МИРЭА. Планируемые направления развития: усиление retrieval (гибридный поиск BM25 + FAISS), расширение knowledge base, добавление мультимодальности (анализ фото кожи).