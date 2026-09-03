# FilingQA — working agreement

The full spec is `docs/PRD.md`. Read the relevant section before implementing;
don't infer the design from filenames or from what seems reasonable.

## What this project is

A citation-grounded QA system over SEC filings. The point of the project is the
**evaluation harness** — the RAG pipeline exists to be measured. Every decision
should be weighed by "does this make the measurement more trustworthy?"

I am building this to demonstrate my own engineering ability. I need to
understand every component well enough to defend it in a technical interview.
Prefer clear code I can follow over clever code I can't.

## Absolute rules — violating these ruins the project

1. **Never fabricate a number.** No hardcoded metric values, no placeholder
   scores, no example outputs presented as real results. If a metric can't be
   computed yet, raise `NotImplementedError`. A stub that returns `0.87` is
   worse than a crash, because I might ship it.

2. **Never generate fake corpus data.** No synthetic "SEC filings," no mock
   XBRL facts, no invented tickers. If you need data to test against, fetch
   real filings or tell me you're blocked. Fixtures must be real filings,
   committed as files, with their accession numbers recorded.

3. **Faithfulness is computed on `claims_pre`, always.** The generator's raw
   output, before verification strips anything. Computing it on post-verified
   claims makes it circular and the metric becomes meaningless. If you touch
   metric code, re-read PRD §11.2 first. This is the single most likely way
   this project silently breaks.

4. **Thresholds live in `eval/thresholds.yaml` and nowhere else.** Never
   hardcode a threshold in Python. Never restate one in a docstring.

5. **Don't mark work complete that you haven't verified runs.** "Should work"
   is not done. Run it.

## Domain traps — these are in the PRD and they bite

- `xbrl_facts` is keyed on `(accession, concept, period_end, fiscal_period, unit)`.
  **`accession` is part of the key.** Keying on `cik` collides on restatements and
  causes false ABSTAINs. PRD §6.5.2 Trap 1.
- Extract inline-XBRL `<ix:*>` spans **before** flattening HTML. Flattening
  first destroys the character offsets, which are the whole point.
- `companyfacts` reports base units; documents print scaled values. Normalize
  both sides. PRD §6.5.2 Trap 2.
- NLI is **never** applied to claims containing figures. Numeric grounding
  handles those. PRD §7.5.
- NLI premise is a **single** cited chunk, never concatenated chunks — the
  model's context window truncates silently.
- Every gated metric is broken out by `source` (`xbrl_auto` / `llm_seeded` /
  `handwritten`). The aggregate alone is carried by the easy 39%. PRD §11.2.
- EDGAR: 8 req/s ceiling, descriptive `User-Agent` with a real email. Getting
  IP-blocked costs days.

## Process

- **One phase at a time.** Don't scaffold ahead. Don't create empty files for
  future phases.
- **End every task with a command I can run to verify it.** Show me the actual
  output, not a description of what it would print.
- **Ask before adding a dependency.** Say what it does and what it replaces.
- **Ask before making a design decision the PRD doesn't cover.** Don't silently
  pick and move on.
- **Stop and ask if something in the PRD looks wrong.** It's been through two
  review passes but it's not infallible. If the spec conflicts with what you're
  seeing in real data, the data wins — tell me.

## Testing

Pure functions get real unit tests. Especially:
- number normalization (`$7,286` / `7,286` / `7286` / `(7,286)` / `7.286 billion`)
- unit-scale conversion
- RRF fusion
- evidence-set sufficiency check

Parser output gets snapshot tests against committed real filings.

## Style

- Python 3.11+, type hints, `ruff` clean.
- Comment the *why* on anything non-obvious, especially domain quirks. I'll be
  re-reading this code months from now to prep for interviews.
- No emoji in code or logs.

## Reporting

End every turn with at most 5 bullets. Implementation detail goes in
`docs/WORKLOG.md`, not in your message to me.

Then one of:

    DECISIONS NEEDED:
    - <question> — <what breaks if we get it wrong>
    (max 3, or omit entirely)

or

    PROCEEDING: <next step>

Keep `docs/OPEN.md` current — update it whenever a finding opens or resolves.
