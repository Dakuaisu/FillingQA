import "server-only";

import type { ApiResult, ChunkDetail, CorpusSummary, Metrics, QueryResponse } from "@/lib/types";

// The FilingQA API (PRD 9). Server-side only: a live answer takes longer than the
// dev proxy's 30 s timeout, so the browser never calls /query directly.
export const API_BASE = process.env.API_BASE ?? "http://localhost:8000";

async function call<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, cache: "no-store" });
  } catch (e) {
    return { ok: false, status: 503, detail: `API unreachable at ${API_BASE}: ${String(e)}` };
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof body.detail === "string" ? body.detail : body.error ?? res.statusText;
    return { ok: false, status: res.status, detail };
  }
  return { ok: true, status: res.status, body: body as T };
}

export function query(question: string) {
  return call<QueryResponse>("/api/v1/query", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

export function chunk(id: string) {
  return call<ChunkDetail>(`/api/v1/chunks/${encodeURIComponent(id)}`);
}

export function corpusSummary() {
  return call<CorpusSummary>("/api/v1/corpus/summary");
}

export function metrics() {
  return call<Metrics>("/api/v1/metrics");
}
