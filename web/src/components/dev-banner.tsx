// Shown whenever a response says it came from a development backend (never from config).
export function DevBanner({ backend, model }: { backend: string; model: string | null }) {
  return (
    <div
      role="status"
      data-testid="dev-banner"
      className="rounded-md border border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-900"
    >
      Development answer: generated on <code>{backend}</code>
      {model ? (
        <>
          {" "}
          (<code>{model}</code>)
        </>
      ) : null}
      . Not a result, not a benchmark.
    </div>
  );
}
