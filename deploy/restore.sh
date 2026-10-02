#!/bin/sh
# Runs in the Postgres image: restore the corpus snapshot once, after migrations.
# EXPECTED_SHA256 is the `snapshot.sha256` recorded in api/corpus_freeze.yaml.
set -e
ARCHIVE=/snapshot/corpus_snapshot.dump
export PGPASSWORD="$POSTGRES_PASSWORD"
PSQL="psql -h ${PGHOST:-db} -U $POSTGRES_USER -d $POSTGRES_DB -v ON_ERROR_STOP=1 -tA"
got=$(sha256sum "$ARCHIVE" | cut -d' ' -f1)
if [ "$got" != "$EXPECTED_SHA256" ]; then
  echo "refusing $ARCHIVE: sha256 $got != recorded $EXPECTED_SHA256" >&2
  exit 1
fi
if [ "$($PSQL -c 'SELECT count(*) FROM chunks')" != "0" ]; then
  echo "chunks already present; not restoring again"
  exit 0
fi
pg_restore -h "${PGHOST:-db}" -U "$POSTGRES_USER" -d "$POSTGRES_DB" --data-only --single-transaction \
  --disable-triggers "$ARCHIVE"
$PSQL -c "REINDEX INDEX chunks_hnsw" -c "ANALYZE"
echo "restored $ARCHIVE"
