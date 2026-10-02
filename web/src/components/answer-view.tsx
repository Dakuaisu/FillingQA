"use client";

import { useState } from "react";

import { DevBanner } from "@/components/dev-banner";
import { SourcePanel } from "@/components/source-panel";
import { Badge } from "@/components/ui/badge";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card";
import type { Citation, Claim, QueryResponse } from "@/lib/types";

// Confidence as a band, not a decimal (PRD 10); the cut points are PRD 7.5's verdict ratios.
function band(c: number | null): string {
  if (c === null) return "Pending";
  if (c >= 0.9) return "High";
  if (c >= 0.6) return "Medium";
  return "Low";
}

function XbrlNote({ claim }: { claim: Claim }) {
  if (claim.xbrl === "verified") {
    return (
      <Badge variant="outline" className="border-emerald-400 text-emerald-700" data-testid="xbrl-badge">
        ✓ matches SEC XBRL
      </Badge>
    );
  }
  if (claim.xbrl === "restatement") {
    return (
      <span className="text-xs text-muted-foreground" data-testid="restatement-note">
        The cited filing&apos;s figure was later restated (filing {claim.restated_in}, value {claim.xbrl_fact_value}).
      </span>
    );
  }
  if (claim.xbrl === "rounded") {
    return (
      <span className="text-xs text-muted-foreground" data-testid="rounded-note">
        Matches SEC XBRL at the precision stated.
      </span>
    );
  }
  return null;
}

function Marker({ n, citation, onOpen }: { n: number; citation: Citation | undefined; onOpen: () => void }) {
  return (
    <HoverCard openDelay={150}>
      <HoverCardTrigger asChild>
        <button
          type="button"
          onClick={onOpen}
          className="ml-0.5 align-super text-xs font-semibold text-primary hover:underline"
          aria-label={`Source ${n}`}
          data-testid="citation-marker"
        >
          [{n}]
        </button>
      </HoverCardTrigger>
      {citation && (
        <HoverCardContent className="w-96 text-xs" data-testid="citation-preview">
          <p className="mb-1 font-medium">
            {citation.ticker} {citation.form_type} FY{citation.fiscal_year}
            {citation.fiscal_quarter ? ` Q${citation.fiscal_quarter}` : ""}
          </p>
          <p className="whitespace-pre-wrap text-muted-foreground">{citation.excerpt}</p>
        </HoverCardContent>
      )}
    </HoverCard>
  );
}

export function AnswerView({ data }: { data: QueryResponse }) {
  const [open, setOpen] = useState<string | null>(null);
  // Citations numbered in reading order: first appearance across the claims.
  const order = [...new Set(data.claims.flatMap((c) => c.citations))];
  const byId = new Map(data.citations.map((c) => [c.chunk_id, c]));
  const listed = order.map((id) => byId.get(id)).filter((c): c is Citation => c !== undefined);
  const seconds = (data.metadata.latency_ms / 1000).toFixed(1);
  const cost = data.metadata.cost_usd !== null ? `$${data.metadata.cost_usd.toFixed(4)}` : data.metadata.cost_note ?? "cost n/a";

  return (
    <div className="space-y-6">
      {data.development && <DevBanner backend={data.backend} model={data.model_served} />}

      {data.verdict === "ABSTAIN" ? (
        <section
          data-testid="abstention"
          className="rounded-lg border-2 border-dashed border-sky-300 bg-sky-50 p-5 text-sky-950"
        >
          <h2 className="text-lg font-semibold">No answer: the filings do not support one</h2>
          <p className="mt-2">{data.abstain_reason}</p>
          {data.nearest_evidence && data.nearest_evidence.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-medium">Nearest evidence found</h3>
              <ul className="mt-2 space-y-2">
                {data.nearest_evidence.map((e) => (
                  <li key={e.chunk_id}>
                    <button
                      type="button"
                      className="text-left text-xs text-sky-900 hover:underline"
                      onClick={() => setOpen(e.chunk_id)}
                    >
                      {e.excerpt.slice(0, 200)}…
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      ) : (
        <section data-testid="answer" className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge data-testid="verdict">{data.verdict === "PENDING_NLI" ? "Verification pending" : data.verdict}</Badge>
            <Badge variant="secondary" data-testid="confidence">
              Confidence: {band(data.confidence)}
            </Badge>
          </div>
          {data.verification_pending && (
            <p data-testid="pending-note" className="text-sm text-muted-foreground">
              Some claims are prose; their entailment check waits on a threshold that has not been set yet, so this
              answer&apos;s verdict is not final.
            </p>
          )}
          {data.verdict === "PARTIAL" && (
            <p className="text-sm text-muted-foreground">I could only partially verify this from the filings.</p>
          )}
          <ul className="space-y-3">
            {data.claims.map((c) => (
              <li key={c.claim_id} data-testid="claim" className="leading-relaxed">
                {c.text}
                {c.citations.map((id) => (
                  <Marker key={id} n={order.indexOf(id) + 1} citation={byId.get(id)} onOpen={() => setOpen(id)} />
                ))}
                <div className="mt-1">
                  <XbrlNote claim={c} />
                </div>
              </li>
            ))}
          </ul>
          <ol className="space-y-1 border-t pt-3 text-sm" data-testid="citations">
            {listed.map((c, i) => (
              <li key={c.chunk_id}>
                <button type="button" className="text-left hover:underline" onClick={() => setOpen(c.chunk_id)}>
                  [{i + 1}] {c.company_name} ({c.ticker}) {c.form_type} FY{c.fiscal_year}
                  {c.fiscal_quarter ? ` Q${c.fiscal_quarter}` : ""} · Item {c.item_code ?? "?"} · {c.chunk_type}
                </button>
              </li>
            ))}
          </ol>
        </section>
      )}

      <p className="text-xs text-muted-foreground" data-testid="latency-cost">
        {data.development ? "Development backend · " : ""}
        {seconds} s · {cost} · intent {data.metadata.intent ?? "?"} · {data.metadata.chunks_used} of{" "}
        {data.metadata.chunks_retrieved} retrieved chunks used
      </p>

      <SourcePanel chunkId={open} onClose={() => setOpen(null)} />
    </div>
  );
}
