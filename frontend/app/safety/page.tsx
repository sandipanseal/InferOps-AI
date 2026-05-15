import { apiGet } from "@/lib/api";

type SafetyData = {
  summary: {
    pii_detections: number;
    blocked_requests: number;
    high_risk_injection_attempts: number;
    medium_risk_injection_attempts: number;
  };
  events: {
    id: string;
    created_at: string;
    input_preview: string;
    model: string;
    provider: string;
    contains_pii: boolean;
    prompt_injection_risk: string;
    blocked: boolean;
    routing_reason: string;
    trace_id: string;
  }[];
};

export default async function SafetyPage() {
  let data: SafetyData = {
    summary: {
      pii_detections: 0,
      blocked_requests: 0,
      high_risk_injection_attempts: 0,
      medium_risk_injection_attempts: 0,
    },
    events: [],
  };

  try {
    data = await apiGet<SafetyData>("/v1/safety/events");
  } catch {}

  return (
    <div>
      <h2 className="text-3xl font-bold">Safety Center</h2>
      <p className="mt-2 text-slate-600">
        Monitor PII detections, prompt-injection attempts, and blocked requests.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mt-8">
        <Metric title="PII Detections" value={data.summary.pii_detections} />
        <Metric title="Blocked Requests" value={data.summary.blocked_requests} />
        <Metric title="High-Risk Attempts" value={data.summary.high_risk_injection_attempts} />
        <Metric title="Medium-Risk Attempts" value={data.summary.medium_risk_injection_attempts} />
      </div>

      <div className="mt-8 rounded-2xl bg-white border shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="p-3">Time</th>
              <th className="p-3">Event</th>
              <th className="p-3">Risk</th>
              <th className="p-3">Action</th>
              <th className="p-3">Model</th>
              <th className="p-3">Trace</th>
              <th className="p-3">Reason</th>
            </tr>
          </thead>

          <tbody>
            {data.events.map((e) => {
              const eventType = e.blocked
                ? "Blocked prompt injection"
                : e.contains_pii
                ? "PII detected"
                : "Risky prompt";

              return (
                <tr key={e.id} className="border-t">
                  <td className="p-3">{new Date(e.created_at).toLocaleString()}</td>
                  <td className="p-3 font-medium">{eventType}</td>
                  <td className="p-3">{e.prompt_injection_risk}</td>
                  <td className="p-3">{e.blocked ? "Blocked" : "Routed safely"}</td>
                  <td className="p-3">{e.model}</td>
                  <td className="p-3 font-mono text-xs">{e.trace_id}</td>
                  <td className="p-3 max-w-md">{e.routing_reason}</td>
                </tr>
              );
            })}

            {data.events.length === 0 && (
              <tr>
                <td colSpan={7} className="p-6 text-slate-500">
                  No safety events yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: number }) {
  return (
    <div className="rounded-2xl bg-white p-5 shadow-sm border">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-2 text-3xl font-semibold">{value}</p>
    </div>
  );
}