const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = err.detail;
    let message = "Request failed";
    if (typeof detail === "string") {
      message = detail;
    } else if (Array.isArray(detail)) {
      message = detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join(", ");
    }
    throw new Error(message);
  }
  return res.json();
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  created_at: string;
}

export interface Segment {
  id: string;
  name: string;
  definition_json: Record<string, unknown>;
  is_ai_generated: boolean;
  created_at: string;
}

export interface Campaign {
  id: string;
  name: string;
  goal: string | null;
  segment_id: string | null;
  message_template: string;
  channel_mix: string[];
  status: string;
  created_at: string;
}

export interface CampaignAnalytics {
  campaign_id: string;
  name: string;
  status: string;
  funnel: Record<string, number>;
  rates: Record<string, number>;
  channel_breakdown: Record<string, Record<string, number>>;
  insights: string[];
}

export const api = {
  getCustomers: () => request<Customer[]>("/customers"),
  getSegments: () => request<Segment[]>("/segments"),
  createSegment: (data: { name: string; definition_json: Record<string, unknown>; is_ai_generated?: boolean }) =>
    request<Segment>("/segments", { method: "POST", body: JSON.stringify(data) }),
  aiSuggestSegment: (natural_language: string) =>
    request<{ name: string; definition_json: Record<string, unknown>; is_ai_generated: boolean }>(
      "/segments/ai-suggest",
      { method: "POST", body: JSON.stringify({ natural_language }) }
    ),
  evaluateSegment: (data: { segment_id?: string; definition_json?: Record<string, unknown> }) =>
    request<Customer[]>("/segments/evaluate", { method: "POST", body: JSON.stringify(data) }),
  getCampaigns: () => request<Campaign[]>("/campaigns"),
  createCampaign: (data: {
    name: string;
    goal?: string;
    segment_id?: string;
    message_template: string;
    channel_mix: string[];
  }) => request<Campaign>("/campaigns", { method: "POST", body: JSON.stringify(data) }),
  sendCampaign: (campaign_id: string) =>
    request<{ campaign_id: string; status: string; recipients: number; messages_sent: number }>(
      "/campaigns/send",
      { method: "POST", body: JSON.stringify({ campaign_id }) }
    ),
  getCampaignAnalytics: (campaign_id: string) =>
    request<CampaignAnalytics>(`/campaigns/${campaign_id}/analytics`),
  recommendCampaign: (goal: string, segment_id?: string) =>
    request<{ channel_mix: string[]; timing: string; rationale: string }>("/campaigns/recommend", {
      method: "POST",
      body: JSON.stringify({ goal, segment_id }),
    }),
  generateMessage: (data: {
    customer_name: string;
    goal: string;
    brand_tone?: string;
    channel?: string;
  }) =>
    request<{ message: string; channel: string; personalization_notes: string }>(
      "/campaigns/generate-message",
      { method: "POST", body: JSON.stringify({ brand_tone: "friendly and professional", channel: "email", ...data }) }
    ),
  seedData: () => request<{ status: string }>("/seed", { method: "POST" }),
};
