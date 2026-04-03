"""
Конфигурация Sphinx для проекта SkinCare Advisor.

Генерирует HTML-документацию из docstrings кода.
Для сборки: make html (в папке docs/sphinx)
"""

import os
import sys

# Добавляем путь к пакету, чтобы autodoc нашёл модули
sys.path.insert(0, os.path.abspath('../../app'))

# -- Project information -----------------------------------------------
project = 'SkinCare Advisor'
copyright = '2026, girl team'
author = 'pshqd'
release = '0.1.0'

# -- General configuration ---------------------------------------------
extensions = [
    'sphinx.ext.autodoc',      # автогенерация из docstrings
    'sphinx.ext.napoleon',     # поддержка Google/NumPy стиля docstrings
    'sphinx.ext.viewcode',     # ссылки на исходный код
    'sphinx.ext.intersphinx',  # ссылки на внешние доки
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'ru'

# -- Options for HTML output -------------------------------------------
html_theme = 'alabaster'
html_static_path = ['_static']

# -- Napoleon settings (стиль docstrings) ------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True

# -- Autodoc settings --------------------------------------------------
autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'private-members': False,
    'show-inheritance': True,
}