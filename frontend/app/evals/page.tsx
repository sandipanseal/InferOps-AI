"use client";

import { useState } from "react";
import { apiPost } from "@/lib/api";

export default function EvalsPage() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function runEvals() {
    setLoading(true);
    try {
      const data = await apiPost("/v1/evals/run", {});
      setResult(data);
    } finally {
      setLoading(false);
    }
  }

  const routingAccuracy = result
    ? `${Math.round(result.routing_accuracy * 100)}%`
    : "0%";

  const piiAccuracy = result
    ? `${Math.round(result.pii_detection_accuracy * 100)}%`
    : "0%";

  const injectionAccuracy = result
    ? `${Math.round(result.prompt_injection_block_accuracy * 100)}%`
    : "0%";

  return (
    <div>
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-3xl font-bold">Evaluation Center</h2>
          <p className="mt-2 text-slate-600">
            Validate routing, PII safety, injection blocking, and deployment behavior.
          </p>
        </div>

        <button
          onClick={runEvals}
          disabled={loading}
          className="rounded-xl bg-slate-950 text-white px-5 py-3 disabled:opacity-50"
        >
          {loading ? "Running..." : "Run Evaluation Suite"}
        </button>
      </div>

      {!result && (
        <div className="mt-8 rounded-2xl bg-white p-6 border shadow-sm text-slate-500">
          No evaluation run yet.
        </div>
      )}

      {result && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mt-8">
            <Metric title="Routing Accuracy" value={routingAccuracy} />
            <Metric title="PII Detection Accuracy" value={piiAccuracy} />
            <Metric title="Injection Block Accuracy" value={injectionAccuracy} />
            <Metric
              title="Cases Passed"
              value={`${result.passed_cases}/${result.total_cases}`}
            />
          </div>

          <div className="mt-8 rounded-2xl bg-white border shadow-sm overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-left">
                <tr>
                  <th className="p-3">Case</th>
                  <th className="p-3">Expected</th>
                  <th className="p-3">Actual</th>
                  <th className="p-3">Priority</th>
                  <th className="p-3">Privacy</th>
                  <th className="p-3">Complexity</th>
                  <th className="p-3">Budget Left</th>
                  <th className="p-3">Passed</th>
                  <th className="p-3">Reason</th>
                </tr>
              </thead>

              <tbody>
                {result.cases.map((c: any) => (
                  <tr key={c.name} className="border-t">
                    <td className="p-3 font-medium">{c.name}</td>

                    <td className="p-3">
                      {c.expected_model} / {c.expected_provider}
                    </td>

                    <td className="p-3">
                      {c.actual_model} / {c.actual_provider}
                    </td>

                    <td className="p-3">{c.priority}</td>
                    <td className="p-3">{c.privacy}</td>
                    <td className="p-3">{c.complexity_score ?? "-"}</td>
                    <td className="p-3">
                      {c.budget_remaining_usd !== undefined
                        ? `$${c.budget_remaining_usd}`
                        : "-"}
                    </td>

                    <td className="p-3">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-medium ${
                          c.passed
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-red-50 text-red-700"
                        }`}
                      >
                        {c.passed ? "Yes" : "No"}
                      </span>
                    </td>

                    <td className="p-3 max-w-md">{c.routing_reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl bg-white p-5 border shadow-sm">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-2 text-3xl font-semibold">{value}</p>
    </div>
  );
}