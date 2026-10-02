#!/bin/sh
# make deploy-check: build both images, run the stack against the corpus snapshot,
# hit /health and the Ask page in the containers, always tear down.
set -e
cd "$(dirname "$0")"
test -f ../build/corpus_snapshot.dump || { echo "build/corpus_snapshot.dump missing: python -m scripts.corpus_snapshot dump" >&2; exit 1; }
EXPECTED_SHA256=$(python3 -c "import yaml;print(yaml.safe_load(open('../api/corpus_freeze.yaml'))['snapshot']['sha256'])")
export EXPECTED_SHA256
trap 'docker compose -f compose.yaml down -v >/dev/null 2>&1' EXIT
docker compose -f compose.yaml up -d --build --wait --wait-timeout 900
echo "--- GET /api/v1/health (api container)"
curl -fsS "http://localhost:${API_PORT:-18000}/api/v1/health"
echo
echo "--- GET / (web container)"
curl -fsS "http://localhost:${WEB_PORT:-13000}/" | grep -o "Ask the filings" | head -1
echo "deploy-check: ok"
