"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { profileAPI, interestsAPI, agentAPI } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { useLibraryStore } from "@/lib/library-store";
import { Logo } from "@/components/Logo";

const NAV_ITEMS = [
  { id: "feed", href: "/feed", label: "Today" },
  { id: "search", href: "/search", label: "Search" },
  { id: "saved", href: "/saved", label: "Saved" },
  { id: "agent", href: "/agent", label: "Agent" },
  { id: "profile", href: "/profile", label: "Profile" },
] as const;

function initialsOf(name: string | null, email: string | null): string {
  if (name && name.trim()) {
    const parts = name.trim().split(/\s+/);
    return (parts[0][0] + (parts[1]?.[0] ?? "")).toUpperCase();
  }
  if (email) return email.slice(0, 2).toUpperCase();
  return "?";
}

export function AppNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { logout, email, fullName, isAuthenticated } = useAuthStore();
  const bookmarkCount = useLibraryStore((s) => Object.keys(s.bookmarks).length);

  const { data: profileData } = useQuery({
    queryKey: ["profile"],
    queryFn: () => profileAPI.getProfile(),
    enabled: isAuthenticated,
  });
  const { data: interestsData } = useQuery({
    queryKey: ["interests"],
    queryFn: () => interestsAPI.list(),
    enabled: isAuthenticated,
  });
  const { data: eventsData } = useQuery({
    queryKey: ["agent-events"],
    queryFn: () => agentAPI.getAdaptationEvents(),
    enabled: isAuthenticated,
  });

  const profile = profileData?.data.data;
  const interests = [...(interestsData?.data.data ?? [])].sort((a, b) => b.weight - a.weight).slice(0, 5);
  const eventCount = eventsData?.data.data?.events.length ?? 0;

  const badges: Record<string, string> = {
    saved: bookmarkCount > 0 ? String(bookmarkCount) : "",
    agent: eventCount > 0 ? String(eventCount) : "",
  };

  const activeId = NAV_ITEMS.find((item) => pathname === item.href || pathname.startsWith(item.href + "/"))?.id;
  const settingsActive = pathname.startsWith("/settings");

  return (
    <nav className="border-r border-white/[0.08] px-4 py-5 flex flex-col gap-1 bg-surface h-full box-border font-sans overflow-y-auto">
      <Link href="/feed" className="flex items-center gap-2.5 px-2 pb-[22px] pt-1">
        <Logo size={28} />
        <span className="font-extrabold text-[15px] tracking-tight text-white">
          DeepFeed{" "}
          <span className="bg-gradient-to-r from-accent-pink to-accent-blue bg-clip-text text-transparent">AI</span>
        </span>
      </Link>

      {NAV_ITEMS.map((item) => {
        const active = activeId === item.id;
        const badge = badges[item.id];
        return (
          <Link
            key={item.id}
            href={item.href}
            className={`flex items-center justify-between px-2.5 py-2 rounded-lg text-[13.5px] transition-colors ${
              active ? "bg-accent-purple/[0.18] text-white font-semibold" : "text-ink-muted font-medium hover:text-white"
            }`}
          >
            <span>{item.label}</span>
            {badge && <span className="font-mono text-[11px] text-ink-faint">{badge}</span>}
          </Link>
        );
      })}

      {interests.length > 0 && (
        <>
          <div className="label-mono px-2.5 pt-[22px] pb-2">Interests</div>
          {interests.map((t) => (
            <div key={t.id} className="flex items-center justify-between px-2.5 py-[7px] text-ink-body text-[13px]">
              <span className="truncate">{t.name}</span>
              <span className="font-mono text-[11px] text-ink-faint shrink-0 ml-2">{t.weight.toFixed(1)}</span>
            </div>
          ))}
        </>
      )}

      <div className="mt-auto flex flex-col gap-0.5 pt-3">
        <Link
          href="/settings"
          className={`flex items-center px-2.5 py-2 rounded-lg text-[13.5px] transition-colors ${
            settingsActive ? "bg-accent-purple/[0.18] text-white font-semibold" : "text-ink-muted font-medium hover:text-white"
          }`}
        >
          Settings
        </Link>
        <button
          onClick={() => {
            logout();
            router.push("/login");
          }}
          title="Sign out"
          className="flex items-center gap-2.5 px-2.5 pt-2.5 pb-1 border-t border-white/[0.08] mt-1.5 text-left hover:opacity-80 transition-opacity"
        >
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center text-[11px] font-semibold text-white shrink-0">
            {initialsOf(fullName, email)}
          </div>
          <div className="min-w-0">
            <div className="text-[12.5px] font-semibold text-ink truncate">{fullName || email || "Account"}</div>
            {profile && (
              <div className="font-mono text-[10px] text-ink-faint uppercase">
                {profile.expertise_level} · {profile.preferred_depth}
              </div>
            )}
          </div>
        </button>
      </div>
    </nav>
  );
}
