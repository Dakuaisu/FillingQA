-- 0003: fiscal_year and fiscal_quarter become nullable at ingest time.
--
-- PRD 8 declares filings.fiscal_year NOT NULL, which assumes the label is known
-- when the filing row is created. It is not. The submissions API carries
-- accessionNumber, filingDate, reportDate, form and primaryDocument, plus a
-- top-level fiscalYearEnd as an MMDD string -- but no per-filing fiscal-year
-- label. The issuer's own label lives in dei:DocumentFiscalYearFocus and
-- dei:DocumentFiscalPeriodFocus inside the filing's inline XBRL, which is not
-- read until parsing.
--
-- Deriving the label from filing_date or reportDate is exactly the heuristic
-- that TRADEOFFS.md finding #5 rejected. TGT is the counterexample: its fiscal
-- 2024 ends in February 2025, so "calendar year of reportDate" yields 2025
-- against a real label of 2024.
--
-- So: ingest writes period_end from reportDate, which is factual and needs no
-- derivation, and leaves the labels NULL. Parsing fills them in from the dei
-- tags. A filing that yields no DocumentFiscalYearFocus is quarantined by
-- validate.py rather than defaulted -- chunks.fiscal_year is NOT NULL in Phase 2
-- and feeds the metadata filter in PRD 7.1, so a wrong label there is worse than
-- a missing filing.

ALTER TABLE filings ALTER COLUMN fiscal_year DROP NOT NULL;

COMMENT ON COLUMN filings.fiscal_year IS
    'Issuer''s own fiscal year label, from dei:DocumentFiscalYearFocus at parse '
    'time. NULL until parsed. Not comparable across companies; use period_end.';

COMMENT ON COLUMN filings.fiscal_quarter IS
    'From dei:DocumentFiscalPeriodFocus at parse time. NULL until parsed, and '
    'NULL for 10-K.';
