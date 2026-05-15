"use client";

import { useState } from "react";
import { apiPost } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type LastTrace = {
  selected_model: string;
  selected_provider: string;
  routing_reason: string;
  latency_ms: number;
  estimated_cost_usd: number;
  fallback: {
    used: boolean;
    reason?: string;
    fallback_model?: string;
  };
  safety: {
    contains_pii: boolean;
    pii_redacted: boolean;
    prompt_injection_risk: string;
    blocked: boolean;
  };
  trace_id: string;
};

export default function PlaygroundPage() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi, I am InferOps AI. Ask me anything about AI deployment, routing, cost, safety, observability, or infrastructure.",
    },
  ]);

  const [input, setInput] = useState("");
  const [priority, setPriority] = useState("cost_optimized");
  const [privacy, setPrivacy] = useState("normal");
  const [loading, setLoading] = useState(false);
  const [lastTrace, setLastTrace] = useState<LastTrace | null>(null);

  async function sendMessage() {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      role: "user",
      content: input.trim(),
    };

    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);

    try {
      const data: any = await apiPost("/v1/chat/conversation", {
        user_id: "demo_user",
        conversation_id: conversationId,
        messages: nextMessages.map((m) => ({
          role: m.role,
          content: m.content,
        })),
        task_type: "auto",
        priority,
        privacy,
        max_output_tokens: 450,
      });

      setConversationId(data.conversation_id);

      setMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: data.assistant_message.content,
        },
      ]);

      setLastTrace({
        selected_model: data.selected_model,
        selected_provider: data.selected_provider,
        routing_reason: data.routing_reason,
        latency_ms: data.latency_ms,
        estimated_cost_usd: data.estimated_cost_usd,
        fallback: data.fallback,
        safety: data.safety,
        trace_id: data.trace_id,
      });
    } catch (e: any) {
      setMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: `Error: ${e.message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function newChat() {
    setConversationId(null);
    setMessages([
      {
        role: "assistant",
        content:
          "New chat started. Ask me about deployment architecture, model routing, safety, budget, or observability.",
      },
    ]);
    setLastTrace(null);
    setInput("");
  }

  return (
    <div>
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-3xl font-bold">Chat Console</h2>
          <p className="mt-2 text-slate-600">
            Multi-turn AI gateway chat with routing, safety, budget, fallback, and latency tracing.
          </p>
        </div>

        <button
          onClick={newChat}
          className="rounded-xl border bg-white px-4 py-2 text-sm hover:bg-slate-50"
        >
          New chat
        </button>
      </div>

      <div className="mt-8 grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 rounded-2xl bg-white border shadow-sm flex flex-col h-[720px]">
          <div className="border-b p-4 flex gap-4">
            <div className="flex-1">
              <label className="text-xs font-medium text-slate-600">Priority</label>
              <select
                className="mt-1 w-full rounded-xl border p-2 text-sm"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                <option value="cost_optimized">Cost optimized</option>
                <option value="quality_optimized">Quality optimized</option>
                <option value="latency_optimized">Latency optimized</option>
              </select>
            </div>

            <div className="flex-1">
              <label className="text-xs font-medium text-slate-600">Privacy</label>
              <select
                className="mt-1 w-full rounded-xl border p-2 text-sm"
                value={privacy}
                onChange={(e) => setPrivacy(e.target.value)}
              >
                <option value="normal">Normal</option>
                <option value="sensitive">Sensitive</option>
                <option value="local_only">Local only</option>
              </select>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-slate-50">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex ${
                  m.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                    m.role === "user"
                      ? "bg-slate-950 text-white"
                      : "bg-white border text-slate-900"
                  }`}
                >
                  {m.role === "assistant" ? (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({ children }) => (
                          <h1 className="text-xl font-bold mt-3 mb-2">{children}</h1>
                        ),
                        h2: ({ children }) => (
                          <h2 className="text-lg font-semibold mt-3 mb-2">{children}</h2>
                        ),
                        h3: ({ children }) => (
                          <h3 className="font-semibold mt-3 mb-2">{children}</h3>
                        ),
                        p: ({ children }) => (
                          <p className="mb-2">{children}</p>
                        ),
                        ul: ({ children }) => (
                          <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>
                        ),
                        ol: ({ children }) => (
                          <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>
                        ),
                        strong: ({ children }) => (
                          <strong className="font-semibold">{children}</strong>
                        ),
                      }}
                    >
                      {m.content}
                    </ReactMarkdown>
                  ) : (
                    <div className="whitespace-pre-wrap">{m.content}</div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="rounded-2xl bg-white border px-4 py-3 text-sm text-slate-500">
                  Routing request and generating response...
                </div>
              </div>
            )}
          </div>

          <div className="border-t p-4">
            <textarea
              className="w-full h-24 rounded-xl border p-3 text-sm"
              placeholder="Ask about deployment architecture, safety, costs, routing, RAG, Kubernetes, observability..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                  sendMessage();
                }
              }}
            />

            <div className="mt-3 flex items-center justify-between">
              <p className="text-xs text-slate-500">
                Press Ctrl + Enter to send
              </p>
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="rounded-xl bg-slate-950 text-white px-5 py-2 disabled:opacity-50"
              >
                {loading ? "Sending..." : "Send"}
              </button>
            </div>
          </div>
        </div>

        <div className="rounded-2xl bg-white border shadow-sm p-5 h-fit">
          <h3 className="text-lg font-semibold">Last Routing Trace</h3>
          <p className="mt-1 text-sm text-slate-500">
            Shows the deployment decision for the latest assistant response.
          </p>

          {!lastTrace && (
            <p className="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
              No trace yet. Send a message first.
            </p>
          )}

          {lastTrace && (
            <div className="mt-5 space-y-3 text-sm">
              <TraceItem label="Model" value={lastTrace.selected_model} />
              <TraceItem label="Provider" value={lastTrace.selected_provider} />
              <TraceItem label="Latency" value={`${lastTrace.latency_ms} ms`} />
              <TraceItem label="Cost" value={`$${lastTrace.estimated_cost_usd}`} />
              <TraceItem label="Fallback" value={lastTrace.fallback?.used ? "Yes" : "No"} />
              <TraceItem label="Contains PII" value={lastTrace.safety?.contains_pii ? "Yes" : "No"} />
              <TraceItem label="PII Redacted" value={lastTrace.safety?.pii_redacted ? "Yes" : "No"} />
              <TraceItem label="Injection Risk" value={lastTrace.safety?.prompt_injection_risk || "low"} />
              <TraceItem label="Blocked" value={lastTrace.safety?.blocked ? "Yes" : "No"} />

              <div>
                <p className="font-medium">Routing reason</p>
                <p className="mt-1 rounded-xl bg-emerald-50 p-3 text-emerald-900">
                  {lastTrace.routing_reason}
                </p>
              </div>

              <div>
                <p className="font-medium">Trace ID</p>
                <p className="mt-1 rounded-xl bg-slate-50 p-3 font-mono text-xs">
                  {lastTrace.trace_id}
                </p>
              </div>

              {lastTrace.fallback?.used && (
                <div>
                  <p className="font-medium">Fallback reason</p>
                  <p className="mt-1 rounded-xl bg-amber-50 p-3 text-amber-900">
                    {lastTrace.fallback.reason || "Primary provider failed."}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TraceItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}