-- 0004: xbrl_facts_unlinked.fiscal_year becomes nullable.
--
-- companyfacts carries no `fy` on facts reported in non-periodic forms. Measured
-- 2026-10-01: AAPL 569 facts (all 8-K), TGT 49 (DEF 14A 40, S-3ASR 5, S-8 4),
-- COST 0. None belong to a 10-K or 10-Q, so none can reach xbrl_facts, whose
-- fiscal_year stays NOT NULL -- a linked fact without one should fail loudly.
--
-- They all land in xbrl_facts_unlinked, which exists to keep history for
-- restatement detection (TRADEOFFS finding #3). Inventing a year for them is the
-- derivation finding #5 rejected; dropping them loses facts we were asked to
-- keep. So the column follows the source: NULL when SEC reports none.

ALTER TABLE xbrl_facts_unlinked ALTER COLUMN fiscal_year DROP NOT NULL;
