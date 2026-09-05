"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { feedAPI, type FeedItem } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth-store";
import { useLibraryStore } from "@/lib/library-store";
import { contentTypeStyle } from "@/lib/content-type";
import { shortAge } from "@/lib/format";
import { AppShell } from "@/components/layout/AppShell";
import { SearchIcon } from "lucide-react";
import Link from "next/link";

const SCOPES = [
  { id: "all", label: "Everything" },
  { id: "paper", label: "Papers" },
  { id: "saved", label: "Saved only" },
  { id: "recent", label: "Last 30 days" },
];

function matchScore(item: FeedItem, terms: string[]): number {
  const haystack = `${item.title} ${item.summary_short ?? ""} ${item.source}`.toLowerCase();
  let hits = 0;
  for (const term of terms) if (haystack.includes(term)) hits += 1;
  return hits / terms.length;
}

export default function SearchPage() {
  const ready = useRequireAuth();
  const bookmarks = useLibraryStore((s) => s.bookmarks);
  const addRecentSearch = useLibraryStore((s) => s.addRecentSearch);
  const recentSearches = useLibraryStore((s) => s.recentSearches);
  const [query, setQuery] = useState("");
  const [committed, setCommitted] = useState("");
  const [scope, setScope] = useState("all");

  const { data, isLoading } = useQuery({
    queryKey: ["feed-search-corpus"],
    queryFn: () => feedAPI.getFeed({ limit: 100, offset: 0 }),
    enabled: ready,
  });

  const items = useMemo(() => data?.data.data.items ?? [], [data]);
  const terms = committed.trim().toLowerCase().split(/\s+/).filter(Boolean);

  const results = useMemo(() => {
    let pool = items;
    if (scope === "paper") pool = pool.filter((i) => i.content_type === "paper");
    if (scope === "saved") pool = pool.filter((i) => bookmarks[i.recommendation_id]);
    if (scope === "recent") pool = pool.filter((i) => i.published_at && Date.now() - new Date(i.published_at).getTime() < 30 * 86400_000);

    if (terms.length === 0) return pool.slice(0, 20);
    return pool
      .map((item) => ({ item, score: matchScore(item, terms) }))
      .filter((r) => r.score > 0)
      .sort((a, b) => b.score - a.score)
      .map((r) => ({ ...r.item, __score: r.score }));
  }, [items, scope, terms, bookmarks]);

  const relatedTopics = useMemo(() => {
    const counts = new Map<string, number>();
    for (const item of items) for (const t of item.matched_interests) counts.set(t, (counts.get(t) ?? 0) + 1);
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5);
  }, [items]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setCommitted(query);
    addRecentSearch(query);
  };

  if (!ready) return null;

  return (
    <AppShell>
      <div className="px-9 pt-7 pb-14 flex flex-col gap-5 max-w-[900px]">
        <form
          onSubmit={submit}
          className="flex items-center gap-3 px-[18px] py-3.5 rounded-xl bg-surface-card border border-accent-purple/50"
          style={{ boxShadow: "0 0 0 4px rgba(124,92,246,.08)" }}
        >
          <SearchIcon className="w-4 h-4 text-accent-purpleText shrink-0" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search your feed…"
            className="flex-1 bg-transparent outline-none text-[16px] text-ink placeholder-ink-faint"
          />
          <span className="font-mono text-[11px] text-ink-faint shrink-0">KEYWORD · {items.length} ITEMS LOADED</span>
        </form>

        <div className="flex gap-1.5 text-[12.5px] font-semibold">
          {SCOPES.map((s) => (
            <button
              key={s.id}
              onClick={() => setScope(s.id)}
              className={`px-2.5 py-1.5 rounded-lg transition-colors ${
                scope === s.id ? "bg-white text-surface" : "text-ink-muted border border-white/10 hover:text-white"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>

        <div className="relative px-[22px] py-[18px] rounded-[14px] border border-white/10 overflow-hidden" style={{ background: "linear-gradient(180deg, rgba(124,92,246,.12), rgba(124,92,246,.03))" }}>
          <span className="absolute inset-y-0 left-0 w-0.5 bg-rail-gradient" />
          <div className="label-mono mb-2">Keyword search</div>
          <div className="text-[13.5px] leading-relaxed text-ink-para">
            {committed
              ? `${results.length} match${results.length === 1 ? "" : "es"} for "${committed}" across your loaded feed. This is plain keyword matching — semantic search isn't available without a backend endpoint for it.`
              : "Type a query and press enter to search titles, summaries and sources across your feed."}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_240px] gap-8">
          <div className="flex flex-col min-w-0">
            <div className="label-mono pb-2">Results · {results.length}</div>
            {isLoading && <div className="text-ink-muted text-sm py-3">Loading your feed…</div>}
            {!isLoading && results.length === 0 && (
              <div className="text-ink-muted text-sm py-3">No matches. Try a different term or scope.</div>
            )}
            {results.map((item) => {
              const type = contentTypeStyle(item.content_type);
              const score = (item as any).__score as number | undefined;
              return (
                <Link
                  key={item.recommendation_id}
                  href={`/feed/${item.recommendation_id}`}
                  className="grid grid-cols-[minmax(0,1fr)_60px] gap-4 py-3.5 border-t border-white/[0.08] hover:bg-white/[0.02] -mx-2 px-2 rounded-lg transition-colors"
                >
                  <div>
                    <div className="flex gap-2 font-mono text-[10.5px] tracking-wide text-ink-dim mb-1">
                      <span className="px-1.5 py-px rounded" style={{ background: type.bg, color: type.text }}>{type.label.toUpperCase()}</span>
                      <span>{item.source}</span>
                      <span>·</span>
                      <span>{shortAge(item.published_at)}</span>
                    </div>
                    <div className="font-serif text-[15.5px] leading-snug text-ink">{item.title}</div>
                  </div>
                  <span className="font-mono text-[11px] text-ink-soft text-right pt-[22px]">
                    {score !== undefined ? score.toFixed(2) : ""}
                  </span>
                </Link>
              );
            })}
          </div>

          <div className="flex flex-col gap-3">
            {relatedTopics.length > 0 && (
              <>
                <div className="label-mono">Related topics</div>
                {relatedTopics.map(([name, n]) => (
                  <div key={name} className="flex justify-between text-[13px] text-ink-body">
                    <span>{name}</span>
                    <span className="font-mono text-[11px] text-ink-faint">{n}</span>
                  </div>
                ))}
              </>
            )}
            {recentSearches.length > 0 && (
              <>
                <div className="label-mono mt-3">Recent searches</div>
                <div className="flex flex-col gap-2">
                  {recentSearches.map((q) => (
                    <button
                      key={q}
                      onClick={() => { setQuery(q); setCommitted(q); }}
                      className="text-left text-[13px] text-ink-muted hover:text-ink transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
