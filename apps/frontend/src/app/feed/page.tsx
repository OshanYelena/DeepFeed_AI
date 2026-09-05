"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { feedAPI, feedbackAPI, contentAPI, type FeedItem } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth-store";
import { useLibraryStore } from "@/lib/library-store";
import { contentTypeStyle } from "@/lib/content-type";
import { shortAge, scorePct } from "@/lib/format";
import { AppShell } from "@/components/layout/AppShell";
import { AgentPanel } from "@/components/agent/AgentPanel";
import { ScoreBar } from "@/components/ScoreBar";
import { useRouter } from "next/navigation";
import { Search, Loader2, Brain } from "lucide-react";
import toast from "react-hot-toast";

const FILTERS = [
  { value: "", label: "All" },
  { value: "paper", label: "Papers" },
  { value: "article", label: "Articles" },
  { value: "blog", label: "Blogs" },
  { value: "news", label: "News" },
];

function useDiscoverNow(enabled: boolean) {
  const qc = useQueryClient();

  const statusQuery = useQuery({
    queryKey: ["discover-status"],
    queryFn: () => contentAPI.getStatus(),
    enabled,
    refetchInterval: 15_000,
  });
  const status = statusQuery.data?.data.data;

  const discoverMutation = useMutation({
    mutationFn: async () => {
      const res = await contentAPI.discover();
      if (res.data.error) throw new Error(res.data.error.message);
      return res.data.data!;
    },
    onSuccess: (data) => {
      if (data.status === "completed") {
        toast.success(
          data.new_items_count
            ? `Found ${data.new_items_count} new items — updating your feed`
            : "Search complete — no new items this time"
        );
      } else {
        toast.error(data.error_message || "Search failed");
      }
      qc.invalidateQueries({ queryKey: ["feed"] });
      qc.invalidateQueries({ queryKey: ["discover-status"] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const isRunning = discoverMutation.isPending;
  const cooldown = status?.cooldown_seconds_remaining ?? 0;
  const quotaLeft = status?.daily.remaining ?? 1;

  let label = "Discover now";
  let disabled = false;
  if (isRunning) {
    label = "Searching…";
    disabled = true;
  } else if (quotaLeft <= 0) {
    label = "Daily limit reached";
    disabled = true;
  } else if (cooldown > 0) {
    label = `Wait ${cooldown}s`;
    disabled = true;
  }

  return { label, disabled, isRunning, status, trigger: () => discoverMutation.mutate() };
}

function FeedCard({ item }: { item: FeedItem }) {
  const qc = useQueryClient();
  const router = useRouter();
  const [dismissed, setDismissed] = useState(false);
  const bookmarked = useLibraryStore((s) => Boolean(s.bookmarks[item.recommendation_id]));
  const setBookmarked = useLibraryStore((s) => s.setBookmarked);
  const setLiked = useLibraryStore((s) => s.setLiked);
  const liked = useLibraryStore((s) => Boolean(s.liked[item.recommendation_id]));
  const type = contentTypeStyle(item.content_type);

  const feedbackMutation = useMutation({
    mutationFn: (kind: "like" | "dislike" | "bookmark" | "ignore") =>
      feedbackAPI.submit(item.recommendation_id, kind),
    onSuccess: (_, kind) => {
      if (kind === "dislike" || kind === "ignore") setDismissed(true);
      if (kind === "like") { setLiked(item.recommendation_id, !liked); toast.success(liked ? "Removed like" : "Liked!"); }
      if (kind === "bookmark") { setBookmarked(item.recommendation_id, !bookmarked); toast.success(bookmarked ? "Removed bookmark" : "Bookmarked!"); }
      qc.invalidateQueries({ queryKey: ["feed"] });
    },
    onError: () => toast.error("Failed to record feedback"),
  });

  if (dismissed) return null;

  return (
    <article className="px-5 py-[18px] rounded-xl bg-surface-card border border-white/[0.08] flex flex-col gap-2.5 animate-slide-up">
      <div className="flex gap-3.5 items-start">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 font-mono text-[10.5px] tracking-wide text-ink-dim mb-2">
            <span className="badge border" style={{ background: type.bg, color: type.text, borderColor: type.border }}>
              {type.label.toUpperCase()}
            </span>
            <span>{item.source}</span>
            <span>·</span>
            <span>{shortAge(item.published_at)}</span>
          </div>
          <button
            onClick={() => router.push(`/feed/${item.recommendation_id}`)}
            className="text-left font-serif text-lg leading-tight text-ink hover:text-accent-purpleText transition-colors"
          >
            {item.title}
          </button>
          {item.summary_short && (
            <p className="mt-1.5 text-[13px] leading-relaxed text-ink-muted line-clamp-3">{item.summary_short}</p>
          )}
        </div>
        <div className="text-right shrink-0">
          <div className="font-mono text-[26px] leading-none bg-brand-gradient-h bg-clip-text text-transparent">
            {Math.round(item.final_score * 100)}
          </div>
          <div className="font-mono text-[10px] text-ink-faint mt-1">SCORE</div>
        </div>
      </div>

      {item.why_recommended && (
        <div className="flex items-center gap-2 px-2.5 py-2 rounded-lg bg-accent-purple/10 text-[12px] text-accent-purpleSoft">
          <span className="font-mono text-[10px] tracking-wide text-ink-dim">WHY</span>
          {item.why_recommended}
        </div>
      )}

      <div className="flex items-center gap-[18px] font-mono text-[10.5px] text-ink-soft flex-wrap">
        <span className="flex items-center gap-1.5">RELEVANCE <ScoreBar value={item.relevance_score} color="#eab308" /></span>
        <span className="flex items-center gap-1.5">CREDIBILITY <ScoreBar value={item.credibility_score} color="#10b981" /></span>
        <span className="flex items-center gap-1.5">FRESH <ScoreBar value={item.freshness_score} color="#3b82f6" /></span>
        {item.matched_interests.length > 0 && (
          <span className="ml-auto flex gap-1.5">
            {item.matched_interests.slice(0, 3).map((interest) => (
              <span key={interest} className="px-1.5 py-0.5 rounded border border-white/10 text-ink-muted">
                {interest}
              </span>
            ))}
          </span>
        )}
      </div>

      <div className="flex gap-1 pt-2.5 border-t border-white/[0.08] text-xs font-semibold text-ink-body">
        <button
          onClick={() => feedbackMutation.mutate("like")}
          disabled={feedbackMutation.isPending}
          className={`px-2.5 py-1.5 rounded-lg hover:bg-white/[0.06] transition-colors ${liked ? "text-accent-purpleText" : ""}`}
        >
          Like
        </button>
        <button
          onClick={() => feedbackMutation.mutate("bookmark")}
          disabled={feedbackMutation.isPending}
          className={`px-2.5 py-1.5 rounded-lg hover:bg-white/[0.06] transition-colors ${bookmarked ? "text-accent-purpleText" : ""}`}
        >
          Bookmark
        </button>
        <button
          onClick={() => feedbackMutation.mutate("dislike")}
          disabled={feedbackMutation.isPending}
          className="px-2.5 py-1.5 rounded-lg hover:bg-white/[0.06] transition-colors text-ink-soft"
        >
          Not relevant
        </button>
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => feedbackAPI.submit(item.recommendation_id, "read")}
          className="ml-auto px-2.5 py-1.5 rounded-lg hover:bg-white/[0.06] transition-colors text-accent-purpleText"
        >
          Open ↗
        </a>
      </div>
    </article>
  );
}

export default function FeedPage() {
  const ready = useRequireAuth();
  const [offset, setOffset] = useState(0);
  const [contentTypeFilter, setContentTypeFilter] = useState<string>("");
  const LIMIT = 20;

  const { data, isLoading, isError } = useQuery({
    queryKey: ["feed", offset, contentTypeFilter],
    queryFn: () =>
      feedAPI.getFeed({
        limit: LIMIT,
        offset,
        content_type: contentTypeFilter || undefined,
      }),
    enabled: ready,
  });

  const discover = useDiscoverNow(ready);

  if (!ready) return null;

  const feed = data?.data.data;
  const items = feed?.items ?? [];
  const topPicks = [...items].sort((a, b) => b.final_score - a.final_score).slice(0, 3);

  const today = new Date().toLocaleDateString("en-US", { weekday: "long", day: "numeric", month: "long" }).toUpperCase();
  const nextAuto = discover.status?.next_scheduled_at
    ? new Date(discover.status.next_scheduled_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : null;

  return (
    <AppShell panel={<AgentPanel context="FEED" />}>
      <div className="px-9 pt-7 pb-10 flex flex-col gap-5 max-w-[880px]">
        {/* Header */}
        <div className="flex items-end justify-between gap-4 flex-wrap">
          <div>
            <div className="font-mono text-[11px] font-medium tracking-[0.08em] text-ink-dim">{today}</div>
            <h1 className="mt-1.5 font-serif text-[30px] leading-tight tracking-tight text-ink">Your brief</h1>
          </div>
          <div className="flex items-center gap-3">
            {discover.status && (
              <span className="font-mono text-[11px] text-ink-faint">
                DISCOVERY {discover.status.daily.used} / {discover.status.daily.limit} TODAY
                {nextAuto ? ` · NEXT AUTO ${nextAuto}` : ""}
              </span>
            )}
            <button
              onClick={discover.trigger}
              disabled={discover.disabled}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-brand-gradient text-white text-[13px] font-bold disabled:opacity-50 transition-opacity hover:opacity-90"
            >
              {discover.isRunning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <span className="w-1.5 h-1.5 rounded-full bg-white" />}
              {discover.label}
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-1.5 items-center flex-wrap">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => { setContentTypeFilter(f.value); setOffset(0); }}
              className={`px-3 py-[7px] rounded-lg text-[12.5px] font-semibold transition-colors ${
                contentTypeFilter === f.value
                  ? "bg-white text-surface"
                  : "text-ink-muted border border-white/10 hover:text-white"
              }`}
            >
              {f.label}
            </button>
          ))}
          <span className="ml-auto font-mono text-[11px] text-ink-faint">{items.length} ITEMS</span>
        </div>

        {/* Top picks */}
        {topPicks.length > 0 && (
          <div className="relative border border-white/10 rounded-[14px] px-[22px] pt-[18px] pb-4 bg-gradient-to-b from-accent-purple/[0.12] to-accent-purple/[0.03] overflow-hidden">
            <span className="absolute inset-y-0 left-0 w-0.5 bg-rail-gradient" />
            <div className="flex items-center gap-2 font-mono text-[11px] font-medium tracking-[0.08em] text-accent-purpleText mb-2.5">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-pink shadow-[0_0_10px_#d946ef]" />
              TOP PICKS · FROM {items.length} ITEMS
            </div>
            <div className="grid gap-5" style={{ gridTemplateColumns: `repeat(${topPicks.length}, minmax(0,1fr))` }}>
              {topPicks.map((p) => (
                <div key={p.recommendation_id}>
                  <div className="font-serif text-[15px] leading-snug text-ink mb-1">{p.title}</div>
                  <div className="text-xs leading-relaxed text-ink-muted line-clamp-3">{p.summary_short}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Feed items */}
        {isLoading && (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="card p-5 animate-pulse">
                <div className="h-4 bg-surface-hover rounded w-3/4 mb-3" />
                <div className="h-3 bg-surface-hover rounded w-full mb-2" />
                <div className="h-3 bg-surface-hover rounded w-2/3" />
              </div>
            ))}
          </div>
        )}

        {isError && (
          <div className="text-center py-12">
            <p className="text-ink-muted">Failed to load feed. Please try again.</p>
          </div>
        )}

        {!isLoading && items.length === 0 && (
          <div className="text-center py-16 card p-8">
            <Brain className="w-10 h-10 text-ink-faint mx-auto mb-3" />
            <h2 className="text-ink font-semibold mb-2">No recommendations yet</h2>
            <p className="text-ink-muted text-sm mb-4">
              Search now to pull in content matching your interests, or add more interests first for better results.
            </p>
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={discover.trigger}
                disabled={discover.disabled}
                className="btn-primary text-sm flex items-center gap-1.5"
              >
                {discover.isRunning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                {discover.label}
              </button>
              <a href="/profile" className="btn-ghost text-sm">Set up interests</a>
            </div>
          </div>
        )}

        {items.length > 0 && (
          <div className="flex flex-col gap-3">
            {items.map((item) => (
              <FeedCard key={item.recommendation_id} item={item} />
            ))}
          </div>
        )}

        {feed && (items.length === LIMIT || offset > 0) && (
          <div className="flex items-center justify-center gap-3 mt-2">
            <button onClick={() => setOffset(Math.max(0, offset - LIMIT))} disabled={offset === 0} className="btn-ghost text-sm disabled:opacity-30">
              ← Previous
            </button>
            <span className="text-ink-faint text-sm">Page {Math.floor(offset / LIMIT) + 1}</span>
            <button onClick={() => setOffset(offset + LIMIT)} disabled={items.length < LIMIT} className="btn-ghost text-sm disabled:opacity-30">
              Next →
            </button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
