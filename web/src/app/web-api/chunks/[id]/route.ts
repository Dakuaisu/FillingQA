import { chunk } from "@/lib/api";

// The source panel's chunk lookup, proxied server-side to the API.
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const r = await chunk(id);
  return Response.json(r.ok ? r.body : { detail: r.detail }, { status: r.status });
}
