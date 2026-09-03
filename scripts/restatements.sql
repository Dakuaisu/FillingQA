-- restatements.sql -- PRD 6.5.2's divergence query.
--
-- Finds every concept/period whose reported value DISAGREES across filings: the
-- company restated a prior figure after an accounting change, reclassification,
-- or discovered error. PRD 6.5.2 turns the restatement trap into a feature --
-- surface these in the UI ("this figure was later restated to $X") and report
-- the count in the README.
--
-- May legitimately return zero rows on a small corpus; restatements are rare.
-- Zero here is a finding about the corpus, not a schema failure. Use
-- key_sanity.sql to test the key itself.
--
-- Reads both fact tables -- see docs/TRADEOFFS.md finding #3.

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
    count(DISTINCT value)     AS variants,
    count(DISTINCT accession) AS filings_reporting,
    min(value)                AS min_value,
    max(value)                AS max_value
FROM all_facts
GROUP BY cik, concept, period_end
HAVING count(DISTINCT value) > 1
ORDER BY variants DESC, cik, concept, period_end;
