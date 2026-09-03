-- key_sanity.sql -- deterministic proof that the xbrl_facts key is right.
--
-- Why this exists separately from restatements.sql:
--
-- PRD 14's Phase 1 exit says "run the restatement-detection query -- if it
-- returns rows, your key is right". That query looks for the same
-- (cik, concept, period_end) carrying DIFFERENT VALUES across filings, i.e. an
-- actual restatement. Restatements are rare. On a three-company, one-year dev
-- slice it can legitimately return zero rows with a perfectly correct key, which
-- would read as a schema bug and send you hunting for one that is not there.
--
-- This query tests the key itself rather than the rarity of restatements. Prior
-- year comparative columns guarantee it is non-zero once real data lands: a
-- FY2024 10-K reports FY2023 figures alongside FY2024, so FY2023 appears under
-- both the FY2023 filing's accession and the FY2024 filing's. If the key had
-- been (cik, concept, period_end, ...) without accession, the second insert
-- would have collided and one row would be gone -- so a zero result here, on a
-- populated database, means accession is not doing its job.
--
-- Reads both fact tables: out-of-window companyfacts rows live in
-- xbrl_facts_unlinked, and that longer history is exactly where cross-filing
-- coverage shows up. See docs/TRADEOFFS.md finding #3.

WITH all_facts AS (
    SELECT cik, accession, concept, period_start, period_end, value
      FROM xbrl_facts
    UNION ALL
    SELECT cik, accession, concept, period_start, period_end, value
      FROM xbrl_facts_unlinked
)
SELECT
    cik,
    concept,
    period_end,
    count(DISTINCT accession) AS filings_reporting,
    count(DISTINCT value)     AS distinct_values
FROM all_facts
GROUP BY cik, concept, period_end
HAVING count(DISTINCT accession) > 1
ORDER BY filings_reporting DESC, cik, concept, period_end
LIMIT 50;
