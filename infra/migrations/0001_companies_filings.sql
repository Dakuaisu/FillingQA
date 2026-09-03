-- 0001: corpus tables. PRD 8.
--
-- pgvector is enabled here because the Phase 1 checklist asks for it, but no
-- column uses it until chunks land in Phase 2.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS companies (
    cik        CHAR(10) PRIMARY KEY,
    ticker     TEXT UNIQUE NOT NULL,
    name       TEXT NOT NULL,
    sic_code   TEXT,
    sector     TEXT
);

CREATE TABLE IF NOT EXISTS filings (
    accession      TEXT PRIMARY KEY,
    cik            CHAR(10) NOT NULL REFERENCES companies(cik),
    form_type      TEXT NOT NULL,
    filing_date    DATE NOT NULL,
    period_end     DATE NOT NULL,
    fiscal_year    INT  NOT NULL,
    fiscal_quarter INT,
    source_url     TEXT NOT NULL,
    raw_path       TEXT NOT NULL,
    content_hash   CHAR(64) NOT NULL,
    parse_status   TEXT NOT NULL DEFAULT 'pending',
    parse_score    REAL,
    parser_version TEXT,
    ingested_at    TIMESTAMPTZ DEFAULT now(),

    -- Deviations from PRD 8, approved 2026-08-30. See docs/TRADEOFFS.md.
    --
    -- norm_path: PRD 8 stores raw HTML at raw_path but gives normalized document
    -- text nowhere to live -- yet chunks.char_start/char_end and
    -- xbrl_spans.char_pos are both offsets into it. Without persisting the exact
    -- string those offsets index into, no offset in this database can be
    -- resolved later.
    norm_path      TEXT,
    -- parse_error: PRD 6.2 says to quarantine a document and inspect it, but
    -- parse_status alone cannot say why.
    parse_error    TEXT
);

CREATE INDEX IF NOT EXISTS filings_cik_fy_form ON filings (cik, fiscal_year, form_type);
CREATE INDEX IF NOT EXISTS filings_parse_status ON filings (parse_status);

-- fiscal_year carries the issuer's own label, not a normalized calendar year:
-- these eight companies do not share a fiscal calendar, so period_end is the only
-- cross-company-comparable field. Approved 2026-08-30.
COMMENT ON COLUMN filings.fiscal_year IS
    'Issuer''s own fiscal year label. Not comparable across companies; use period_end.';
