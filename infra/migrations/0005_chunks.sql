-- 0005: chunks, and the span -> chunk link. PRD 8 and PRD 6.5.2.
--
-- The table is PRD 8's as written. Its HNSW and GIN indexes are NOT created here:
-- PRD 14 lists them at Phase 2 step 4, and building them before the bulk load
-- would maintain them row by row for nothing. chunks_meta is created now -- the
-- metadata filter (PRD 7.1) and resolution queries use it from the start.
--
-- item_code is part-qualified on a 10-Q ("I.1", "II.1A") and plain on a 10-K
-- ("1A"), because a 10-Q has two Item 1s (F-04). See TRADEOFFS, chunker decision 2.

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id        TEXT PRIMARY KEY,
    accession       TEXT NOT NULL REFERENCES filings(accession) ON DELETE CASCADE,
    cik             CHAR(10) NOT NULL,
    ticker          TEXT NOT NULL,
    form_type       TEXT NOT NULL,
    fiscal_year     INT  NOT NULL,
    fiscal_quarter  INT,
    item_code       TEXT,
    section_title   TEXT,
    chunk_type      TEXT NOT NULL,          -- 'prose' | 'table'
    text            TEXT NOT NULL,          -- with context header
    raw_text        TEXT NOT NULL,          -- for display
    token_count     INT  NOT NULL,          -- model sequence length, special tokens included
    page_hint       INT,                    -- not computed yet (F-55)
    char_start      INT,
    char_end        INT,
    unit_scale      TEXT,
    content_hash    CHAR(64) NOT NULL,
    embedding       VECTOR(768),
    tsv             TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    chunker_version TEXT
);

CREATE INDEX IF NOT EXISTS chunks_meta ON chunks (ticker, fiscal_year, form_type, item_code);

-- PRD 6.5.2 declares this column on xbrl_spans; 0002 deferred it until chunks
-- existed. SET NULL, not CASCADE: re-chunking a filing must not delete its spans,
-- which are parser output -- they are re-resolved instead (Phase 2 step 2).
ALTER TABLE xbrl_spans
    ADD COLUMN IF NOT EXISTS chunk_id TEXT REFERENCES chunks(chunk_id) ON DELETE SET NULL;
