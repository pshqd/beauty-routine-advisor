# Принудительно linux/amd64 — стабильные wheel-пакеты, без ARM-специфики
FROM --platform=linux/amd64 python:3.11-slim
WORKDIR /app
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

RUN pip install --no-cache-dir \
        torch --index-url https://download.pytorch.org/whl/cpu

        RUN pip install --no-cache-dir \
        sentence-transformers \
        langchain-huggingface

# Слой 3: langchain-стек
RUN pip install --no-cache-dir \
        langchain-community \
        langchain-gigachat \
        langchain-text-splitters \
        faiss-cpu

RUN pip install --no-cache-dir \
        flask \
        flask-cors \
        python-frontmatter \
        python-dotenv \
        requests \
        gunicorn

COPY app/ .

RUN mkdir -p .faiss_index artifacts \
    && mkdir -p /home/appuser/.cache/huggingface \
    && chown -R appuser:appuser /app /home/appuser

USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=5000 \
    DEBUG=false \
    VERSION=1.0.0 \
    HF_HOME=/home/appuser/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface

EXPOSE 8800

ENTRYPOINT ["sh", "-c", "python init_kb.py && gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 2 --timeout 120 app:app"]