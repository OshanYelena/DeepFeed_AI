"use client";

import { useQuery } from "@tanstack/react-query";
import { contentAPI } from "@/lib/api";
import { useAuthStore, useRequireAuth } from "@/lib/auth-store";
import { AppShell } from "@/components/layout/AppShell";
import { useRouter } from "next/navigation";

const SECTIONS = [
  { id: "account", label: "Account" },
  { id: "discovery", label: "Discovery" },
  { id: "security", label: "Security" },
  { id: "danger", label: "Data & export" },
];

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export default function SettingsPage() {
  const ready = useRequireAuth();
  const router = useRouter();
  const { email, fullName, logout } = useAuthStore();

  const { data: statusData } = useQuery({
    queryKey: ["discover-status"],
    queryFn: () => contentAPI.getStatus(),
    enabled: ready,
  });
  const status = statusData?.data.data;

  if (!ready) return null;

  return (
    <AppShell>
      <div className="px-9 pt-7 pb-14 grid grid-cols-1 md:grid-cols-[160px_minmax(0,1fr)] gap-10 max-w-[900px]">
        <div className="hidden md:flex flex-col gap-0.5 pt-[54px] text-[13.5px]">
          {SECTIONS.map((s, i) => (
            <button
              key={s.id}
              onClick={() => scrollTo(s.id)}
              className={`text-left px-2.5 py-2 rounded-lg transition-colors ${
                i === 0 ? "bg-white/[0.06] text-white font-semibold" : "text-ink-muted hover:text-white"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>

        <div className="flex flex-col gap-4 min-w-0">
          <h1 className="font-serif text-[30px] leading-tight text-ink m-0">Settings</h1>

          <section id="account" className="card px-5 py-[18px] flex flex-col gap-3.5 scroll-mt-6">
            <div className="label-mono">Account</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <div className="text-xs text-ink-dim mb-1.5">Full name</div>
                <div className="px-3 py-2.5 rounded-lg bg-surface border border-white/10 text-[13.5px] text-ink">
                  {fullName || <span className="text-ink-faint">Not set</span>}
                </div>
              </div>
              <div>
                <div className="text-xs text-ink-dim mb-1.5">Email</div>
                <div className="px-3 py-2.5 rounded-lg bg-surface border border-white/10 text-[13.5px] text-ink">
                  {email || <span className="text-ink-faint">Unknown</span>}
                </div>
              </div>
            </div>
          </section>

          <section id="discovery" className="card px-5 py-[18px] flex flex-col gap-3.5 scroll-mt-6">
            <div className="label-mono">Discovery</div>
            <div className="flex items-center gap-4 pt-1">
              <div className="flex-1">
                <div className="text-sm font-semibold text-ink">Scheduled discovery</div>
                <div className="text-xs text-ink-soft mt-0.5">Runs the research agent automatically in the background</div>
              </div>
              <span className="font-mono text-[11px] text-ink-muted">AUTOMATIC</span>
            </div>
            <div className="flex items-center gap-4 pt-3 border-t border-white/[0.06]">
              <div className="flex-1">
                <div className="text-sm font-semibold text-ink">Manual &quot;Discover now&quot;</div>
                <div className="text-xs text-ink-soft mt-0.5">Daily quota and cooldown between runs</div>
              </div>
              <span className="font-mono text-[11px] text-ink-muted">
                {status ? `${status.daily.used} / ${status.daily.limit} · ${status.daily.remaining} LEFT` : "…"}
              </span>
            </div>
          </section>

          <section id="security" className="card px-5 py-[18px] flex flex-col gap-3 scroll-mt-6">
            <div className="label-mono">Security</div>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="text-sm font-semibold text-ink">This session</div>
                <div className="text-xs text-ink-soft mt-0.5">
                  Cross-device session management isn&apos;t available yet — you can sign out of this browser.
                </div>
              </div>
              <button
                onClick={() => { logout(); router.push("/login"); }}
                className="btn-outline shrink-0"
              >
                Sign out
              </button>
            </div>
          </section>

          <section id="danger" className="flex items-center gap-4 px-5 py-3.5 rounded-xl border border-red-500/30 scroll-mt-6">
            <div className="flex-1">
              <div className="text-sm font-semibold text-red-300">Delete account</div>
              <div className="text-xs text-ink-soft mt-0.5">Not available yet — there&apos;s no account-deletion endpoint to call.</div>
            </div>
            <span className="px-3 py-1.5 rounded-lg border border-red-500/40 text-red-300/50 text-xs font-semibold cursor-not-allowed">
              Delete…
            </span>
          </section>
        </div>
      </div>
    </AppShell>
  );
}
