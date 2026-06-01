"""
Тесты базы знаний (knowledge_base/*.md).
Что мокается: НИЧЕГО — тесты читают реальные файлы напрямую.
Что проверяется:
  - frontmatter-заголовки обязательных полей
  - структура Markdown (есть ## секции)
  - допустимые значения skin_type
  - минимальный объём контента в каждом файле
  - нет дублирующихся title

Эти тесты НЕ требуют FAISS или ML — только файловую систему.
Запускай: pytest tests/test_knowledge_base.py -v
"""

import sys
import os
import pytest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import frontmatter
    FRONTMATTER_AVAILABLE = True
except ImportError:
    FRONTMATTER_AVAILABLE = False

KB_DIR = Path(__file__).parent.parent / "knowledge_base"

# Собираем все .md файлы один раз
MD_FILES = sorted(KB_DIR.rglob("*.md")) if KB_DIR.exists() else []

VALID_SKIN_TYPES = {"жирная", "сухая", "комбинированная", "нормальная", "чувствительная", "all", ""}
VALID_CATEGORIES = {"cleansing", "moisturizing", "sunscreen", "acne", "anti-aging",
                    "toning", "exfoliation", "serum", "eye-care", "mask", "general"}


# ═══════════════════════════════════════════════════════════════════════════
# Пропускаем все тесты, если knowledge_base не найдена
# ═══════════════════════════════════════════════════════════════════════════

pytestmark = pytest.mark.skipif(
    not KB_DIR.exists() or not MD_FILES,
    reason=f"knowledge_base не найдена или пуста: {KB_DIR}"
)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Структура директории
# ═══════════════════════════════════════════════════════════════════════════

class TestKnowledgeBaseDirectory:

    def test_kb_directory_exists(self):
        """Директория knowledge_base должна существовать."""
        assert KB_DIR.exists(), f"Не найдена: {KB_DIR}"

    def test_has_md_files(self):
        """В базе знаний должен быть хотя бы один .md файл."""
        assert len(MD_FILES) > 0, "Нет .md файлов в knowledge_base/"

    def test_has_minimum_files(self):
        """Минимум 3 файла — иначе RAG не имеет смысла."""
        assert len(MD_FILES) >= 3, f"Слишком мало файлов: {len(MD_FILES)}"

    def test_no_empty_files(self):
        """Ни один .md файл не должен быть пустым."""
        empty = [f.name for f in MD_FILES if f.stat().st_size == 0]
        assert empty == [], f"Пустые файлы: {empty}"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Frontmatter — обязательные поля
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(not FRONTMATTER_AVAILABLE, reason="pip install python-frontmatter")
class TestFrontmatter:

    @pytest.fixture(params=MD_FILES, ids=[f.name for f in MD_FILES])
    def md_post(self, request):
        return frontmatter.load(request.param), request.param.name

    def test_has_title(self, md_post):
        """Каждый файл должен иметь поле title в frontmatter."""
        post, name = md_post
        assert post.metadata.get("title"), f"{name}: нет поля title"

    def test_has_category(self, md_post):
        """Каждый файл должен иметь поле category."""
        post, name = md_post
        assert post.metadata.get("category"), f"{name}: нет поля category"

    def test_skin_type_valid(self, md_post):
        """skin_type должен быть из разрешённого списка (если задан)."""
        post, name = md_post
        st = post.metadata.get("skin_type", "all")
        # Может быть строкой или списком
        if isinstance(st, list):
            invalid = [s for s in st if s not in VALID_SKIN_TYPES]
            assert not invalid, f"{name}: недопустимые skin_type: {invalid}"
        else:
            assert st in VALID_SKIN_TYPES, f"{name}: недопустимый skin_type: {st!r}"

    def test_title_is_string(self, md_post):
        """title должен быть строкой, не числом и не None."""
        post, name = md_post
        title = post.metadata.get("title")
        assert isinstance(title, str), f"{name}: title должен быть строкой, получен {type(title)}"

    def test_content_not_empty(self, md_post):
        """Основной контент файла (после frontmatter) не должен быть пустым."""
        post, name = md_post
        assert post.content.strip(), f"{name}: пустой контент после frontmatter"

    def test_content_minimum_length(self, md_post):
        """Контент должен быть минимум 200 символов — иначе RAG нечего искать."""
        post, name = md_post
        length = len(post.content.strip())
        assert length >= 200, f"{name}: контент слишком короткий ({length} символов)"


# ═══════════════════════════════════════════════════════════════════════════
# 3. Markdown-структура
# ═══════════════════════════════════════════════════════════════════════════

class TestMarkdownStructure:

    @pytest.fixture(params=MD_FILES, ids=[f.name for f in MD_FILES])
    def md_text(self, request):
        return request.param.read_text(encoding="utf-8"), request.param.name

    def test_has_h2_sections(self, md_text):
        """Каждый файл должен содержать хотя бы один раздел ## (для MarkdownHeaderTextSplitter)."""
        text, name = md_text
        lines = text.splitlines()
        h2_lines = [l for l in lines if l.startswith("## ")]
        assert len(h2_lines) >= 1, f"{name}: нет разделов ## (нужны для чанкинга)"

    def test_no_broken_frontmatter(self, md_text):
        """Frontmatter должен начинаться с --- и закрываться ---."""
        text, name = md_text
        lines = text.splitlines()
        if lines and lines[0].strip() == "---":
            # Ищем закрывающий ---
            close_idx = None
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    close_idx = i
                    break
            assert close_idx is not None, f"{name}: незакрытый frontmatter (нет второго ---)"


# ═══════════════════════════════════════════════════════════════════════════
# 4. Уникальность
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(not FRONTMATTER_AVAILABLE, reason="pip install python-frontmatter")
class TestUniqueness:

    def test_no_duplicate_titles(self):
        """Все title должны быть уникальными."""
        titles = []
        for f in MD_FILES:
            post = frontmatter.load(f)
            t = post.metadata.get("title")
            if t:
                titles.append(t)
        duplicates = [t for t in set(titles) if titles.count(t) > 1]
        assert not duplicates, f"Дублирующиеся title: {duplicates}"

    def test_no_duplicate_filenames(self):
        """Имена файлов должны быть уникальными."""
        names = [f.name for f in MD_FILES]
        duplicates = [n for n in set(names) if names.count(n) > 1]
        assert not duplicates, f"Дублирующиеся имена файлов: {duplicates}"
