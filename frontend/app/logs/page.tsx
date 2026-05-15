"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

type RequestLog = {
  id: string;
  created_at: string;
  input_preview: string;
  response_preview?: string | null;
  task_type: string;
  priority: string;
  privacy: string;
  model: string;
  provider: string;
  cost: number;
  latency: number;
  input_tokens: number;
  output_tokens: number;
  contains_pii: boolean;
  injection_risk: string;
  blocked: boolean;
  fallback: boolean;
  fallback_reason?: string | null;
  routing_reason: string;
  trace_id: string;
  rag_used: boolean;
  rag_document?: string | null;
  rag_filename?: string | null;
  rag_chunks: number;
  rag_top_score?: number | null;
};

export default function LogsPage() {
  const [logs, setLogs] = useState<RequestLog[]>([]);
  const [selected, setSelected] = useState<RequestLog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadLogs() {
    try {
      setLoading(true);
      setError("");
      const data = await apiGet("/v1/logs");
      setLogs(data);
    } catch (e: any) {
      setError(e.message || "Failed to load request logs.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLogs();
  }, []);

  return (
    <div>
      <h2 className="text-3xl font-bold">Request Logs</h2>
      <p className="mt-2 text-slate-600">
        Audit every LLM request lifecycle with routing, safety, cost, latency, and RAG trace data.
      </p>

      <div className="mt-8 rounded-2xl border bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Recent Requests</h3>
          <button
            onClick={loadLogs}
            className="rounded-xl border bg-white px-4 py-2 text-sm hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>

        {loading && <p className="text-sm text-slate-500">Loading logs...</p>}

        {error && (
          <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </p>
        )}

        {!loading && !error && logs.length === 0 && (
          <p className="text-sm text-slate-500">
            No logs yet. Send a chat request first.
          </p>
        )}

        {!loading && !error && logs.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="p-3 font-semibold">Time</th>
                  <th className="p-3 font-semibold">Model</th>
                  <th className="p-3 font-semibold">Provider</th>
                  <th className="p-3 font-semibold">Cost</th>
                  <th className="p-3 font-semibold">Latency</th>
                  <th className="p-3 font-semibold">PII</th>
                  <th className="p-3 font-semibold">Blocked</th>
                  <th className="p-3 font-semibold">Fallback</th>
                  <th className="p-3 font-semibold">RAG</th>
                  <th className="p-3 font-semibold">Reason</th>
                </tr>
              </thead>

              <tbody>
                {logs.map((log) => (
                  <tr
                    key={log.id}
                    onClick={() => setSelected(log)}
                    className="cursor-pointer border-t hover:bg-slate-50"
                  >
                    <td className="whitespace-nowrap p-3">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="p-3">{log.model}</td>
                    <td className="p-3">{log.provider}</td>
                    <td className="p-3">${Number(log.cost || 0).toFixed(6)}</td>
                    <td className="p-3">{log.latency} ms</td>
                    <td className="p-3">{log.contains_pii ? "Yes" : "No"}</td>
                    <td className="p-3">{log.blocked ? "Yes" : "No"}</td>
                    <td className="p-3">{log.fallback ? "Yes" : "No"}</td>
                    <td className="p-3">{log.rag_used ? "Yes" : "No"}</td>
                    <td className="max-w-[420px] truncate p-3">
                      {log.routing_reason}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selected && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40">
          <div className="h-full w-full max-w-xl overflow-y-auto bg-white p-6 shadow-xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-semibold">Request Details</h3>
                <p className="mt-1 font-mono text-xs text-slate-500">
                  {selected.trace_id}
                </p>
              </div>

              <button
                onClick={() => setSelected(null)}
                className="rounded-xl border px-3 py-1 text-sm hover:bg-slate-50"
              >
                Close
              </button>
            </div>

            <div className="mt-6 space-y-3 text-sm">
              <Detail label="Priority" value={selected.priority} />
              <Detail label="Privacy" value={selected.privacy} />
              <Detail label="Task Type" value={selected.task_type} />
              <Detail label="Model" value={selected.model} />
              <Detail label="Provider" value={selected.provider} />
              <Detail label="Cost" value={`$${Number(selected.cost || 0).toFixed(6)}`} />
              <Detail label="Latency" value={`${selected.latency} ms`} />
              <Detail label="Input Tokens" value={String(selected.input_tokens)} />
              <Detail label="Output Tokens" value={String(selected.output_tokens)} />
              <Detail label="Contains PII" value={selected.contains_pii ? "Yes" : "No"} />
              <Detail label="Injection Risk" value={selected.injection_risk} />
              <Detail label="Blocked" value={selected.blocked ? "Yes" : "No"} />
              <Detail label="Fallback" value={selected.fallback ? "Yes" : "No"} />

              {selected.fallback_reason && (
                <Detail label="Fallback Reason" value={selected.fallback_reason} />
              )}

              <Detail label="RAG Used" value={selected.rag_used ? "Yes" : "No"} />

              {selected.rag_used && (
                <>
                  <Detail label="RAG Document" value={selected.rag_document || "-"} />
                  <Detail label="RAG Filename" value={selected.rag_filename || "-"} />
                  <Detail label="RAG Chunks" value={String(selected.rag_chunks)} />
                  <Detail
                    label="RAG Top Score"
                    value={
                      selected.rag_top_score !== null &&
                      selected.rag_top_score !== undefined
                        ? selected.rag_top_score.toFixed(4)
                        : "-"
                    }
                  />
                </>
              )}

              <Block label="Input Preview" value={selected.input_preview} />
              <Block label="Response Preview" value={selected.response_preview || "-"} />
              <Block label="Routing Reason" value={selected.routing_reason} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}

function Block({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="font-medium">{label}</p>
      <p className="mt-1 whitespace-pre-wrap rounded-xl bg-slate-50 p-3 text-slate-700">
        {value}
      </p>
    </div>
  );
}