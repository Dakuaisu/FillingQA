import { ApiError } from "@/components/api-error";
import { corpusSummary } from "@/lib/api";

export const dynamic = "force-dynamic";

// PRD 10 Corpus screen: what is in the index, and what is not.
export default async function CorpusPage() {
  const r = await corpusSummary();
  if (!r.ok) return <ApiError status={r.status} detail={r.detail} />;
  const c = r.body;
  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h1 className="text-2xl font-semibold">What is indexed</h1>
        <p className="text-sm text-muted-foreground" data-testid="corpus-totals">
          {c.filings.listed} filings listed in the frozen corpus: {c.filings.parsed} parsed and indexed,{" "}
          {c.filings.quarantined} quarantined (not indexed). {c.total_chunks.toLocaleString("en-US")} chunks.
        </p>
        <p className="text-xs text-muted-foreground" data-testid="freeze">
          Frozen {c.freeze.frozen_on} · parser {c.freeze.parser_version} · chunker {c.freeze.chunker_version}
          {c.last_ingested_at ? ` · last ingestion ${c.last_ingested_at.slice(0, 10)}` : ""} · never re-ingested
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Companies</h2>
        <table className="w-full text-sm" data-testid="companies">
          <thead className="text-left text-muted-foreground">
            <tr>
              <th className="py-1">Company</th>
              <th>Filings indexed (form, fiscal year: chunks)</th>
              <th className="text-right">Chunks</th>
            </tr>
          </thead>
          <tbody>
            {c.companies.map((co) => (
              <tr key={co.ticker} className="border-t align-top">
                <td className="py-2 pr-3">
                  {co.name} ({co.ticker})
                </td>
                <td className="py-2 text-xs text-muted-foreground">
                  {co.chunks.map((x) => `${x.form_type} FY${x.fiscal_year}: ${x.chunks}`).join(" · ")}
                </td>
                <td className="py-2 text-right">{co.chunks.reduce((n, x) => n + x.chunks, 0).toLocaleString("en-US")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Not indexed: quarantined filings</h2>
        <p className="text-sm text-muted-foreground">
          Filings whose parse failed a content check at the freeze. Questions about them cannot be answered from this
          index.
        </p>
        <ul className="space-y-2 text-sm" data-testid="quarantined">
          {c.quarantined.map((q) => (
            <li key={q.accession} className="rounded-md border px-3 py-2">
              <span className="font-medium">
                {q.ticker} {q.form}
              </span>{" "}
              <span className="font-mono text-xs">{q.accession}</span> · {q.finding}
              <p className="text-xs text-muted-foreground">{q.reason}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
