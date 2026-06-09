"use client";

import { useEffect, useState } from "react";
import { api, Customer, Segment } from "@/lib/api";

export default function SegmentsPage() {
  const [segments, setSegments] = useState<Segment[]>([]);
  const [nlQuery, setNlQuery] = useState("High value customers in the last 30 days");
  const [suggested, setSuggested] = useState<{
    name: string;
    definition_json: Record<string, unknown>;
    is_ai_generated: boolean;
  } | null>(null);
  const [preview, setPreview] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getSegments().then(setSegments).catch(() => {});
  }, []);

  async function handleAISuggest() {
    setLoading(true);
    setError(null);
    try {
      const result = await api.aiSuggestSegment(nlQuery);
      setSuggested(result);
      const customers = await api.evaluateSegment({ definition_json: result.definition_json });
      setPreview(customers);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    if (!suggested) return;
    setLoading(true);
    try {
      const { is_ai_generated, fallback, description, ...definition } =
        suggested.definition_json as Record<string, unknown> & {
          is_ai_generated?: boolean;
          fallback?: boolean;
          description?: string;
        };
      const seg = await api.createSegment({
        name: suggested.name,
        definition_json: definition,
        is_ai_generated: suggested.is_ai_generated,
      });
      setSegments((prev) => [seg, ...prev]);
      setSuggested(null);
      setPreview([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setLoading(false);
    }
  }

  async function handleEvaluate(segmentId: string) {
    setLoading(true);
    try {
      const customers = await api.evaluateSegment({ segment_id: segmentId });
      setPreview(customers);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-white">Segments</h1>
        <p className="mt-1 text-zinc-500">
          Rule-based or AI-generated audience selection
        </p>
      </header>

      <div className="mb-8 rounded-xl border border-violet-800/30 bg-violet-950/20 p-6">
        <h2 className="mb-3 text-sm font-semibold text-violet-300">AI Segment Builder</h2>
        <p className="mb-4 text-sm text-zinc-500">
          Describe your audience in natural language — AI converts it to a segment definition.
        </p>
        <div className="flex gap-3">
          <input
            type="text"
            value={nlQuery}
            onChange={(e) => setNlQuery(e.target.value)}
            placeholder="e.g. High value customers last 30 days"
            className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-sm text-white placeholder-zinc-600 focus:border-violet-600 focus:outline-none"
          />
          <button
            onClick={handleAISuggest}
            disabled={loading}
            className="rounded-lg bg-violet-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate Segment"}
          </button>
        </div>

        {suggested && (
          <div className="mt-4 space-y-3">
            <pre className="overflow-x-auto rounded-lg border border-zinc-800 bg-zinc-950 p-4 text-xs text-zinc-400">
              {JSON.stringify(suggested.definition_json, null, 2)}
            </pre>
            <div className="flex items-center gap-3">
              <p className="text-sm text-emerald-400">
                {preview.length} customers matched
              </p>
              <button
                onClick={handleSave}
                className="rounded-lg border border-emerald-700 bg-emerald-900/30 px-4 py-2 text-sm text-emerald-300 hover:bg-emerald-900/50"
              >
                Save Segment
              </button>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-900/50 bg-red-950/30 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {preview.length > 0 && (
        <section className="mb-8 rounded-xl border border-zinc-800 bg-zinc-900/30 p-6">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-zinc-500">
            Preview ({preview.length} customers)
          </h2>
          <div className="grid grid-cols-2 gap-2">
            {preview.map((c) => (
              <div
                key={c.id}
                className="rounded-lg border border-zinc-800 bg-zinc-950/50 px-3 py-2 text-sm"
              >
                <p className="font-medium text-white">{c.name}</p>
                <p className="text-xs text-zinc-500">{c.email}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-zinc-500">
          Saved Segments
        </h2>
        {segments.length === 0 ? (
          <p className="text-sm text-zinc-600">No segments saved yet.</p>
        ) : (
          <ul className="space-y-3">
            {segments.map((s) => (
              <li
                key={s.id}
                className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950/50 px-4 py-3"
              >
                <div>
                  <p className="font-medium text-white">
                    {s.name}
                    {s.is_ai_generated && (
                      <span className="ml-2 rounded bg-violet-900/40 px-1.5 py-0.5 text-[10px] text-violet-400">
                        AI
                      </span>
                    )}
                  </p>
                  <p className="text-xs text-zinc-500">
                    {(s.definition_json as { type?: string }).type || "custom"}
                  </p>
                </div>
                <button
                  onClick={() => handleEvaluate(s.id)}
                  className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-400 hover:border-zinc-600 hover:text-zinc-200"
                >
                  Evaluate
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
