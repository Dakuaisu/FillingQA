# FilingQA web

The PRD 10 frontend (Next.js): ask a question about the indexed 10-K and 10-Q filings and read a citation-checked answer with its sources.
Run it locally: `make serve` (the API on :8000), then `make web-dev` (this app on :3000).
Every screen showing generated text displays a "Development answer" banner whenever the API response says `development: true`; the banner comes from the response, never from config.
The e2e suite (`npm run test:e2e`, part of `make test`) starts its own mock API on :8765 and its own Next server on :3100, with responses captured from the real API (`e2e/fixtures/`, development responses).
