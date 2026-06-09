"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const nav = [
  { href: "/", label: "Dashboard", icon: "◈" },
  { href: "/segments", label: "Segments", icon: "◎" },
  { href: "/campaigns", label: "Campaigns", icon: "▶" },
  { href: "/analytics", label: "Analytics", icon: "◉" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 flex h-full w-56 flex-col border-r border-zinc-800 bg-zinc-950 p-4">
      <div className="mb-8 px-2">
        <h1 className="text-lg font-bold tracking-tight text-white">Xeno CRM</h1>
        <p className="text-xs text-zinc-500">AI Campaign Operator</p>
      </div>
      <nav className="flex flex-1 flex-col gap-1">
        {nav.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                active
                  ? "bg-violet-600/20 text-violet-300"
                  : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
        <p className="text-xs font-medium text-zinc-400">AI-Native</p>
        <p className="mt-1 text-[11px] leading-relaxed text-zinc-600">
          Goal → AI decides audience + message + channel → executes → learns
        </p>
      </div>
    </aside>
  );
}
