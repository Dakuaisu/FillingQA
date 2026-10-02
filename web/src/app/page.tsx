import Link from "next/link";

import { AskForm } from "@/components/ask-form";

// PRD 10: three example questions, one deliberately unanswerable. The unanswerable one
// is a question the pipeline actually declines (intent `unsupported`), not a staged panel.
const EXAMPLES = [
  { q: "What did Apple report as its research and development expense for fiscal 2023?" },
  {
    q: "How did Bank of America net interest income for the first two quarters of fiscal 2026 compare with the first two quarters of fiscal 2024?",
  },
  { q: "Should I buy NVIDIA stock right now?", label: "See how it handles a question it can't answer." },
];

export default function AskPage() {
  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h1 className="text-2xl font-semibold">Ask the filings</h1>
        <p className="text-sm text-muted-foreground">
          Answers come from 10-K and 10-Q filings of eight companies (fiscal 2023 to 2026). Every claim cites the chunk
          it came from and is checked against it; figures are checked against the filing&apos;s own XBRL data. When the
          filings do not support an answer, the system says so.
        </p>
      </section>
      <AskForm />
      <section className="space-y-3" aria-label="Example questions">
        <h2 className="text-sm font-medium">Try one</h2>
        <ul className="space-y-2">
          {EXAMPLES.map((e) => (
            <li key={e.q}>
              <Link
                href={`/answer?q=${encodeURIComponent(e.q)}`}
                className="block rounded-md border px-4 py-3 text-sm hover:bg-muted"
                data-testid="example"
              >
                {e.label && <span className="mb-1 block text-xs font-medium text-sky-700">{e.label}</span>}
                {e.q}
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
