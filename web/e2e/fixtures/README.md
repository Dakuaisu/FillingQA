# e2e fixtures: development responses

Captured on 2026-10-02 from the local FilingQA API (`make serve`) answering on
the `claude_cli` development backend. Every `/query` fixture carries
`"development": true`: these are recordings of what the API returned, used to
test the screens, never results and never README material (F-59).

- `query_pass_lookup.development.json`: "What did Apple report as its research
  and development expense for fiscal 2023?" (PASS, one claim, XBRL verified)
- `query_pending_comparison.development.json`: "How did Bank of America net
  interest income for the first two quarters of fiscal 2026 compare with the
  first two quarters of fiscal 2024?" (PENDING_NLI: two XBRL-verified figure
  claims and one prose claim waiting on the NLI threshold, F-125)
- `query_abstain_unsupported.development.json`: "Should I buy NVIDIA stock right
  now?" (ABSTAIN, intent unsupported)
- `query_422.development.json`: a 602-token question (the 422 error body; no
  answer, so no `development` field, labelled by name)
- `chunk.json`, `chunk_*.json`: `GET /api/v1/chunks/{id}` for the cited chunks
  (database records of the frozen corpus, no generated text)
- `chunk_404.json`: `GET /api/v1/chunks/nope`

No restatement response was seen live, so no fixture exercises the
restatement annotation.
