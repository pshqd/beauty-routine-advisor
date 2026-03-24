from pathlib import Path
from init_kb import load_md_files, split_into_chunks

def test_load_md_files_finds_markdown():
    docs = load_md_files(Path("knowledge_base"))
    assert isinstance(docs, list)
    assert len(docs) > 0

def test_split_into_chunks_returns_chunks():
    docs = load_md_files(Path("knowledge_base"))
    chunks = split_into_chunks(docs)
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert "text" in chunks[0]
    assert "source" in chunks[0]
