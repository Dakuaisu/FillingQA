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
--
-- Groups on period_start and unit as well as period_end. Without period_start, a
-- quarter and the year-to-date figure ending the same day count as two "values"
-- of one fact -- finding #1's collision again -- and the query returned 5,146 rows
-- on the dev slice instead of 1,390 (2026-10-01). Rows are divergent groups, not
-- restatements; no restatement count is published until F-47 is resolved.
--
-- Not yet a restatement count fit for the README: companyfacts drops the iXBRL
-- `decimals` attribute, so one figure tagged exactly in a statement and rounded
-- in a note (AAPL LongTermDebt 90,678M vs 90,700M) is indistinguishable here
-- from a real restatement (TGT 2016 equity, 12,957M -> 12,965M). F-47.

WITH all_facts AS (
    SELECT cik, accession, concept, unit, period_start, period_end, value
      FROM xbrl_facts
    UNION ALL
    SELECT cik, accession, concept, unit, period_start, period_end, value
      FROM xbrl_facts_unlinked
)
SELECT
    cik,
    concept,
    unit,
    period_start,
    period_end,
    count(DISTINCT value)     AS variants,
    count(DISTINCT accession) AS filings_reporting,
    min(value)                AS min_value,
    max(value)                AS max_value
FROM all_facts
GROUP BY cik, concept, unit, period_start, period_end
HAVING count(DISTINCT value) > 1
ORDER BY variants DESC, cik, concept, period_end, period_start;
