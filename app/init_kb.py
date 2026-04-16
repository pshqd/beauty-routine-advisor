# app/init_kb.py
"""Индексация базы знаний в FAISS (LangChain LCEL)."""

import frontmatter
from pathlib import Path
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from config import Config

HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3")]
md_splitter  = MarkdownHeaderTextSplitter(headers_to_split_on=HEADERS, strip_headers=False)
char_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

def _normalize_meta(meta: dict) -> dict:
    """FAISS требует строки в метаданных."""
    return {
        k: ", ".join(str(i) for i in v) if isinstance(v, list)
           else str(v) if v is not None else ""
        for k, v in meta.items()
    }

def build_chunks() -> list:
    chunks = []
    for md_file in sorted(Path(Config.KNOWLEDGE_BASE_PATH).rglob("*.md")):
        post = frontmatter.load(md_file)
        meta = post.metadata
        if not meta.get("title") or not meta.get("category"):
            continue
        for chunk in md_splitter.split_text(post.content.strip()):
            sub = char_splitter.split_documents([chunk]) \
                  if len(chunk.page_content) > 1000 else [chunk]
            for sc in sub:
                sc.metadata.update(_normalize_meta({
                    k: v for k, v in meta.items()
                }) | {"source": md_file.name})
                chunks.append(sc)
    return chunks

if __name__ == "__main__":
    embeddings = HuggingFaceEmbeddings(
        model_name=Config.EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    chunks = build_chunks()
    print(f"📦 Чанков: {len(chunks)}")
    vs = FAISS.from_documents(chunks, embeddings)
    vs.save_local(str(Config.FAISS_INDEX_PATH))
    print(f"✅ Сохранено: {Config.FAISS_INDEX_PATH} ({vs.index.ntotal} векторов)")