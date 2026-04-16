"""
Файл сборки пакета через setuptools.
Основная конфигурация находится в pyproject.toml.

Для сборки документации Sphinx:
    python setup.py build_sphinx
"""

from setuptools import setup
from setuptools.command.build_py import build_py
import subprocess
import os


class BuildSphinxDocs(build_py):
    """Команда для сборки Sphinx документации вместе с пакетом."""

    def run(self):
        """Запускает сборку Sphinx перед сборкой пакета."""
        sphinx_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "sphinx")
        if os.path.exists(sphinx_dir):
            subprocess.run(["make", "html"], cwd=sphinx_dir, check=True)
        super().run()


setup(
    cmdclass={
        "build_sphinx": BuildSphinxDocs,
    }
)
