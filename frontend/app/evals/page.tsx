"use client";

import { useState } from "react";
import { apiPost } from "@/lib/api";

type RagasScenario = {
  id: string;
  label: string;
  description: string;
  expected: "high" | "low";
  question: string;
  answer: string;
  ground_truth: string;
};

const RAGAS_SCENARIOS: RagasScenario[] = [
  {
    id: "grounded",
    label: "Grounded answer",
    description:
      "Answer faithfully restates the runbook. Faithfulness should be ~1.0.",
    expected: "high",
    question: "What is the rollback procedure?",
    answer:
      "Disable premium routing, route to local Ollama, inspect fallback logs.",
    ground_truth:
      "Disable premium model routing, route requests to local Ollama, inspect fallback logs.",
  },
  {
    id: "hallucinated",
    label: "Hallucinated answer",
    description:
      "Answer invents a procedure not in the runbook. Faithfulness should drop sharply.",
    expected: "low",
    question: "What is the rollback procedure?",
    answer:
      "Roll back by flipping the master switch in the AWS console.",
    ground_truth:
      "Disable premium model routing, route requests to local Ollama, inspect fallback logs.",
  },
  {
    id: "partial",
    label: "Partial answer",
    description:
      "Answer is grounded but incomplete. Faithfulness stays high; recall would be lower.",
    expected: "high",
    question: "What is the rollback procedure?",
    answer: "Disable premium routing.",
    ground_truth:
      "Disable premium model routing, route requests to local Ollama, inspect fallback logs.",
  },
];

export default function EvalsPage() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const [judgeResult, setJudgeResult] = useState<any>(null);
  const [judgeLoading, setJudgeLoading] = useState(false);

  const [ragasResult, setRagasResult] = useState<any>(null);
  const [ragasLoading, setRagasLoading] = useState(false);
  const [ragasScenarioId, setRagasScenarioId] = useState<string | null>(null);

  async function runEvals() {
    setLoading(true);
    try {
      const data = await apiPost("/v1/evals/run", {});
      setResult(data);
    } finally {
      setLoading(false);
    }
  }

  async function runJudge() {
    setJudgeLoading(true);
    try {
      const data = await apiPost("/v1/evals/judge", { judge_model: "gpt-4o" });
      setJudgeResult(data);
    } catch (e: any) {
      setJudgeResult({ ok: false, error: e?.message || "judge call failed" });
    } finally {
      setJudgeLoading(false);
    }
  }

  async function runRagasScenario(scenario: RagasScenario) {
    setRagasLoading(true);
    setRagasScenarioId(scenario.id);
    setRagasResult(null);
    try {
      const data = await apiPost("/v1/evals/ragas", {
        samples: [
          {
            question: scenario.question,
            answer: scenario.answer,
            ground_truth: scenario.ground_truth,
          },
        ],
        top_k: 4,
      });
      setRagasResult({ ...data, scenario });
    } catch (e: any) {
      setRagasResult({
        ok: false,
        error: e?.message || "ragas call failed",
        scenario,
      });
    } finally {
      setRagasLoading(false);
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

      {/* ---------- LLM-as-Judge ---------- */}
      <div className="mt-12 rounded-2xl bg-white p-6 border shadow-sm">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-2xl font-bold">LLM-as-Judge (GPT-4)</h3>
            <p className="mt-1 text-slate-600">
              Runs the routing eval suite, then asks GPT-4 to score every routing
              decision 1-5 with a written rationale. Catches "passed for the
              wrong reason" cases that exact-match evals miss.
            </p>
          </div>
          <button
            onClick={runJudge}
            disabled={judgeLoading}
            className="rounded-xl bg-slate-950 text-white px-5 py-3 disabled:opacity-50"
          >
            {judgeLoading ? "Judging..." : "Run LLM Judge"}
          </button>
        </div>

        {judgeResult && judgeResult.ok === false && (
          <p className="mt-4 text-red-700">Error: {judgeResult.error}</p>
        )}

        {judgeResult && judgeResult.ok && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-6">
              <Metric
                title="Avg Judge Score"
                value={`${judgeResult.average_judge_score} / ${judgeResult.max_score}`}
              />
              <Metric title="Judge Model" value={judgeResult.judge_model} />
              <Metric
                title="Scored Cases"
                value={`${judgeResult.scored_cases}/${judgeResult.total_cases}`}
              />
            </div>

            <div className="mt-6 overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-left">
                  <tr>
                    <th className="p-3">Case</th>
                    <th className="p-3">Model</th>
                    <th className="p-3">Score</th>
                    <th className="p-3">Rationale</th>
                  </tr>
                </thead>
                <tbody>
                  {judgeResult.cases.map((c: any) => (
                    <tr key={c.name} className="border-t">
                      <td className="p-3 font-medium">{c.name}</td>
                      <td className="p-3">
                        {c.actual_model} / {c.actual_provider}
                      </td>
                      <td className="p-3">
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-medium ${
                            (c.judge?.score ?? 0) >= 4
                              ? "bg-emerald-50 text-emerald-700"
                              : (c.judge?.score ?? 0) >= 3
                              ? "bg-amber-50 text-amber-700"
                              : "bg-red-50 text-red-700"
                          }`}
                        >
                          {c.judge?.score ?? "?"} / 5
                        </span>
                      </td>
                      <td className="p-3 max-w-xl text-slate-700">
                        {c.judge?.rationale}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      {/* ---------- RAGAS ---------- */}
      <div className="mt-12 rounded-2xl bg-white p-6 border shadow-sm">
        <div>
          <h3 className="text-2xl font-bold">RAGAS Metrics</h3>
          <p className="mt-1 text-slate-600">
            <span className="font-medium">Faithfulness</span> — is the answer grounded in retrieved context?{" "}
            <span className="font-medium">Context precision</span> — did the retriever rank the right chunks?
            Contexts are pulled live from the InferOps RAG retriever.
          </p>
        </div>

        <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
          {RAGAS_SCENARIOS.map((scenario) => {
            const isActive = ragasScenarioId === scenario.id;
            return (
              <button
                key={scenario.id}
                onClick={() => runRagasScenario(scenario)}
                disabled={ragasLoading}
                className={`text-left rounded-2xl border p-4 transition disabled:opacity-50 ${
                  isActive
                    ? "border-slate-950 bg-slate-50 ring-2 ring-slate-200"
                    : "bg-white hover:bg-slate-50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <p className="font-semibold">{scenario.label}</p>
                  <span
                    className={`text-xs rounded-full px-2 py-0.5 ${
                      scenario.expected === "high"
                        ? "bg-emerald-50 text-emerald-700"
                        : "bg-red-50 text-red-700"
                    }`}
                  >
                    expected: {scenario.expected}
                  </span>
                </div>
                <p className="mt-2 text-xs text-slate-600">
                  {scenario.description}
                </p>
                <p className="mt-3 text-xs text-slate-500">
                  {ragasLoading && isActive
                    ? "Scoring..."
                    : isActive
                    ? "Click again to re-run"
                    : "Click to run"}
                </p>
              </button>
            );
          })}
        </div>

        {ragasResult && ragasResult.ok === false && (
          <p className="mt-4 text-red-700">Error: {ragasResult.error}</p>
        )}

        {ragasResult && ragasResult.ok && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-6">
              <ScoreBar
                title="Faithfulness"
                score={ragasResult.scores?.faithfulness}
                tooltip="Fraction of claims in the answer supported by retrieved context."
              />
              <ScoreBar
                title="Context Precision"
                score={ragasResult.scores?.context_precision}
                tooltip="Average precision of retrieved chunks ordered against the ground truth."
              />
            </div>

            <div className="mt-6 space-y-4">
              {ragasResult.samples.map((s: any, idx: number) => (
                <div key={idx} className="rounded-xl border p-4 bg-slate-50">
                  <p className="text-sm">
                    <span className="font-semibold">Q:</span> {s.user_input}
                  </p>
                  <p className="text-sm mt-1">
                    <span className="font-semibold">A:</span> {s.response}
                  </p>
                  <p className="text-sm mt-1">
                    <span className="font-semibold">Ground truth:</span>{" "}
                    {s.reference}
                  </p>
                  <p className="text-xs mt-2 text-slate-600">
                    Retrieved {s.retrieved_contexts?.length ?? 0} chunks ·
                    faithfulness {fmtScore(s.faithfulness)} ·
                    context_precision {fmtScore(s.context_precision)}
                  </p>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function fmtScore(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "-";
  return v.toFixed(3);
}

function scoreColor(v: number): { bar: string; text: string } {
  if (v >= 0.8) return { bar: "bg-emerald-500", text: "text-emerald-700" };
  if (v >= 0.5) return { bar: "bg-amber-500", text: "text-amber-700" };
  return { bar: "bg-red-500", text: "text-red-700" };
}

function ScoreBar({
  title,
  score,
  tooltip,
}: {
  title: string;
  score: number | null | undefined;
  tooltip?: string;
}) {
  const value =
    score === null || score === undefined || Number.isNaN(score) ? 0 : score;
  const color = scoreColor(value);
  const pct = Math.round(value * 100);

  return (
    <div className="rounded-2xl bg-white p-5 border shadow-sm" title={tooltip}>
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">{title}</p>
        <p className={`text-sm font-semibold ${color.text}`}>{pct}%</p>
      </div>
      <p className="mt-1 text-3xl font-semibold">{fmtScore(score)}</p>
      <div className="mt-3 h-2 w-full rounded-full bg-slate-100 overflow-hidden">
        <div
          className={`h-full ${color.bar} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
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