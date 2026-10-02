export function ApiError({ status, detail }: { status: number; detail: string }) {
  return (
    <div role="alert" data-testid="error" className="rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-900">
      <p className="font-medium">{status === 503 ? "The API is unavailable right now." : `The request failed (${status}).`}</p>
      <p className="mt-1 text-xs text-red-800">{detail}</p>
    </div>
  );
}
