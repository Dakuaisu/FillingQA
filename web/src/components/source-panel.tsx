"use client";

import { useEffect, useState } from "react";

import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import type { ChunkDetail } from "@/lib/types";

type Loaded =
  | { id: string; kind: "ok"; chunk: ChunkDetail }
  | { id: string; kind: "error"; status: number; detail: string };

// PRD 10 source panel: the chunk, its metadata and a link to the filing on sec.gov.
export function SourcePanel({ chunkId, onClose }: { chunkId: string | null; onClose: () => void }) {
  const [loaded, setLoaded] = useState<Loaded | null>(null);

  useEffect(() => {
    if (!chunkId) return;
    let live = true;
    fetch(`/web-api/chunks/${encodeURIComponent(chunkId)}`)
      .then(async (res) => {
        const body = await res.json().catch(() => ({}));
        if (!live) return;
        if (res.ok) setLoaded({ id: chunkId, kind: "ok", chunk: body as ChunkDetail });
        else setLoaded({ id: chunkId, kind: "error", status: res.status, detail: body.detail ?? res.statusText });
      })
      .catch((e) => live && setLoaded({ id: chunkId, kind: "error", status: 0, detail: String(e) }));
    return () => {
      live = false;
    };
  }, [chunkId]);

  const state = loaded && loaded.id === chunkId ? loaded : { kind: "loading" as const };

  return (
    <Sheet open={chunkId !== null} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-xl" data-testid="source-panel">
        <SheetHeader>
          <SheetTitle>Source</SheetTitle>
          <SheetDescription className="break-all font-mono text-xs">{chunkId}</SheetDescription>
        </SheetHeader>
        <div className="space-y-4 px-4 pb-6 text-sm">
          {state.kind === "loading" && <p>Loading source…</p>}
          {state.kind === "error" && (
            <p role="alert" data-testid="source-error">
              {state.status === 404 ? "This chunk was not found in the index." : `Could not load the source (${state.status}): ${state.detail}`}
            </p>
          )}
          {state.kind === "ok" && (
            <>
              <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
                <dt className="text-muted-foreground">Company</dt>
                <dd>
                  {state.chunk.company_name} ({state.chunk.ticker})
                </dd>
                <dt className="text-muted-foreground">Filing</dt>
                <dd>
                  {state.chunk.form_type} · FY{state.chunk.fiscal_year}
                  {state.chunk.fiscal_quarter ? ` Q${state.chunk.fiscal_quarter}` : ""} · {state.chunk.accession}
                </dd>
                <dt className="text-muted-foreground">Section</dt>
                <dd>
                  Item {state.chunk.item_code ?? "?"}
                  {state.chunk.section_title ? ` — ${state.chunk.section_title}` : ""}
                </dd>
                <dt className="text-muted-foreground">Type</dt>
                <dd>
                  {state.chunk.chunk_type}
                  {state.chunk.unit_scale ? ` · in ${state.chunk.unit_scale}` : ""}
                </dd>
                <dt className="text-muted-foreground">Page</dt>
                <dd>{state.chunk.page_hint ?? "not computed"}</dd>
              </dl>
              <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded bg-muted p-3 text-xs">{state.chunk.text}</pre>
              <a className="text-primary underline" href={state.chunk.source_url} target="_blank" rel="noreferrer">
                View the filing on sec.gov
              </a>
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
