interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  accent?: string;
}

export function StatCard({ label, value, sub, accent = "violet" }: StatCardProps) {
  const colors: Record<string, string> = {
    violet: "from-violet-600/20 to-violet-900/10 border-violet-800/40",
    emerald: "from-emerald-600/20 to-emerald-900/10 border-emerald-800/40",
    amber: "from-amber-600/20 to-amber-900/10 border-amber-800/40",
    sky: "from-sky-600/20 to-sky-900/10 border-sky-800/40",
  };

  return (
    <div
      className={`rounded-xl border bg-gradient-to-br p-5 ${colors[accent] || colors.violet}`}
    >
      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">{label}</p>
      <p className="mt-2 text-3xl font-bold text-white">{value}</p>
      {sub && <p className="mt-1 text-xs text-zinc-500">{sub}</p>}
    </div>
  );
}
