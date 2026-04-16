APP_DIR       := app
DOCS_DIR      := $docs/sphinx
TESTS_DIR     := $(APP_DIR)/tests
UV            := uv

CYAN  := \033[0;36m
RESET := \033[0m

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo ""
	@echo "$(CYAN)SkinCare Advisor — доступные команды:$(RESET)"
	@echo ""
	@echo "  make install       Установить зависимости (dev) через uv"
	@echo "  make install-dev   Алиас для dev-установки"
	@echo "  make run           Запустить Flask с авторелоадом"
	@echo "  make test          Запустить все тесты"
	@echo "  make test-v        Запустить тесты подробно"
	@echo "  make test-cov      Запустить тесты с coverage"
	@echo "  make lint          Проверить код через flake8"
	@echo "  make format        Отформатировать код через black"
	@echo "  make format-check  Проверить black без изменений"
	@echo "  make check         lint + format-check"
	@echo "  make docs          Собрать документацию Sphinx"
	@echo "  make docs-clean    Очистить сборку документации"
	@echo "  make init-kb       Переиндексировать knowledge base"
	@echo "  make clean         Очистить кэш и временные файлы"
	@echo ""

.PHONY: install
install:
	@echo "$(CYAN)▶ Установка зависимостей (dev) через uv...$(RESET)"
	$(UV) sync --dev

.PHONY: install-dev
install-dev: install

.PHONY: run
run:
	@echo "$(CYAN)▶ Запуск Flask с autoreload...$(RESET)"
	cd $(APP_DIR) && \
	FLASK_APP=app.py \
	FLASK_ENV=development \
	FLASK_DEBUG=1 \
	$(UV) run flask run --reload --host=0.0.0.0 --port=8000

.PHONY: test
test:
	@echo "$(CYAN)▶ Запуск тестов...$(RESET)"
	cd $(APP_DIR) && $(UV) run pytest tests -q

.PHONY: test-v
test-v:
	@echo "$(CYAN)▶ Запуск тестов (verbose)...$(RESET)"
	cd $(APP_DIR) && $(UV) run pytest tests -v

.PHONY: test-cov
test-cov:
	@echo "$(CYAN)▶ Тесты с coverage...$(RESET)"
	cd $(APP_DIR) && $(UV) run pytest tests \
		--cov=. \
		--cov-report=term-missing \
		--cov-report=html:artifacts/coverage_html \
		-q

.PHONY: lint
lint:
	@echo "$(CYAN)▶ flake8...$(RESET)"
	cd $(APP_DIR) && $(UV) run flake8 . \
		--max-line-length=88 \
		--extend-ignore=E203,W503 \
		--exclude=.venv,__pycache__,artifacts,.faiss_index,.faiss_index_v2

.PHONY: format
format:
	@echo "$(CYAN)▶ black format...$(RESET)"
	cd $(APP_DIR) && $(UV) run black . \
		--line-length=88 \
		--exclude="\.venv|__pycache__|artifacts"

.PHONY: format-check
format-check:
	@echo "$(CYAN)▶ black check...$(RESET)"
	cd $(APP_DIR) && $(UV) run black . \
		--check \
		--line-length=88 \
		--exclude="\.venv|__pycache__|artifacts"

.PHONY: check
check: lint format-check

.PHONY: docs
docs:
	@echo "$(CYAN)▶ Генерация Sphinx API docs...$(RESET)"
	cd $(APP_DIR) && $(UV) run sphinx-apidoc \
		-o docs/sphinx/source \
		. \
		tests \
		--force \
		--separate
	cd $(DOCS_DIR) && $(UV) run sphinx-build \
		-b html \
		source \
		build/html \
		-E

.PHONY: docs-clean
docs-clean:
	@echo "$(CYAN)▶ Очистка Sphinx build...$(RESET)"
	rm -rf $(DOCS_DIR)/build
	rm -f $(DOCS_DIR)/source/*.rst

.PHONY: init-kb
init-kb:
	@echo "$(CYAN)▶ Переиндексация knowledge base (FAISS)...$(RESET)"
	cd $(APP_DIR) && $(UV) run python init_kb.py

.PHONY: clean
clean:
	@echo "$(CYAN)▶ Очистка кэша...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true