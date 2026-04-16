from pathlib import Path
from config import Config


def test_paths_are_path_objects():
    assert isinstance(Config.KNOWLEDGE_BASE_PATH, Path)
    assert isinstance(Config.EMBEDDINGS_DB_PATH, Path)


def test_collection_name_is_ascii():
    assert Config.COLLECTION_KB == "skincare_kb"
