"use client";

import { useMemo, useState } from "react";
import { useQueries } from "@tanstack/react-query";
import { feedAPI } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth-store";
import { useLibraryStore } from "@/lib/library-store";
import { contentTypeStyle } from "@/lib/content-type";
import { AppShell } from "@/components/layout/AppShell";
import { formatDistanceToNow } from "date-fns";
import { Bookmark } from "lucide-react";
import Link from "next/link";

const TABS = [
  { id: "all", label: "All" },
  { id: "paper", label: "Papers" },
  { id: "article", label: "Articles" },
  { id: "liked", label: "Liked" },
];

export default function SavedPage() {
  const ready = useRequireAuth();
  const bookmarks = useLibraryStore((s) => s.bookmarks);
  const liked = useLibraryStore((s) => s.liked);
  const [tab, setTab] = useState("all");

  const ids = useMemo(() => Object.keys(bookmarks), [bookmarks]);

  const results = useQueries({
    queries: ids.map((id) => ({
      queryKey: ["feed-detail", id],
      queryFn: () => feedAPI.getDetail(id),
      enabled: ready,
    })),
  });

  const items = results
    .map((r) => r.data?.data.data)
    .filter((item): item is NonNullable<typeof item> => Boolean(item));

  const isLoading = ready && ids.length > 0 && items.length === 0 && results.some((r) => r.isLoading);

  const filtered = items.filter((item) => {
    if (tab === "all") return true;
    if (tab === "liked") return Boolean(liked[item.recommendation_id]);
    return item.content_type === tab;
  });

  const byType = items.reduce<Record<string, number>>((acc, item) => {
    acc[item.content_type] = (acc[item.content_type] ?? 0) + 1;
    return acc;
  }, {});

  if (!ready) return null;

  return (
    <AppShell>
      <div className="px-9 pt-7 pb-14 grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_320px] gap-10 max-w-[1180px]">
        <div className="flex flex-col gap-[18px] min-w-0">
          <div className="flex items-baseline justify-between">
            <h1 className="font-serif text-[30px] leading-tight text-ink m-0">Saved</h1>
            <span className="font-mono text-[11px] text-ink-faint">{items.length} ITEMS</span>
          </div>

          <div className="flex gap-1.5">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-3 py-[7px] rounded-lg text-[12.5px] font-semibold transition-colors ${
                  tab === t.id ? "bg-white text-surface" : "text-ink-muted border border-white/10 hover:text-white"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {ids.length === 0 && (
            <div className="card p-8 text-center">
              <Bookmark className="w-8 h-8 text-ink-faint mx-auto mb-3" />
              <p className="text-ink font-medium text-sm mb-1.5">Nothing saved yet</p>
              <p className="text-ink-muted text-xs">
                Bookmark items from your <Link href="/feed" className="text-accent-purpleText font-semibold">feed</Link> to build a reading list.
              </p>
            </div>
          )}

          {isLoading && ids.length > 0 && <div className="text-ink-muted text-sm">Loading saved items…</div>}

          {filtered.length > 0 && (
            <div className="flex flex-col">
              {filtered
                .sort((a, b) => (bookmarks[b.recommendation_id] ?? "").localeCompare(bookmarks[a.recommendation_id] ?? ""))
                .map((item) => {
                  const type = contentTypeStyle(item.content_type);
                  const savedAt = bookmarks[item.recommendation_id];
                  return (
                    <Link
                      key={item.recommendation_id}
                      href={`/feed/${item.recommendation_id}`}
                      className="grid grid-cols-[minmax(0,1fr)_120px_60px] gap-4 items-center py-3.5 border-t border-white/[0.08] hover:bg-white/[0.02] -mx-2 px-2 rounded-lg transition-colors"
                    >
                      <div className="min-w-0">
                        <div className="flex gap-2 font-mono text-[10.5px] tracking-wide text-ink-dim mb-1.5">
                          <span className="px-1.5 py-px rounded" style={{ background: type.bg, color: type.text }}>{type.label.toUpperCase()}</span>
                          <span>{new URL(item.url).hostname.replace(/^www\./, "").toUpperCase()}</span>
                          {savedAt && <><span>·</span><span>SAVED {formatDistanceToNow(new Date(savedAt), { addSuffix: true }).toUpperCase()}</span></>}
                        </div>
                        <div className="font-serif text-[16px] leading-snug text-ink">{item.title}</div>
                      </div>
                      <span className="font-mono text-[10.5px] text-right" style={{ color: liked[item.recommendation_id] ? "#d946ef" : "#5d6280" }}>
                        {liked[item.recommendation_id] ? "LIKED" : ""}
                      </span>
                      <span className="font-mono text-[15px] text-ink-body text-right">{Math.round(item.final_score * 100)}</span>
                    </Link>
                  );
                })}
            </div>
          )}
        </div>

        <div className="flex flex-col gap-4 pt-2 lg:pt-14">
          <div className="relative px-5 py-[18px] rounded-[14px] border border-white/10 overflow-hidden" style={{ background: "linear-gradient(180deg, rgba(124,92,246,.14), rgba(124,92,246,.03))" }}>
            <span className="absolute inset-y-0 left-0 w-0.5 bg-rail-gradient" />
            <div className="label-mono mb-2">AI digest</div>
            <div className="font-serif text-[16px] leading-snug text-ink mb-2">Turn your saves into a 5-minute read</div>
            <div className="text-[12.5px] leading-relaxed text-ink-muted mb-3.5">
              Grouped digests aren&apos;t wired up yet — this needs a summarization endpoint the backend doesn&apos;t expose.
            </div>
            <span className="inline-block px-3.5 py-2 rounded-lg bg-white/10 text-ink-faint text-[12.5px] font-bold cursor-not-allowed">
              Generate digest
            </span>
          </div>

          {items.length > 0 && (
            <div className="card px-4.5 py-4 px-[18px]">
              <div className="label-mono mb-3">By type</div>
              <div className="flex flex-col gap-2.5 text-[13.5px]">
                {Object.entries(byType).map(([type, count]) => (
                  <div key={type} className="flex justify-between">
                    <span className="capitalize text-ink-body">{type}s</span>
                    <span className="font-mono text-[11px] text-ink-faint">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
