"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

type BudgetUsage = {
  model: string;
  requests: number;
  estimated_cost: number;
};

export default function BudgetPage() {
  const [usage, setUsage] = useState<BudgetUsage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadUsage() {
    try {
      setLoading(true);
      setError("");
      const data = await apiGet("/v1/budget/usage");
      setUsage(data);
    } catch (e: any) {
      setError(e.message || "Failed to load budget usage.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsage();
  }, []);

  const totalRequests = usage.reduce((sum, row) => sum + row.requests, 0);
  const totalCost = usage.reduce((sum, row) => sum + row.estimated_cost, 0);

  return (
    <div>
      <h2 className="text-3xl font-bold">Budget & Usage</h2>
      <p className="mt-2 text-slate-600">
        Track estimated spend by model.
      </p>

      <div className="mt-8 grid grid-cols-1 gap-5 md:grid-cols-2">
        <MetricCard label="Total Requests" value={String(totalRequests)} />
        <MetricCard label="Total Estimated Cost" value={`$${totalCost.toFixed(6)}`} />
      </div>

      <div className="mt-8 rounded-2xl border bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Usage by Model</h3>
          <button
            onClick={loadUsage}
            className="rounded-xl border bg-white px-4 py-2 text-sm hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>

        {loading && <p className="text-sm text-slate-500">Loading usage...</p>}

        {error && (
          <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </p>
        )}

        {!loading && !error && usage.length === 0 && (
          <p className="text-sm text-slate-500">
            No usage yet. Send a chat request first.
          </p>
        )}

        {!loading && !error && usage.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="p-3 font-semibold">Model</th>
                  <th className="p-3 font-semibold">Requests</th>
                  <th className="p-3 font-semibold">Estimated Cost</th>
                </tr>
              </thead>
              <tbody>
                {usage.map((row) => (
                  <tr key={row.model} className="border-t">
                    <td className="p-3">{row.model}</td>
                    <td className="p-3">{row.requests}</td>
                    <td className="p-3">${row.estimated_cost.toFixed(6)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border bg-white p-6 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-3 text-3xl font-semibold">{value}</p>
    </div>
  );
}