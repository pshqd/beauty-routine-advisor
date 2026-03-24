"""
Скрипт инициализации базы знаний.

Рекурсивно читает .md файлы из knowledge_base/, нарезает на чанки
по заголовкам ##/###, генерирует эмбеддинги и сохраняет в ChromaDB.

Использование:
    python init_kb.py

Автор: Участник 1 (ML Backend Engineer)
"""

import pathlib
import frontmatter
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import MarkdownHeaderTextSplitter
from utils.logger import setup_logger
from config import Config
logger = setup_logger(__name__)

KB_DIR = Config.KNOWLEDGE_BASE_PATH
CHROMA_DIR = Config.EMBEDDINGS_DB_PATH
COLLECTION_NAME = Config.COLLECTION_KB
EMBED_MODEL = Config.EMBEDDING_MODEL


def load_md_files(kb_dir: pathlib.Path) -> list[dict]:
    """
    Рекурсивно читает все .md файлы из директории базы знаний.

    Args:
        kb_dir (pathlib.Path): Путь к директории с MD-файлами.

    Returns:
        list[dict]: Список словарей с ключами 'content', 'metadata', 'source'.
    """
    docs = []
    for md_path in kb_dir.rglob("*.md"):
        if md_path.name == "README.md":
            continue
        try:
            post = frontmatter.load(str(md_path))
            docs.append({
                "content": post.content,
                "metadata": dict(post.metadata),
                "source": md_path.relative_to(kb_dir).as_posix(),
            })
            logger.debug(f"Загружен файл: {md_path.name}")
        except Exception as e:
            logger.warning(f"Не удалось загрузить {md_path}: {e}")
    return docs


def split_into_chunks(docs: list[dict]) -> list[dict]:
    """
    Разбивает документы на чанки по заголовкам ## и ###.

    Args:
        docs (list[dict]): Список документов из load_md_files().

    Returns:
        list[dict]: Список чанков с ключами 'text', 'source', 'section', 'skin_type'.
    """
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("##", "section"), ("###", "subsection")],
        strip_headers=False,
    )
    chunks = []
    for doc in docs:
        try:
            splits = splitter.split_text(doc["content"])
            for split in splits:
                if len(split.page_content.strip()) < 50:
                    continue
                chunks.append({
                    "text": split.page_content.strip(),
                    "source": doc["source"],
                    "section": split.metadata.get("section", ""),
                    "skin_type": doc["metadata"].get("skin_type", "all"),
                })
        except Exception as e:
            logger.warning(f"Ошибка при разбиении {doc['source']}: {e}")
    return chunks


def index_chunks(chunks: list[dict], embed_model: str, chroma_dir: pathlib.Path) -> None:
    """
    Генерирует эмбеддинги для чанков и сохраняет их в ChromaDB.

    Args:
        chunks (list[dict]): Список чанков из split_into_chunks().
        embed_model (str): Название модели sentence-transformers.
        chroma_dir (pathlib.Path): Путь для хранения ChromaDB.
    """
    logger.info(f"Загрузка модели эмбеддингов: {embed_model}")
    model = SentenceTransformer(embed_model)

    client = chromadb.PersistentClient(path=str(chroma_dir))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    texts = [c["text"] for c in chunks]
    logger.info(f"Генерация эмбеддингов для {len(texts)} чанков...")
    embeddings = model.encode(
        texts, show_progress_bar=True, normalize_embeddings=True
    ).tolist()

    collection.add(
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        embeddings=embeddings,
        documents=texts,
        metadatas=[
            {
                "source": c["source"],
                "section": c["section"],
                "skin_type": c["skin_type"],
            }
            for c in chunks
        ],
    )
    unique_files = len(set(c["source"] for c in chunks))
    logger.info(f"Проиндексировано {len(chunks)} чанков из {unique_files} файлов")


if __name__ == "__main__":
    logger.info("Запуск индексации базы знаний...")
    docs = load_md_files(KB_DIR)
    if not docs:
        logger.error(f"❌ Не найдено .md файлов в {KB_DIR}")
        exit(1)
    logger.info(f"Загружено файлов: {len(docs)}")
    chunks = split_into_chunks(docs)
    logger.info(f"Нарезано чанков: {len(chunks)}")
    index_chunks(chunks, EMBED_MODEL, CHROMA_DIR)
    logger.info("Индексация завершена!")
