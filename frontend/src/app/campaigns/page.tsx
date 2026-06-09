"use client";

import { useEffect, useState } from "react";
import { api, Campaign, Segment } from "@/lib/api";

const CHANNELS = ["email", "whatsapp", "sms", "rcs"];

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [name, setName] = useState("");
  const [goal, setGoal] = useState("Win back customers with a 20% discount");
  const [segmentId, setSegmentId] = useState("");
  const [message, setMessage] = useState("Hi {{name}}, we miss you! Enjoy 20% off your next order.");
  const [channels, setChannels] = useState<string[]>(["email", "whatsapp"]);
  const [recommendation, setRecommendation] = useState<{
    channel_mix: string[];
    timing: string;
    rationale: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [sendingId, setSendingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getCampaigns(), api.getSegments()])
      .then(([c, s]) => {
        setCampaigns(c);
        setSegments(s);
        if (s.length > 0) setSegmentId(s[0].id);
      })
      .catch(() => {});
  }, []);

  function toggleChannel(ch: string) {
    setChannels((prev) =>
      prev.includes(ch) ? prev.filter((c) => c !== ch) : [...prev, ch]
    );
  }

  async function handleRecommend() {
    setLoading(true);
    setError(null);
    try {
      const rec = await api.recommendCampaign(goal, segmentId || undefined);
      setRecommendation(rec);
      setChannels(rec.channel_mix);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateMessage() {
    setLoading(true);
    setError(null);
    try {
      const result = await api.generateMessage({
        customer_name: "Priya",
        goal,
        channel: channels[0] || "email",
      });
      setMessage(result.message);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!name || !segmentId || channels.length === 0) {
      setError("Name, segment, and at least one channel are required.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const campaign = await api.createCampaign({
        name,
        goal,
        segment_id: segmentId,
        message_template: message,
        channel_mix: channels,
      });
      setCampaigns((prev) => [campaign, ...prev]);
      setName("");
      setSuccess("Campaign created successfully.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(campaignId: string) {
    setSendingId(campaignId);
    setError(null);
    setSuccess(null);
    try {
      const result = await api.sendCampaign(campaignId);
      setSuccess(
        `Sent to ${result.recipients} recipients (${result.messages_sent} messages). Events will stream in shortly.`
      );
      const updated = await api.getCampaigns();
      setCampaigns(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Send failed");
    } finally {
      setSendingId(null);
    }
  }

  return (
    <div>
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-white">Campaigns</h1>
        <p className="mt-1 text-zinc-500">
          Goal → AI decides audience + message + channel → execute
        </p>
      </header>

      <form
        onSubmit={handleCreate}
        className="mb-8 rounded-xl border border-zinc-800 bg-zinc-900/30 p-6"
      >
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-zinc-500">
          Create Campaign
        </h2>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-xs text-zinc-500">Campaign Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Summer Win-back"
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-violet-600 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-zinc-500">Segment</label>
            <select
              value={segmentId}
              onChange={(e) => setSegmentId(e.target.value)}
              aria-label="Select segment"
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-violet-600 focus:outline-none"
            >
              <option value="">Select segment</option>
              {segments.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-4">
          <label className="mb-1 block text-xs text-zinc-500">Goal</label>
          <input
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            aria-label="Campaign goal"
            placeholder="Describe your campaign goal"
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-violet-600 focus:outline-none"
          />
        </div>

        <div className="mt-4">
          <label className="mb-1 block text-xs text-zinc-500">
            Message Template <span className="text-zinc-600">(use {"{{name}}"} for personalization)</span>
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={3}
            aria-label="Message template"
            placeholder="Hi {{name}}, ..."
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-violet-600 focus:outline-none"
          />
        </div>

        <div className="mt-4">
          <label className="mb-2 block text-xs text-zinc-500">Channels</label>
          <div className="flex gap-2">
            {CHANNELS.map((ch) => (
              <button
                key={ch}
                type="button"
                onClick={() => toggleChannel(ch)}
                className={`rounded-lg border px-3 py-1.5 text-xs capitalize ${
                  channels.includes(ch)
                    ? "border-violet-600 bg-violet-900/30 text-violet-300"
                    : "border-zinc-700 text-zinc-500 hover:border-zinc-600"
                }`}
              >
                {ch}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleRecommend}
            disabled={loading}
            className="rounded-lg border border-sky-700 bg-sky-900/20 px-4 py-2 text-sm text-sky-300 hover:bg-sky-900/40 disabled:opacity-50"
          >
            AI Recommend Channels
          </button>
          <button
            type="button"
            onClick={handleGenerateMessage}
            disabled={loading}
            className="rounded-lg border border-violet-700 bg-violet-900/20 px-4 py-2 text-sm text-violet-300 hover:bg-violet-900/40 disabled:opacity-50"
          >
            AI Generate Message
          </button>
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-violet-600 px-5 py-2 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50"
          >
            Create Campaign
          </button>
        </div>

        {recommendation && (
          <div className="mt-4 rounded-lg border border-sky-800/40 bg-sky-950/20 p-4 text-sm">
            <p className="text-sky-300">AI Recommendation</p>
            <p className="mt-1 text-zinc-400">{recommendation.rationale}</p>
            <p className="mt-1 text-xs text-zinc-500">Best timing: {recommendation.timing}</p>
          </div>
        )}
      </form>

      {error && (
        <div className="mb-4 rounded-lg border border-red-900/50 bg-red-950/30 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 rounded-lg border border-emerald-900/50 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-400">
          {success}
        </div>
      )}

      <section className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-zinc-500">
          All Campaigns
        </h2>
        {campaigns.length === 0 ? (
          <p className="text-sm text-zinc-600">No campaigns yet. Create one above.</p>
        ) : (
          <ul className="space-y-3">
            {campaigns.map((c) => (
              <li
                key={c.id}
                className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950/50 px-4 py-3"
              >
                <div>
                  <p className="font-medium text-white">{c.name}</p>
                  <p className="text-xs text-zinc-500">
                    {c.channel_mix.join(", ")} · {c.status}
                  </p>
                  {c.goal && <p className="mt-1 text-xs text-zinc-600">{c.goal}</p>}
                </div>
                <div className="flex gap-2">
                  {c.status === "draft" && (
                    <button
                      onClick={() => handleSend(c.id)}
                      disabled={sendingId === c.id}
                      className="rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
                    >
                      {sendingId === c.id ? "Sending..." : "Send"}
                    </button>
                  )}
                  <a
                    href={`/analytics?campaign=${c.id}`}
                    className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-400 hover:border-zinc-600 hover:text-zinc-200"
                  >
                    Analytics
                  </a>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
