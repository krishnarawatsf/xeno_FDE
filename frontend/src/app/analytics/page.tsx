"use client";

import { useCallback, useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { FunnelChart } from "@/components/FunnelChart";
import { api, Campaign, CampaignAnalytics } from "@/lib/api";

function AnalyticsContent() {
  const searchParams = useSearchParams();
  const initialCampaign = searchParams.get("campaign");

  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedId, setSelectedId] = useState<string>(initialCampaign || "");
  const [analytics, setAnalytics] = useState<CampaignAnalytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadAnalytics = useCallback(async (id: string) => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await api.getCampaignAnalytics(id);
      setAnalytics(data);
    } catch {
      setAnalytics(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    api.getCampaigns().then((c) => {
      setCampaigns(c);
      if (!selectedId && c.length > 0) {
        setSelectedId(c[0].id);
      }
    });
  }, [selectedId]);

  useEffect(() => {
    if (selectedId) loadAnalytics(selectedId);
  }, [selectedId, loadAnalytics]);

  useEffect(() => {
    if (!autoRefresh || !selectedId) return;
    const interval = setInterval(() => loadAnalytics(selectedId), 3000);
    return () => clearInterval(interval);
  }, [autoRefresh, selectedId, loadAnalytics]);

  return (
    <div>
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Analytics</h1>
          <p className="mt-1 text-zinc-500">
            Campaign funnel — sent → delivered → opened → clicked → converted
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-zinc-500">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            Auto-refresh (3s)
          </label>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            aria-label="Select campaign for analytics"
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-violet-600 focus:outline-none"
          >
            <option value="">Select campaign</option>
            {campaigns.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.status})
              </option>
            ))}
          </select>
          <button
            onClick={() => selectedId && loadAnalytics(selectedId)}
            disabled={loading}
            className="rounded-lg border border-zinc-700 px-3 py-2 text-xs text-zinc-400 hover:border-zinc-600 hover:text-zinc-200"
          >
            Refresh
          </button>
        </div>
      </header>

      {!selectedId && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-12 text-center text-zinc-500">
          Select a campaign to view analytics.
        </div>
      )}

      {selectedId && loading && !analytics && (
        <div className="flex h-48 items-center justify-center text-zinc-500">
          Loading analytics...
        </div>
      )}

      {analytics && (
        <div className="grid grid-cols-3 gap-6">
          <section className="col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/30 p-6">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">{analytics.name}</h2>
              <span className="rounded-full bg-zinc-800 px-3 py-1 text-xs capitalize text-zinc-400">
                {analytics.status}
              </span>
            </div>
            <FunnelChart funnel={analytics.funnel} rates={analytics.rates} />
          </section>

          <section className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6">
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-zinc-500">
              Key Rates
            </h2>
            <div className="space-y-4">
              {[
                { label: "Delivery Rate", value: analytics.rates.delivery_rate },
                { label: "Open Rate", value: analytics.rates.open_rate },
                { label: "Click Rate", value: analytics.rates.click_rate },
                { label: "Conversion Rate", value: analytics.rates.conversion_rate },
              ].map((r) => (
                <div key={r.label}>
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-400">{r.label}</span>
                    <span className="font-mono text-white">{(r.value * 100).toFixed(1)}%</span>
                  </div>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-zinc-800">
                    <div
                      className="h-full rounded-full bg-violet-500"
                      style={{ width: `${Math.min(r.value * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/30 p-6">
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-zinc-500">
              Channel Breakdown
            </h2>
            {Object.keys(analytics.channel_breakdown).length === 0 ? (
              <p className="text-sm text-zinc-600">No channel data yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-zinc-800 text-left text-xs text-zinc-500">
                      <th className="pb-2 pr-4">Channel</th>
                      <th className="pb-2 pr-4">Sent</th>
                      <th className="pb-2 pr-4">Delivered</th>
                      <th className="pb-2 pr-4">Opened</th>
                      <th className="pb-2 pr-4">Clicked</th>
                      <th className="pb-2">Failed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(analytics.channel_breakdown).map(([ch, stats]) => (
                      <tr key={ch} className="border-b border-zinc-800/50">
                        <td className="py-2 pr-4 capitalize text-white">{ch}</td>
                        <td className="py-2 pr-4 font-mono text-zinc-400">{stats.sent}</td>
                        <td className="py-2 pr-4 font-mono text-zinc-400">{stats.delivered}</td>
                        <td className="py-2 pr-4 font-mono text-zinc-400">{stats.opened}</td>
                        <td className="py-2 pr-4 font-mono text-zinc-400">{stats.clicked}</td>
                        <td className="py-2 font-mono text-zinc-400">{stats.failed}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="rounded-xl border border-violet-800/30 bg-violet-950/20 p-6">
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-violet-400">
              AI Insights
            </h2>
            {analytics.insights.length === 0 ? (
              <p className="text-sm text-zinc-600">Insights will appear after events stream in.</p>
            ) : (
              <ul className="space-y-3">
                {analytics.insights.map((insight, i) => (
                  <li key={i} className="flex gap-2 text-sm text-zinc-300">
                    <span className="text-violet-500">→</span>
                    {insight}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <Suspense fallback={<div className="text-zinc-500">Loading analytics...</div>}>
      <AnalyticsContent />
    </Suspense>
  );
}
