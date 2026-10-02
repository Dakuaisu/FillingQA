import { ApiError } from "@/components/api-error";
import { metrics } from "@/lib/api";
import type { GateRow } from "@/lib/types";

export const dynamic = "force-dynamic";

const SOURCE_LABEL: Record<string, string> = {
  aggregate: "aggregate",
  xbrl_auto: "XBRL-templated slice",
  llm_seeded: "LLM-seeded slice",
  handwritten: "hand-written slice",
};

const sentence = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

const fmt = (v: number | string | null, d = 3) => (typeof v === "number" ? v.toFixed(d) : (v ?? "-"));

function StatusCell({ row }: { row: GateRow }) {
  const tone =
    row.status === "pass" ? "text-emerald-700" : row.status === "pending" ? "text-amber-700" : "text-red-700";
  return <td className={`py-1 pr-2 font-medium uppercase ${tone}`}>{row.status}</td>;
}

// PRD 10 eval dashboard. Renders only what /metrics returns: the gate as eval/compare.py
// computes it, model-free retrieval runs, development run ids (no values), owner-blocked items.
export default async function DashboardPage() {
  const r = await metrics();
  if (!r.ok) return <ApiError status={r.status} detail={r.detail} />;
  const m = r.body;
  const current = m.retrieval_runs.find((x) => x.current);
  const others = m.retrieval_runs.filter((x) => !x.current);

  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <h1 className="text-2xl font-semibold">Eval dashboard</h1>
        <div
          data-testid="gate-status"
          className={`rounded-md border px-4 py-3 text-sm ${m.gate.passed ? "border-emerald-300 bg-emerald-50" : "border-red-300 bg-red-50 text-red-900"}`}
        >
          <p className="font-semibold">{m.gate.passed ? "The CI eval gate passes." : "The CI eval gate fails."}</p>
          <p className="mt-1">
            {m.gate.run_id ? `Gated run ${m.gate.run_id}.` : `${sentence(m.gate.reason ?? "no gated run")}.`} Development runs
            cannot pass the gate and are not results.
          </p>
        </div>
        <div className="text-sm" data-testid="pending-with-run">
          <p>Even once a gated run exists, these stay pending:</p>
          <ul className="ml-5 list-disc">
            {m.pending_even_with_a_gated_run.map((x) => (
              <li key={x.metrics}>
                {x.metrics} ({x.reason}, {x.findings.join(", ")})
              </li>
            ))}
          </ul>
        </div>
        <table className="w-full text-xs [&_th]:pr-3" data-testid="gate-table">
          <thead className="text-left text-muted-foreground">
            <tr>
              <th className="py-1">Metric</th>
              <th>Scope</th>
              <th>Rule</th>
              <th>Threshold</th>
              <th>Value</th>
              <th>Status</th>
              <th>Why</th>
            </tr>
          </thead>
          <tbody>
            {m.gate.rows.map((row) => (
              <tr key={`${row.metric}-${row.scope}-${row.rule}`} className="border-t align-top" data-testid="gate-row">
                <td className="py-1 pr-2 font-mono">{row.metric}</td>
                <td className="pr-2">{row.scope}</td>
                <td className="pr-2">{row.rule}</td>
                <td className="pr-2">{fmt(row.threshold, 2)}</td>
                <td className="pr-2">{fmt(row.value)}</td>
                <StatusCell row={row} />
                <td className="text-muted-foreground">{row.why ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {current && (
        <section className="space-y-3" data-testid="retrieval-current">
          <h2 className="text-lg font-medium">Retrieval sufficiency (model-free)</h2>
          <p className="text-sm text-muted-foreground">
            Retrieval run <span className="font-mono">{current.run_id}</span>, {current.config}:{" "}
            {current.label}; dense search {current.dense_search}, sparse {current.sparse}. Sufficiency@10 against the
            thresholds in <span className="font-mono">eval/thresholds.yaml</span>.
          </p>
          <table className="w-full text-sm">
            <thead className="text-left text-muted-foreground">
              <tr>
                <th className="py-1">Slice</th>
                <th>Sufficiency@10</th>
                <th>Threshold</th>
                <th>Note</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(current.sufficiency_at_10).map(([src, v]) => (
                <tr key={src} className="border-t" data-testid={`retrieval-${src}`}>
                  <td className="py-1">{SOURCE_LABEL[src] ?? src}</td>
                  <td>{v.value === null ? "no items yet" : fmt(v.value)}</td>
                  <td>{fmt(v.threshold, 2)}</td>
                  <td className="text-xs text-muted-foreground">
                    {v.value !== null && v.threshold !== null ? (v.value >= v.threshold ? "meets" : "misses") : ""}
                    {current.notes[src] ? ` · ${current.notes[src]}` : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {others.length > 0 && (
            <p className="text-xs text-muted-foreground" data-testid="retrieval-earlier">
              Earlier model-free runs, superseded as the comparison point:{" "}
              {others
                .map((o) => `${o.run_id} (dense ${o.dense_search}, sparse ${o.sparse}, aggregate ${fmt(o.sufficiency_at_10.aggregate?.value ?? null)})`)
                .join("; ")}
              .
            </p>
          )}
        </section>
      )}

      <section className="space-y-3" data-testid="development-runs">
        <h2 className="text-lg font-medium">Development runs</h2>
        <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-900">
          Each is a development run on <code>claude_cli</code>, not a result. Listed by id only; no value from them is
          shown anywhere on this page.
        </div>
        <ul className="grid grid-cols-1 gap-1 text-xs sm:grid-cols-2">
          {m.development_runs.map((d) => (
            <li key={d.run_id} title={d.banner}>
              <span className="font-mono">{d.run_id}</span>{" "}
              <span className="text-muted-foreground">({d.files.map((f) => f.split("/").pop()).join(", ")})</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">What waits on the owner</h2>
        <table className="w-full text-sm" data-testid="owner-blocked">
          <tbody>
            {m.owner_blocked.map((o) => (
              <tr key={o.item} className="border-t align-top">
                <td className="py-1 pr-3">{o.item}</td>
                <td className="whitespace-nowrap text-xs text-muted-foreground">{o.findings.join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
