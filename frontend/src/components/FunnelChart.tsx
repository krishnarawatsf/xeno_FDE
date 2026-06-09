interface FunnelChartProps {
  funnel: Record<string, number>;
  rates?: Record<string, number>;
}

const STAGES = ["sent", "delivered", "opened", "clicked", "converted"] as const;

const LABELS: Record<string, string> = {
  sent: "Sent",
  delivered: "Delivered",
  opened: "Opened",
  clicked: "Clicked",
  converted: "Converted",
};

export function FunnelChart({ funnel, rates }: FunnelChartProps) {
  const max = Math.max(...STAGES.map((s) => funnel[s] || 0), 1);

  return (
    <div className="space-y-3">
      {STAGES.map((stage) => {
        const count = funnel[stage] || 0;
        const pct = (count / max) * 100;
        return (
          <div key={stage}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="text-zinc-400">{LABELS[stage]}</span>
              <span className="font-mono text-white">
                {count}
                {rates && stage === "delivered" && rates.delivery_rate !== undefined && (
                  <span className="ml-2 text-xs text-zinc-500">
                    ({(rates.delivery_rate * 100).toFixed(0)}%)
                  </span>
                )}
                {rates && stage === "opened" && rates.open_rate !== undefined && (
                  <span className="ml-2 text-xs text-zinc-500">
                    ({(rates.open_rate * 100).toFixed(0)}%)
                  </span>
                )}
                {rates && stage === "clicked" && rates.click_rate !== undefined && (
                  <span className="ml-2 text-xs text-zinc-500">
                    ({(rates.click_rate * 100).toFixed(0)}%)
                  </span>
                )}
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
              <div
                className="h-full rounded-full bg-gradient-to-r from-violet-600 to-violet-400 transition-all duration-500"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
