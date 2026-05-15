"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const CHART_COLORS = [
  "#2563eb", // blue
  "#16a34a", // green
  "#f97316", // orange
  "#dc2626", // red
  "#7c3aed", // purple
  "#0891b2", // cyan
];

type DashboardSummary = {
  total_requests: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  p95_latency_ms?: number;
  fallback_count: number;
  safety_blocks: number;
  pii_detections?: number;
  active_models?: number;
  estimated_cost_saved_usd?: number;
  model_distribution: {
    model: string;
    requests?: number;
    count?: number;
    cost_usd?: number;
    avg_latency_ms?: number;
  }[];
  recent_requests?: {
    id: string;
    created_at: string;
    model: string;
    provider: string;
    cost_usd: number;
    latency_ms: number;
    contains_pii: boolean;
    blocked: boolean;
    fallback_used: boolean;
    routing_reason: string;
  }[];
};

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary>({
    total_requests: 0,
    total_cost_usd: 0,
    avg_latency_ms: 0,
    p95_latency_ms: 0,
    fallback_count: 0,
    safety_blocks: 0,
    pii_detections: 0,
    active_models: 0,
    estimated_cost_saved_usd: 0,
    model_distribution: [],
    recent_requests: [],
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const data = await apiGet<DashboardSummary>("/v1/dashboard/summary");

        const normalizedModelDistribution = data.model_distribution.map((m) => ({
          ...m,
          requests: m.requests ?? m.count ?? 0,
          cost_usd: m.cost_usd ?? 0,
          avg_latency_ms: m.avg_latency_ms ?? 0,
        }));

        setSummary({
          ...data,
          p95_latency_ms: data.p95_latency_ms ?? 0,
          pii_detections: data.pii_detections ?? 0,
          active_models: data.active_models ?? normalizedModelDistribution.length,
          estimated_cost_saved_usd: data.estimated_cost_saved_usd ?? 0,
          model_distribution: normalizedModelDistribution,
          recent_requests: data.recent_requests ?? [],
        });
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  return (
    <div>
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-3xl font-bold">Deployment Dashboard</h2>
          <p className="mt-2 text-slate-600">
            Operate and monitor cost-aware LLM inference across local, mock, and premium providers.
          </p>
        </div>

        <button
          onClick={() => window.location.reload()}
          className="rounded-xl border bg-white px-4 py-2 text-sm hover:bg-slate-50"
        >
          Refresh
        </button>
      </div>

      {loading && (
        <div className="mt-8 rounded-2xl bg-white p-6 border shadow-sm text-slate-500">
          Loading dashboard...
        </div>
      )}

      {!loading && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mt-8">
            <MetricCard title="Total Requests" value={summary.total_requests} />
            <MetricCard title="Total Cost" value={`$${summary.total_cost_usd}`} />
            <MetricCard
              title="Estimated Cost Saved"
              value={`$${summary.estimated_cost_saved_usd ?? 0}`}
            />
            <MetricCard
              title="Active Models"
              value={summary.active_models ?? summary.model_distribution.length}
            />

            <MetricCard title="Average Latency" value={`${summary.avg_latency_ms} ms`} />
            <MetricCard title="p95 Latency" value={`${summary.p95_latency_ms ?? 0} ms`} />
            <MetricCard title="Fallbacks" value={summary.fallback_count} />
            <MetricCard title="Safety Blocks" value={summary.safety_blocks} />
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mt-8">
            <div className="xl:col-span-2 rounded-2xl bg-white p-5 border shadow-sm">
              <h3 className="text-lg font-semibold">Requests by Model</h3>
              <p className="text-sm text-slate-500 mt-1">
                How traffic is distributed across model routes.
              </p>

              <div className="h-80 mt-6">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={summary.model_distribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="model" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar
                      dataKey="requests"
                      fill="#2563eb"
                      radius={[8, 8, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-2xl bg-white p-5 border shadow-sm">
              <h3 className="text-lg font-semibold">Traffic Split</h3>
              <p className="text-sm text-slate-500 mt-1">
                Model share by request count.
              </p>

              <div className="h-80 mt-6">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={summary.model_distribution}
                      dataKey="requests"
                      nameKey="model"
                      outerRadius={110}
                      label
                    >
                      {summary.model_distribution.map((_, index) => (
                        <Cell
                          key={index}
                          fill={CHART_COLORS[index % CHART_COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-8">
            <div className="rounded-2xl bg-white p-5 border shadow-sm">
              <h3 className="text-lg font-semibold">Cost by Model</h3>
              <p className="text-sm text-slate-500 mt-1">
                Estimated spend grouped by model.
              </p>

              <div className="h-72 mt-6">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={summary.model_distribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="model" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar
                      dataKey="cost_usd"
                      fill="#16a34a"
                      radius={[8, 8, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-2xl bg-white p-5 border shadow-sm">
              <h3 className="text-lg font-semibold">Average Latency by Model</h3>
              <p className="text-sm text-slate-500 mt-1">
                Average response latency per route.
              </p>

              <div className="h-72 mt-6">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={summary.model_distribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="model" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar
                      dataKey="avg_latency_ms"
                      fill="#f97316"
                      radius={[8, 8, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="rounded-2xl bg-white p-5 border shadow-sm mt-8">
            <h3 className="text-lg font-semibold">Recent Requests</h3>
            <p className="text-sm text-slate-500 mt-1">
              Latest requests with model, latency, cost, safety, and routing decision.
            </p>

            <div className="overflow-x-auto mt-5">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-left">
                  <tr>
                    <th className="p-3">Time</th>
                    <th className="p-3">Model</th>
                    <th className="p-3">Provider</th>
                    <th className="p-3">Cost</th>
                    <th className="p-3">Latency</th>
                    <th className="p-3">PII</th>
                    <th className="p-3">Blocked</th>
                    <th className="p-3">Fallback</th>
                    <th className="p-3">Reason</th>
                  </tr>
                </thead>

                <tbody>
                  {(summary.recent_requests ?? []).map((r) => (
                    <tr key={r.id} className="border-t hover:bg-slate-50">
                      <td className="p-3">{new Date(r.created_at).toLocaleString()}</td>
                      <td className="p-3 font-medium">{r.model}</td>
                      <td className="p-3">{r.provider}</td>
                      <td className="p-3">${r.cost_usd}</td>
                      <td className="p-3">{r.latency_ms} ms</td>
                      <td className="p-3">{r.contains_pii ? "Yes" : "No"}</td>
                      <td className="p-3">{r.blocked ? "Yes" : "No"}</td>
                      <td className="p-3">{r.fallback_used ? "Yes" : "No"}</td>
                      <td className="p-3 max-w-md">{r.routing_reason}</td>
                    </tr>
                  ))}

                  {(summary.recent_requests ?? []).length === 0 && (
                    <tr>
                      <td colSpan={9} className="p-6 text-slate-500">
                        No recent request rows available. Update the backend dashboard endpoint to include recent_requests.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function MetricCard({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="rounded-2xl bg-white p-5 shadow-sm border border-slate-200 hover:shadow-md transition">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-2 text-3xl font-semibold text-slate-950">{value}</p>
    </div>
  );
}