import chromadb
from config import Config

client = chromadb.PersistentClient(path=str(Config.EMBEDDINGS_DB_PATH))
collection = client.get_collection(Config.COLLECTION_KB)

data = collection.get(include=["documents", "metadatas"], limit=10)

for i, meta in enumerate(data["metadatas"], 1):
    print(f"\n--- {i} ---")
    print(meta)
