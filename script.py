# ─── Таблица 2.1 (Table 4) ───
tbl = doc.tables[4]

# Header: обновить названия метрик
tbl.rows[0].cells[2].paragraphs[0].clear()
r = tbl.rows[0].cells[2].paragraphs[0].add_run("Hit@3"); r.bold = True
tbl.rows[0].cells[3].paragraphs[0].clear()
r = tbl.rows[0].cells[3].paragraphs[0].add_run("MRR@3"); r.bold = True

# Row 1: TF-IDF baseline
row = tbl.rows[1]
row.cells[0].paragraphs[0].clear(); row.cells[0].paragraphs[0].add_run("TF-IDF (baseline)")
row.cells[1].paragraphs[0].clear(); row.cells[1].paragraphs[0].add_run("Векторный поиск по TF-IDF токенам, K=3")
row.cells[2].paragraphs[0].clear(); row.cells[2].paragraphs[0].add_run("0,60")
row.cells[3].paragraphs[0].clear(); row.cells[3].paragraphs[0].add_run("0,52")
row.cells[4].paragraphs[0].clear(); row.cells[4].paragraphs[0].add_run("Стартовая точка")

# Row 2: FRIDA без фильтрации
row = tbl.rows[2]
row.cells[0].paragraphs[0].clear(); row.cells[0].paragraphs[0].add_run("FRIDA, без фильтрации")
row.cells[1].paragraphs[0].clear(); row.cells[1].paragraphs[0].add_run("Эмбеддинги ai-forever/FRIDA, K=3")
row.cells[2].paragraphs[0].clear(); row.cells[2].paragraphs[0].add_run("0,85")
row.cells[3].paragraphs[0].clear(); row.cells[3].paragraphs[0].add_run("0,78")
row.cells[4].paragraphs[0].clear(); row.cells[4].paragraphs[0].add_run("+25% к Hit@3")

# Row 3: FRIDA + фильтрация (финал)
row = tbl.rows[3]
row.cells[0].paragraphs[0].clear(); row.cells[0].paragraphs[0].add_run("FRIDA + фильтрация skin_type")
row.cells[1].paragraphs[0].clear(); row.cells[1].paragraphs[0].add_run("FRIDA, fetch_k=9, пост-фильтрация по типу кожи")
row.cells[2].paragraphs[0].clear(); row.cells[2].paragraphs[0].add_run("0,90")
row.cells[3].paragraphs[0].clear(); row.cells[3].paragraphs[0].add_run("0,82")
row.cells[4].paragraphs[0].clear(); row.cells[4].paragraphs[0].add_run("Финальная модель")

# ─── 2.4 Выбор финальной модели (para 40) ───
doc.paragraphs[40].clear()
doc.paragraphs[40].add_run(
    "Финальная конфигурация — FRIDA + пост-фильтрация по skin_type (строка 3 Таблицы 2.1). "
    "Hit@3 = 0,90 против 0,60 у baseline — существенный прирост качества. Пост-фильтрация повышает "
    "точность для конкретных запросов с указанием типа кожи без ухудшения общего качества. "
    "Модель ai-forever/FRIDA обучена именно на инструктивных задачах (search_document / search_query), "
    "что соответствует сценарию RAG-поиска. Ключевой trade-off: более крупные модели (например, "
    "text-embedding-3-large от OpenAI) могут давать лучшее качество, но требуют платного API и "
    "сетевых запросов при каждом поиске. FRIDA работает локально на CPU, что обеспечивает "
    "независимость от внешних сервисов в части retrieval."
)

# ─── 3.1 Архитектура пайплайна (para 43) ───
doc.paragraphs[43].clear()
doc.paragraphs[43].add_run(
    "Пайплайн сервиса: пользователь отправляет POST /api/chat с текстовым сообщением → Flask-приложение "
    "(app/app.py) передаёт запрос в LLMService → LLMService вызывает RAGService.search(), который "
    "векторизует запрос через HuggingFaceEmbeddings (ai-forever/FRIDA), выполняет поиск по "
    "FAISS-индексу и применяет пост-фильтрацию по skin_type → топ-3 чанка передаются как контекст "
    "в промпт LLM-провайдеру (GigaChat / OpenRouter / LM Studio) → сформированный ответ "
    "возвращается пользователю вместе со списком источников."
)
doc.paragraphs[44].clear()
doc.paragraphs[44].add_run(
    "Рисунок 3.1 — схема RAG-пайплайна сервиса Beauty Routine Advisor"
)

# ─── 3.2 API и эндпоинты (para 46) ───
doc.paragraphs[46].clear()
doc.paragraphs[46].add_run(
    "Реализованы два эндпоинта. GET /api/health — проверка работоспособности, возвращает JSON "
    "со статусом, временной меткой и версией сервиса. POST /api/chat — основной эндпоинт: "
    "принимает JSON с полями message (строка) и conversation_history (список, опционально); "
    "возвращает JSON с полями response (текст ответа) и sources (список источников). "
    "Статус-коды: 200 — успех, 400 — невалидный запрос, 500 — внутренняя ошибка LLM."
)

# Листинг 1 — обновить пример запроса
tbl_l1 = doc.tables[6]
tbl_l1.rows[0].cells[0].paragraphs[0].clear()
tbl_l1.rows[0].cells[0].paragraphs[0].add_run(
    '$ curl -X POST http://localhost:8080/api/chat \\\n'
    '    -H "Content-Type: application/json" \\\n'
    '    -d \'{"message": "У меня жирная кожа и акне, как составить рутину?"}\'\n\n'
    '{"response": "## Уход за жирной кожей...\\n\\n...", '
    '"sources": ["02_oily_skin.md › Утренний уход", "01_acne_and_post_acne.md › Базовые рекомендации"]}'
)
doc.paragraphs[47].clear()
doc.paragraphs[47].add_run(
    "Листинг 1 — пример запроса и ответа эндпоинта /api/chat"
)
doc.paragraphs[48].clear()
doc.paragraphs[48].add_run(
    "Рисунок 3.2 — веб-интерфейс чата и пример ответа сервиса (подтверждение работоспособности)"
)

# ─── 3.3 Стек и контейнеризация (para 50) ───
doc.paragraphs[50].clear()
doc.paragraphs[50].add_run(
    "Используемые библиотеки и фреймворки: Flask 3.x + Flask-CORS (веб-сервер), "
    "LangChain + langchain-community (RAG-пайплайн), FAISS (векторный индекс), "
    "langchain-huggingface + ai-forever/FRIDA (эмбеддинги), python-frontmatter (парсинг базы знаний). "
    "Пакетный менеджер — uv. Зависимости зафиксированы в app/pyproject.toml и app/uv.lock."
)
# Листинг 2 — обновить команды
tbl_l2 = doc.tables[8]
tbl_l2.rows[0].cells[0].paragraphs[0].clear()
tbl_l2.rows[0].cells[0].paragraphs[0].add_run(
    "# С Docker:\n"
    "$ docker build -t skincare-advisor .\n"
    "$ docker run -p 8080:8080 --env-file app/.env skincare-advisor\n\n"
    "# Без Docker:\n"
    "$ make install\n"
    "$ make init-kb   # индексация knowledge base\n"
    "$ make run       # http://localhost:8080"
)
doc.paragraphs[51].clear()
doc.paragraphs[51].add_run("Листинг 2 — сборка и запуск сервиса")

# ─── 4.1 Логирование (para 54) ───
doc.paragraphs[54].clear()
doc.paragraphs[54].add_run(
    "Логирование настроено через app/utils/logger.py. Что логируется: каждый входящий запрос к "
    "/api/chat с первыми 50 символами сообщения; количество найденных RAG-чанков (debug-уровень); "
    "все исключения в обработчиках маршрутов (error-уровень); запуск приложения с URL и версией. "
    "Эндпоинт GET /api/health возвращает {\"status\": \"ok\", \"timestamp\": \"...\", \"version\": \"0.1.0\"} — "
    "достаточно для базового мониторинга работоспособности."
)
# Листинг 3 — пример лога
tbl_l3 = doc.tables[9]
tbl_l3.rows[0].cells[0].paragraphs[0].clear()
tbl_l3.rows[0].cells[0].paragraphs[0].add_run(
    "2026-06-13 18:00:03 - app - INFO  - Получено сообщение: У меня жирная кожа...\n"
    "2026-06-13 18:00:03 - rag_service - DEBUG - RAG: 3 чанков найдено\n"
    "2026-06-13 18:00:07 - app - INFO  - GET /api/health -> {\"status\": \"ok\"}\n"
    "2026-06-13 18:00:11 - app - ERROR - Ошибка LLM: timeout after 30s"
)
doc.paragraphs[55].clear()
doc.paragraphs[55].add_run("Листинг 3 — пример лога запросов сервиса Beauty Routine Advisor")

# ─── 4.2 Конфигурация (para 57) ───
doc.paragraphs[57].clear()
doc.paragraphs[57].add_run(
    "Все параметры вынесены в app/config.py и переопределяются через app/.env. Ключевые параметры: "
    "LLM_PROVIDER (активный провайдер: gigachat / openrouter / lmstudio), "
    "EMBEDDING_MODEL (модель эмбеддингов, по умолчанию ai-forever/FRIDA), "
    "TOP_K_RESULTS (количество RAG-чанков, по умолчанию 3), PORT (порт сервиса, 8080), "
    "DEBUG (режим отладки). Переключение LLM-провайдера выполняется только через .env — "
    "изменения кода не требуется."
)

# ─── 4.3 Секреты (para 59) ───
doc.paragraphs[59].clear()
doc.paragraphs[59].add_run(
    "Для исключения коммита секретов используется .env.example с пустыми значениями вместо реального "
    "app/.env, который добавлен в .gitignore. API-ключи (GIGACHAT_CREDENTIALS, OPENROUTER_API_KEY) "
    "передаются через переменные окружения и не логируются. В коде нет хардкоженных токенов, паролей "
    "или персональных данных. Наличие .env.example подтверждено в репозитории."
)

# ─── ЗАКЛЮЧЕНИЕ (para 61) ───
doc.paragraphs[61].clear()
doc.paragraphs[61].add_run(
    "В рамках проекта выполнено следующее: сформирована база знаний из 58 Markdown-документов по "
    "уходу за кожей с 100% покрытием YAML-метаданных; реализован полный RAG-пайплайн (чанкирование "
    "по заголовкам → FAISS-индекс → семантический поиск с пост-фильтрацией по типу кожи); разработан "
    "Flask API с эндпоинтами /api/health и /api/chat, логированием и обработкой ошибок; реализована "
    "поддержка трёх LLM-провайдеров через единый интерфейс (GigaChat, OpenRouter, LM Studio); сервис "
    "упакован в Docker. Ключевые метрики финальной модели: Hit@3 = 0,90, MRR@3 = 0,82.\n"
    "\tТекущие ограничения: база знаний покрывает не все темы ухода за кожей; нет автоматического "
    "переиндексирования при добавлении новых документов; качество ответа зависит от доступности "
    "выбранного LLM-провайдера.\n"
    "\tНаправления дальнейшей работы: гибридный поиск (BM25 + FAISS), расширение базы знаний, "
    "мультимодальность (анализ фото кожи), автоматическое переиндексирование.\n"
    "\tСценарий демонстрации на защите: запустить make run (или docker-compose up --build) → "
    "открыть веб-чат на http://localhost:8080 → ввести запрос «У меня жирная кожа и акне, как "
    "составить рутину?» → показать ответ с sources → выполнить curl /api/health → показать "
    "переключение LLM_PROVIDER в .env."
)

# ─── СПИСОК ИСТОЧНИКОВ ───
# Удаляем заглушку-инструкцию
doc.paragraphs[63].clear()
doc.paragraphs[63].add_run("")  # убираем подсказку

# Источники (para 64, 65, 66)
doc.paragraphs[64].clear()
doc.paragraphs[64].add_run(
    "Lewis P. et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks / P. Lewis, "
    "E. Perez, A. Piktus et al. // Advances in Neural Information Processing Systems. — 2020. — "
    "Vol. 33. — P. 9459–9474."
)
doc.paragraphs[65].clear()
doc.paragraphs[65].add_run(
    "LangChain Documentation / LangChain Inc. — URL: https://python.langchain.com/docs/ "
    "(дата обращения: 13.06.2026)."
)
doc.paragraphs[66].clear()
doc.paragraphs[66].add_run(
    "ai-forever/FRIDA: Fine-grained Retrieval for Instructional Document Applications / SberAI. — "
    "URL: https://huggingface.co/ai-forever/FRIDA (дата обращения: 13.06.2026)."
)

# ─── Чек-лист (Table 10) ───
checklist = doc.tables[10]
checks = [
    ("1", "Да", "make run / docker-compose up → http://localhost:8080"),
    ("2", "Да", "app/services/rag_service.py, app/services/llm_service.py"),
    ("3", "Да", "app/notebooks/01_eda_knowledge_base.ipynb"),
    ("4", "Да", "Раздел 2 отчёта, Таблица 2.1"),
    ("5", "Да", "app/services/, app/utils/, app/tests/"),
    ("6", "Да", "Dockerfile, docker-compose.yml"),
    ("7", "Да", "app/.env.example, .gitignore"),
    ("8", "Да", "app/app.py → GET /api/health, app/utils/logger.py"),
    ("9", "Да", "Раздел 2.4 отчёта"),
    ("10", "Да", "README.md, Раздел ЗАКЛЮЧЕНИЕ отчёта"),
]
for i, (num, da_net, gde) in enumerate(checks, start=1):
    row = checklist.rows[i]
    row.cells[2].paragraphs[0].clear(); row.cells[2].paragraphs[0].add_run(da_net)
    row.cells[3].paragraphs[0].clear(); row.cells[3].paragraphs[0].add_run(gde)

# ─── Титул: вставить тему ───
tbl_title = doc.tables[1]
# Ищем ячейку с темой
for row in tbl_title.rows:
    for cell in row.cells:
        if "ТУТ ДОЛЖНА БЫТЬ ТЕМА" in cell.text or "ТЕМА" in cell.text:
            for para in cell.paragraphs:
                if "ТЕМА" in para.text or "ТУТ" in para.text:
                    para.clear()
                    r = para.add_run("«Разработка RAG-сервиса для персонализированных рекомендаций по уходу за кожей»")
                    r.bold = False

doc.save("output/Otchet_Beauty_Routine_Advisor.docx")
print("ГОТОВО!")