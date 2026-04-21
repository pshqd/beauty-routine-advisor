# SkinCare Advisor

AI-консультант по уходу за кожей на основе RAG-архитектуры. Он отвечает на вопросы о типах кожи, уходовых рутинах и косметических ингредиентах, опираясь на внутреннюю базу знаний в Markdown и локальный FAISS-индекс.

## Стек

| Слой | Технология |
|---|---|
| Backend | Flask + Flask-CORS |
| LLM | OpenRouter API через provider abstraction, с поддержкой GigaChat |
| Embeddings | `deepvk/USER-base` |
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
- Поддержка нескольких LLM-провайдеров через единый сервисный слой.

## Структура проекта

```text
beauty-routine-advisor/
├── Makefile
├── pyproject.toml
└── app/
    ├── app.py
    ├── config.py
    ├── init_kb.py
    ├── services/
    │   ├── llm_service.py
    │   ├── rag_service.py
    │   └── providers/
    │       ├── base.py
    │       ├── openrouter.py
    │       └── gigachat.py
    ├── knowledge_base/
    │   └── skincare_kb/
    ├── templates/
    │   └── index.html
    ├── static/
    │   ├── css/style.css
    │   └── js/chat.js
    ├── tests/
    ├── docs/
    │   └── sphinx/
    ├── artifacts/
    └── .faiss_index/
```

Рабочая часть проекта находится в каталоге `app/`, а `Makefile` лежит в корне и запускает команды относительно этой структуры.

## Быстрый старт

### Клонирование

```bash
git clone <repo-url>
cd beauty-routine-advisor
```

### Установка зависимостей

```bash
make install
```

Команда устанавливает dev-зависимости через `uv`.

### Настройка `.env`

Создай файл `app/.env` и укажи нужные переменные:

```env
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=google/gemma-3-27b-it:free

GIGACHAT_CREDENTIALS=your_gigachat_credentials

HOST=0.0.0.0
PORT=5000
DEBUG=true
VERSION=1.0.0
```

Если используется только OpenRouter, `GIGACHAT_CREDENTIALS` можно не задавать.

### Индексация knowledge base

```bash
make init-kb
```

Команда запускает `app/init_kb.py`, который читает Markdown-документы, извлекает frontmatter, режет текст на чанки и строит FAISS-индекс.

### Запуск приложения

```bash
make run
```

Сервер запускается в dev-режиме Flask с autoreload.

## Make-команды

### Разработка

```bash
make install
make install-dev
make run
make init-kb
```

- `make install` — установка зависимостей через `uv`.
- `make run` — запуск Flask backend с autoreload.
- `make init-kb` — переиндексация knowledge base в FAISS.

### Тесты

```bash
make test
make test-v
make test-cov
```

- `make test` — быстрый запуск тестов.
- `make test-v` — запуск тестов с подробным выводом.
- `make test-cov` — запуск тестов с coverage-отчётом.

### Качество кода

```bash
make lint
make format
make format-check
make check
```

- `make lint` — проверка кода через `flake8`.
- `make format` — форматирование через `black`.
- `make format-check` — проверка форматирования без изменений.
- `make check` — комбинированная команда для CI: `lint + format-check`.

### Документация

```bash
make docs
make docs-clean
```

- `make docs` — генерация API-документации через `sphinx-apidoc` и сборка HTML через Sphinx.
- `make docs-clean` — очистка собранной документации.

Sphinx используется для генерации документации по Python docstrings через `sphinx-apidoc` и `sphinx-build`.

После сборки документация будет доступна в:

```text
app/docs/sphinx/build/html/index.html
```

### Очистка

```bash
make clean
```

Удаляет `__pycache__`, `.pyc`, `.pytest_cache`, `.coverage` и другие временные артефакты.

## Формат knowledge base

Каждый Markdown-файл в knowledge base должен содержать YAML frontmatter и текст с заголовками, потому что индексатор извлекает метаданные и режет документы по структуре Markdown.

Пример:

```yaml
***
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
***

# Жирная кожа

Краткое описание темы.

## Основные признаки

...

## Утренний уход

...

## Вечерний уход

...
```

`MarkdownHeaderTextSplitter` использует заголовки как границы смысловых блоков, а затем длинные секции дополнительно режутся через `RecursiveCharacterTextSplitter`.

## API

### `GET /api/health`

Проверка статуса backend.

Пример ответа:

```json
{
  "status": "ok",
  "message": "SkinCare Advisor API is running",
  "timestamp": "2026-04-16T20:00:00",
  "version": "1.0.0"
}
```

### `POST /api/chat`

Основной endpoint чата.

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

## Retrieval и качество

Рекомендуется иметь отдельный eval-скрипт, который считает метрики `Hit@K`, `Recall@K` и `MRR@K` по фиксированному набору запросов и сохраняет результаты в `app/artifacts/` (`retrieval_eval.csv`, `retrieval_metrics_summary.json`, графики и примеры ответов).

## Учебный проект

Проект разработан как учебный backend с RAG-архитектурой для консультаций по уходу за кожей. План развития включает усиление retrieval, тестов, документации и качества knowledge base. Планируется добавление мультимодальности
