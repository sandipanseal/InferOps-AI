"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

type ModelInfo = {
  name: string;
  provider: string;
  status: string;
  cost_tier: string;
  deployment: string;
  description: string;
};

export default function ModelsPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadModels() {
    try {
      setLoading(true);
      setError("");
      const data = await apiGet("/v1/models");
      setModels(data);
    } catch (e: any) {
      setError(e.message || "Failed to load models.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadModels();
  }, []);

  return (
    <div>
      <h2 className="text-3xl font-bold">Model Registry</h2>
      <p className="mt-2 text-slate-600">
        Available model providers and deployment modes.
      </p>

      {loading && (
        <p className="mt-8 rounded-2xl border bg-white p-5 text-slate-500">
          Loading models...
        </p>
      )}

      {error && (
        <p className="mt-8 rounded-2xl border border-red-200 bg-red-50 p-5 text-red-700">
          {error}
        </p>
      )}

      {!loading && !error && (
        <div className="mt-8 grid grid-cols-1 gap-5 xl:grid-cols-2">
          {models.map((model) => (
            <div
              key={`${model.provider}-${model.name}`}
              className="rounded-2xl border bg-white p-6 shadow-sm"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-xl font-semibold">{model.name}</h3>
                  <p className="text-sm text-slate-500">{model.provider}</p>
                </div>

                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                  {model.status}
                </span>
              </div>

              <p className="mt-4 text-sm leading-6 text-slate-700">
                {model.description}
              </p>

              <div className="mt-5 grid grid-cols-2 gap-4 text-sm">
                <Info label="Cost tier" value={model.cost_tier} />
                <Info label="Deployment" value={model.deployment} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}