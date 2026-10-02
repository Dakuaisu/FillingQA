#!/bin/sh
# Migrate, check the restored corpus against the freeze, and only then serve.
set -e
python -m api.db
if ! python -m scripts.verify_freeze --snapshot; then
  echo "corpus does not match api/corpus_freeze.yaml: refusing to serve" >&2
  exit 1
fi
exec uvicorn api.server:app --host 0.0.0.0 --port "${PORT:-8000}"
