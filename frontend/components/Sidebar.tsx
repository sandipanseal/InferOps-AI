"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/chat", label: "Chat Console" },
  { href: "/logs", label: "Request Logs" },
  { href: "/models", label: "Models" },
  { href: "/budget", label: "Budget" },
  { href: "/safety", label: "Safety Center" },
  { href: "/evals", label: "Evaluation Center" },
  { href: "/knowledge", label: "Knowledge Base" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-56 bg-slate-950 text-white px-4 py-6">
      <div>
        <h1 className="text-xl font-bold">InferOps AI</h1>
        <p className="mt-1 text-xs text-slate-400">LLM Deployment Console</p>
      </div>

      <nav className="mt-10 space-y-2">
        {navItems.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-xl px-3 py-2 text-sm transition ${
                active
                  ? "bg-slate-800 text-white"
                  : "text-slate-200 hover:bg-slate-900 hover:text-white"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}