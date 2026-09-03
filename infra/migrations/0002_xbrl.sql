-- 0002: XBRL ground truth. PRD 6.5.2.
--
-- Two sources, used differently (PRD 6.5.1):
--   xbrl_facts -- from the companyfacts API. Tells you the answer.
--   xbrl_spans -- from inline <ix:*> tags during parsing. Tells you where it lives.

CREATE TABLE IF NOT EXISTS xbrl_facts (
    fact_id        BIGSERIAL PRIMARY KEY,
    cik            CHAR(10) NOT NULL,
    accession      TEXT NOT NULL REFERENCES filings(accession) ON DELETE CASCADE,
    concept        TEXT NOT NULL,
    label          TEXT,
    value          NUMERIC NOT NULL,   -- base units, never scaled. PRD 6.5.2 Trap 2.
    unit           TEXT NOT NULL,
    period_start   DATE,               -- NULL for instant facts (balance sheet)
    period_end     DATE NOT NULL,
    fiscal_year    INT NOT NULL,
    fiscal_period  TEXT,
    form_type      TEXT,
    is_comparative BOOLEAN NOT NULL DEFAULT FALSE,

    -- Trap 1 (PRD 6.5.2): accession is part of the key. Keying on cik collides
    -- on restatements -- the same period reported twice with different values --
    -- and at runtime that presents as a contradiction against a correct answer,
    -- forcing a false ABSTAIN.
    --
    -- period_start is also part of the key, which the PRD does not have. A Q2 or
    -- Q3 10-Q tags income-statement concepts for BOTH the three-month and the
    -- year-to-date duration. In companyfacts those two entries share accn, end,
    -- fp, fy and unit, and differ only in start -- so the PRD's key collides on
    -- them, drops one, and then validates a quarterly claim against a YTD fact.
    -- Same damage pattern as Trap 1. 72 of the 96 corpus filings are 10-Qs.
    -- Approved 2026-08-30; see docs/TRADEOFFS.md finding #1.
    --
    -- NULLS NOT DISTINCT (pg15+) so instant facts, whose period_start is NULL,
    -- still deduplicate against each other.
    CONSTRAINT xbrl_facts_key
        UNIQUE NULLS NOT DISTINCT
        (accession, concept, period_start, period_end, fiscal_period, unit)
);

CREATE INDEX IF NOT EXISTS xbrl_facts_cik_concept_period
    ON xbrl_facts (cik, concept, period_end);
CREATE INDEX IF NOT EXISTS xbrl_facts_accession_concept
    ON xbrl_facts (accession, concept);

-- No CHECK on fiscal_period. The PRD comments it as 'FY' | 'Q1' | 'Q2' | 'Q3',
-- but that enumeration has not been verified against real companyfacts output.
-- Constrain it once the data has been seen, not before.


-- Facts whose accession is not in filings. companyfacts returns every fact a
-- company has ever tagged -- 8-Ks, S-1s, 10-Ks from a decade ago -- while filings
-- holds only 3 years of 10-K/10-Q, so the foreign key above would reject most
-- rows outright (PRD 6.1 stores them wholesale and does not account for this).
--
-- Kept rather than dropped: the restatement-detection query in PRD 6.5.2 gets
-- materially better with a longer history, since a figure restated in a later
-- filing is only visible when both filings' facts are present.
-- Approved 2026-08-30; see docs/TRADEOFFS.md finding #3.
CREATE TABLE IF NOT EXISTS xbrl_facts_unlinked (
    fact_id       BIGSERIAL PRIMARY KEY,
    cik           CHAR(10) NOT NULL,
    accession     TEXT NOT NULL,      -- deliberately no FK
    concept       TEXT NOT NULL,
    label         TEXT,
    value         NUMERIC NOT NULL,
    unit          TEXT NOT NULL,
    period_start  DATE,
    period_end    DATE NOT NULL,
    fiscal_year   INT NOT NULL,
    fiscal_period TEXT,
    form_type     TEXT,

    CONSTRAINT xbrl_facts_unlinked_key
        UNIQUE NULLS NOT DISTINCT
        (accession, concept, period_start, period_end, fiscal_period, unit)
);

CREATE INDEX IF NOT EXISTS xbrl_facts_unlinked_cik_concept_period
    ON xbrl_facts_unlinked (cik, concept, period_end);


CREATE TABLE IF NOT EXISTS xbrl_spans (
    span_id     BIGSERIAL PRIMARY KEY,
    accession   TEXT NOT NULL REFERENCES filings(accession) ON DELETE CASCADE,
    concept     TEXT NOT NULL,
    context_ref TEXT NOT NULL,
    value       NUMERIC NOT NULL,   -- after applying scale and sign
    scale       INT,
    raw_text    TEXT,               -- '7,286' as printed in the document

    -- char_start/char_end are offsets into the NORMALIZED document text at
    -- filings.norm_path -- the same coordinate system Phase 2's chunks use.
    -- PRD 6.2 says to harvest spans "before you flatten", keyed by character
    -- offset, but PRD 6.2's Block.char_start is an offset into normalized text.
    -- Those are different strings. Extraction and flattening are therefore one
    -- traversal that records each ix element's range in the text it emits.
    -- Approved 2026-08-30; see docs/TRADEOFFS.md, Phase 1 decision 4.
    --
    -- PRD 6.5.2 also declares chunk_id REFERENCES chunks(chunk_id) here. chunks
    -- does not exist until Phase 2, which adds the column and the key.
    char_start  INT NOT NULL,
    char_end    INT NOT NULL
);

CREATE INDEX IF NOT EXISTS xbrl_spans_accession_concept
    ON xbrl_spans (accession, concept);
