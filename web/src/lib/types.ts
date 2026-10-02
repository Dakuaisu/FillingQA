// Shapes of the FilingQA API (PRD 9) as the server returns them.

export type Verdict = "PASS" | "PARTIAL" | "ABSTAIN" | "PENDING_NLI";

export interface Figure {
  value: number;
  unit: string;
  currency?: string | null;
  period?: string;
  concept?: string | null;
}

export interface Claim {
  claim_id: string;
  text: string;
  citations: string[];
  figure: Figure | null;
  entailment_score: number | null;
  numbers_grounded: boolean | null;
  unit_ok: boolean | "unknown" | null;
  xbrl: "verified" | "restatement" | "rounded" | "contradiction" | "no_fact" | "not_checked" | null;
  xbrl_fact_value: string | null;
  restated_in: string | null;
}

export interface Citation {
  chunk_id: string;
  ticker: string;
  company_name: string;
  form_type: string;
  fiscal_year: number;
  fiscal_quarter: number | null;
  item_code: string | null;
  section_title: string | null;
  page_hint: number | null;
  chunk_type: string;
  excerpt: string;
  source_url: string;
}

export interface ChunkDetail extends Citation {
  text: string;
  accession: string;
  unit_scale: string | null;
}

export interface QueryResponse {
  query_id: string;
  verdict: Verdict;
  backend: string;
  model_served: string | null;
  development: boolean;
  confidence: number | null;
  answer: string | null;
  verification_pending?: boolean;
  abstain_reason?: string;
  nearest_evidence?: { chunk_id: string; excerpt: string; rerank_score: number | null }[];
  claims: Claim[];
  citations: Citation[];
  metadata: {
    intent: string | null;
    cache_hit: boolean;
    latency_ms: number;
    cost_usd: number | null;
    cost_note: string | null;
    chunks_retrieved: number;
    chunks_used: number;
    trace_id: string | null;
  };
}

export type ApiResult<T> =
  | { ok: true; status: number; body: T }
  | { ok: false; status: number; detail: string };

export interface CorpusSummary {
  companies: { ticker: string; name: string; chunks: { form_type: string; fiscal_year: number; chunks: number }[] }[];
  total_chunks: number;
  last_ingested_at: string | null;
  freeze: { frozen_on: string; parser_version: string; chunker_version: string };
  filings: { listed: number; parsed: number; quarantined: number };
  quarantined: { accession: string; ticker: string; form: string; reason: string; finding: string }[];
}

export interface GateRow {
  metric: string;
  scope: string;
  rule: string;
  threshold: number | null;
  value: number | string | null;
  baseline: number | null;
  status: "pass" | "fail" | "pending";
  why: string | null;
}

export interface Metrics {
  gate: { passed: boolean; run_id: string | null; reason: string | null; rows: GateRow[] };
  retrieval_runs: {
    run_id: string;
    current: boolean;
    config: string;
    label: string;
    dense_search: string;
    sparse: string;
    sufficiency_at_10: Record<string, { value: number | null; threshold: number | null }>;
    notes: Record<string, string>;
  }[];
  gated_runs: string[];
  development_runs: { run_id: string; files: string[]; banner: string }[];
  pending_even_with_a_gated_run: { metrics: string; reason: string; findings: string[] }[];
  owner_blocked: { item: string; findings: string[] }[];
}
