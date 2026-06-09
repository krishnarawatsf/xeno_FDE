"use client";

import { useEffect, useState } from "react";
import { StatCard } from "@/components/StatCard";
import { api, Campaign, Customer, Segment } from "@/lib/api";

export default function DashboardPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);

  async function handleSeed() {
    setSeeding(true);
    try {
      await api.seedData();
      const [c, s, camp] = await Promise.all([
        api.getCustomers(),
        api.getSegments(),
        api.getCampaigns(),
      ]);
      setCustomers(c);
      setSegments(s);
      setCampaigns(camp);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Seed failed");
    } finally {
      setSeeding(false);
    }
  }

  useEffect(() => {
    Promise.all([api.getCustomers(), api.getSegments(), api.getCampaigns()])
      .then(([c, s, camp]) => {
        setCustomers(c);
        setSegments(s);
        setCampaigns(camp);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const activeCampaigns = campaigns.filter((c) =>
    ["sending", "sent", "completed"].includes(c.status)
  );

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-zinc-500">
        Loading dashboard...
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-900/50 bg-red-950/30 p-6">
        <h2 className="font-semibold text-red-400">Connection Error</h2>
        <p className="mt-2 text-sm text-zinc-400">
          Could not reach the backend at{" "}
          <code className="text-zinc-300">
            {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
          </code>
        </p>
        <p className="mt-1 text-sm text-zinc-500">{error}</p>
        <p className="mt-4 text-xs text-zinc-600">
          Run <code>docker compose up</code> to start all services.
        </p>
      </div>
    );
  }

  return (
    <div>
      <header className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="mt-1 text-zinc-500">
            AI-native shopper engagement — decide who, what, and how to reach
          </p>
        </div>
        {customers.length === 0 && (
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
          >
            {seeding ? "Seeding..." : "Load Demo Data"}
          </button>
        )}
      </header>

      <div className="mb-8 grid grid-cols-4 gap-4">
        <StatCard label="Customers" value={customers.length} accent="violet" />
        <StatCard label="Segments" value={segments.length} accent="emerald" />
        <StatCard label="Campaigns" value={campaigns.length} accent="amber" />
        <StatCard
          label="Active"
          value={activeCampaigns.length}
          sub="sending or completed"
          accent="sky"
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <section className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-zinc-500">
            Recent Campaigns
          </h2>
          {campaigns.length === 0 ? (
            <p className="text-sm text-zinc-600">
              No campaigns yet. Create one from the Campaigns page.
            </p>
          ) : (
            <ul className="space-y-3">
              {campaigns.slice(0, 5).map((c) => (
                <li
                  key={c.id}
                  className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950/50 px-4 py-3"
                >
                  <div>
                    <p className="font-medium text-white">{c.name}</p>
                    <p className="text-xs text-zinc-500">{c.channel_mix.join(", ")}</p>
                  </div>
                  <StatusBadge status={c.status} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-zinc-500">
            Workflow
          </h2>
          <ol className="space-y-4 text-sm">
            {[
              { step: "1", title: "Define Goal", desc: "What do you want to achieve?" },
              { step: "2", title: "AI Segments", desc: "Natural language → audience" },
              { step: "3", title: "Generate Message", desc: "Personalized per channel" },
              { step: "4", title: "Execute", desc: "Send via channel service" },
              { step: "5", title: "Learn", desc: "Events stream back → insights" },
            ].map((item) => (
              <li key={item.step} className="flex gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-violet-600/20 text-xs font-bold text-violet-400">
                  {item.step}
                </span>
                <div>
                  <p className="font-medium text-zinc-200">{item.title}</p>
                  <p className="text-zinc-500">{item.desc}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: "bg-zinc-800 text-zinc-400",
    sending: "bg-amber-900/40 text-amber-400",
    sent: "bg-sky-900/40 text-sky-400",
    completed: "bg-emerald-900/40 text-emerald-400",
    failed: "bg-red-900/40 text-red-400",
  };
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${colors[status] || colors.draft}`}
    >
      {status}
    </span>
  );
}
