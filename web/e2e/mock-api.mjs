// Serves the captured API fixtures for the e2e suite (no database, no model).
import { readFileSync, readdirSync } from "node:fs";
import { createServer } from "node:http";
import { join } from "node:path";

const dir = new URL("./fixtures/", import.meta.url).pathname;
const load = (f) => readFileSync(join(dir, f), "utf8");
const chunks = {};
for (const f of readdirSync(dir).filter((f) => f.startsWith("chunk") && f !== "chunk_404.json")) {
  const body = load(f);
  chunks[JSON.parse(body).chunk_id] = body;
}

function answerFor(question) {
  if (question.split(/\s+/).length > 500) return [422, load("query_422.development.json")];
  if (/buy|undervalued/i.test(question)) return [200, load("query_abstain_unsupported.development.json")];
  if (/net interest income/i.test(question)) return [200, load("query_pending_comparison.development.json")];
  return [200, load("query_pass_lookup.development.json")];
}

createServer((req, res) => {
  const send = (status, body) => {
    res.writeHead(status, { "content-type": "application/json" });
    res.end(body);
  };
  if (req.method === "POST" && req.url === "/api/v1/query") {
    let raw = "";
    req.on("data", (d) => (raw += d));
    req.on("end", () => send(...answerFor(JSON.parse(raw || "{}").question ?? "")));
    return;
  }
  if (req.method === "GET" && req.url === "/api/v1/metrics") return send(200, load("metrics.json"));
  if (req.method === "GET" && req.url === "/api/v1/corpus/summary") return send(200, load("corpus_summary.json"));
  const m = req.url?.match(/^\/api\/v1\/chunks\/(.+)$/);
  if (req.method === "GET" && m) {
    const id = decodeURIComponent(m[1]);
    return chunks[id] ? send(200, chunks[id]) : send(404, load("chunk_404.json"));
  }
  send(404, JSON.stringify({ detail: "not mocked" }));
}).listen(Number(process.env.MOCK_PORT ?? 8765));
