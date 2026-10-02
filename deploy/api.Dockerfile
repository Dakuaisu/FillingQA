# FilingQA API (PRD 9). CPU image; the pipeline runs the embedder, reranker and NLI
# model locally (downloaded from Hugging Face on first use). Generation in a deploy
# is `anthropic_api` (FILINGQA_GENERATION_BACKEND); keys come from the environment.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# torch from the CPU index first, so the project's pin resolves to a CPU wheel.
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.1

COPY pyproject.toml ./
COPY api ./api
RUN pip install -e .

COPY eval ./eval
COPY scripts ./scripts
COPY infra ./infra
COPY deploy/entrypoint.sh ./deploy/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["sh", "deploy/entrypoint.sh"]
