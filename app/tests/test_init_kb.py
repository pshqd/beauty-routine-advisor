"""
Тесты для init_kb.py: функции build_chunks и _normalize_meta.
Используют временные файлы — не требуют реального FAISS-индекса.
"""

import pytest
import sys
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile, textwrap

# ── патч ML-зависимостей ──────────────────────────────────────────────────────
sys.modules.setdefault("langchain_community", MagicMock())
sys.modules.setdefault("langchain_community.vectorstores", MagicMock())
sys.modules.setdefault("langchain_huggingface", MagicMock())
sys.modules.setdefault("langchain_text_splitters", MagicMock())
sys.modules.setdefault("frontmatter", MagicMock())

# Импортируем напрямую нужные функции
from init_kb import _normalize_meta


# ── _normalize_meta ───────────────────────────────────────────────────────────

class TestNormalizeMeta:
    def test_string_values_unchanged(self):
        meta = {"title": "Уход", "category": "oily"}
        result = _normalize_meta(meta)
        assert result["title"] == "Уход"
        assert result["category"] == "oily"

    def test_list_joined_with_comma(self):
        meta = {"tags": ["acne", "oily", "teen"]}
        result = _normalize_meta(meta)
        assert result["tags"] == "acne, oily, teen"

    def test_none_becomes_empty_string(self):
        meta = {"author": None}
        result = _normalize_meta(meta)
        assert result["author"] == ""

    def test_int_becomes_string(self):
        meta = {"order": 5}
        result = _normalize_meta(meta)
        assert result["order"] == "5"

    def test_empty_dict(self):
        assert _normalize_meta({}) == {}

    def test_nested_list_of_ints(self):
        meta = {"ids": [1, 2, 3]}
        result = _normalize_meta(meta)
        assert result["ids"] == "1, 2, 3"

    def test_bool_value(self):
        meta = {"active": True}
        result = _normalize_meta(meta)
        assert result["active"] == "True"


# ── build_chunks (с мок-файловой системой) ────────────────────────────────────

class TestBuildChunks:
    """
    build_chunks читает *.md файлы из Config.KNOWLEDGE_BASE_PATH.
    Мокаем frontmatter.load и Path.rglob для изоляции.
    """

    def _make_post(self, title, category, content):
        post = MagicMock()
        post.metadata = {"title": title, "category": category}
        post.content = content
        return post

    def test_skips_files_without_title(self):
        """Файл без поля title должен быть пропущен."""
        import init_kb as kb
        post_no_title = MagicMock()
        post_no_title.metadata = {"category": "oily"}
        post_no_title.content = "# Текст"

        with patch("init_kb.frontmatter.load", return_value=post_no_title), \
             patch.object(Path, "rglob", return_value=[Path("no_title.md")]):
            chunks = kb.build_chunks()
        assert chunks == []

    def test_skips_files_without_category(self):
        """Файл без поля category должен быть пропущен."""
        import init_kb as kb
        post_no_cat = MagicMock()
        post_no_cat.metadata = {"title": "Уход"}
        post_no_cat.content = "# Текст"

        with patch("init_kb.frontmatter.load", return_value=post_no_cat), \
             patch.object(Path, "rglob", return_value=[Path("no_cat.md")]):
            chunks = kb.build_chunks()
        assert chunks == []

    def test_source_meta_added(self):
        """Каждый чанк должен содержать metadata['source'] с именем файла."""
        import init_kb as kb

        fake_doc = MagicMock()
        fake_doc.page_content = "Короткий текст."
        fake_doc.metadata = {}

        post = MagicMock()
        post.metadata = {"title": "Уход", "category": "oily"}
        post.content = "## Очищение\nИспользуйте мягкий гель."

        with patch("init_kb.frontmatter.load", return_value=post), \
             patch.object(Path, "rglob", return_value=[Path("oily_skin.md")]), \
             patch("init_kb.md_splitter.split_text", return_value=[fake_doc]):
            chunks = kb.build_chunks()

        assert all("source" in c.metadata for c in chunks)
        assert chunks[0].metadata["source"] == "oily_skin.md"

    def test_no_md_files_returns_empty(self):
        """Если нет md-файлов — возвращаем пустой список."""
        import init_kb as kb
        with patch.object(Path, "rglob", return_value=[]):
            chunks = kb.build_chunks()
        assert chunks == []
