"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { feedAPI, feedbackAPI } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth-store";
import { useLibraryStore } from "@/lib/library-store";
import { contentTypeStyle } from "@/lib/content-type";
import { shortAge } from "@/lib/format";
import { AppShell } from "@/components/layout/AppShell";
import { AgentPanel } from "@/components/agent/AgentPanel";
import toast from "react-hot-toast";

function sourceOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "").toUpperCase();
  } catch {
    return "";
  }
}

function takeawaysOf(raw: unknown): string[] {
  if (Array.isArray(raw)) return raw as string[];
  if (raw && typeof raw === "object" && Array.isArray((raw as any).takeaways)) return (raw as any).takeaways;
  return [];
}

const SCORE_META = [
  { key: "final" as const, label: "FINAL", color: "#c9bdff" },
  { key: "relevance" as const, label: "RELEVANCE", color: "#eab308" },
  { key: "credibility" as const, label: "CREDIBILITY", color: "#10b981" },
  { key: "freshness" as const, label: "FRESHNESS", color: "#3b82f6" },
];

export default function FeedDetailPage() {
  const ready = useRequireAuth();
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const qc = useQueryClient();
  const bookmarked = useLibraryStore((s) => Boolean(s.bookmarks[params.id]));
  const liked = useLibraryStore((s) => Boolean(s.liked[params.id]));
  const setBookmarked = useLibraryStore((s) => s.setBookmarked);
  const setLiked = useLibraryStore((s) => s.setLiked);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["feed-detail", params.id],
    queryFn: () => feedAPI.getDetail(params.id),
    enabled: ready && Boolean(params.id),
  });

  const feedbackMutation = useMutation({
    mutationFn: (kind: "like" | "dislike" | "bookmark" | "ignore") => feedbackAPI.submit(params.id, kind),
    onSuccess: (_, kind) => {
      if (kind === "like") { setLiked(params.id, !liked); toast.success(liked ? "Removed like" : "Liked!"); }
      if (kind === "bookmark") { setBookmarked(params.id, !bookmarked); toast.success(bookmarked ? "Removed bookmark" : "Bookmarked!"); }
      qc.invalidateQueries({ queryKey: ["feed"] });
    },
    onError: () => toast.error("Failed to record feedback"),
  });

  if (!ready) return null;

  const item = data?.data.data;
  const type = item ? contentTypeStyle(item.content_type) : null;
  const scores = item?.scoring_breakdown ?? {};
  const takeaways = takeawaysOf(item?.key_takeaways);
  const paragraphs = (item?.summary_detailed ?? "").split(/\n+/).filter(Boolean);

  return (
    <AppShell panel={<AgentPanel context="THIS PAPER" />}>
      <div className="px-9 pt-7 pb-14 max-w-[900px]">
        <div className="flex items-center gap-3.5 text-[13px] text-ink-dim mb-4">
          <button onClick={() => router.push("/feed")} className="hover:text-ink transition-colors">← Today</button>
          {item && (
            <>
              <button
                onClick={() => feedbackMutation.mutate("like")}
                className={`ml-auto font-semibold hover:text-white transition-colors ${liked ? "text-accent-purpleText" : "text-ink-body"}`}
              >
                Like
              </button>
              <button
                onClick={() => feedbackMutation.mutate("bookmark")}
                className={`font-semibold hover:text-white transition-colors ${bookmarked ? "text-accent-purpleText" : "text-ink-body"}`}
              >
                Bookmark
              </button>
              <a href={item.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-accent-purpleText hover:text-white transition-colors">
                Open original ↗
              </a>
            </>
          )}
        </div>

        {isLoading && <div className="text-ink-muted text-sm">Loading…</div>}
        {isError && <div className="text-ink-muted text-sm">Couldn&apos;t load this item.</div>}

        {item && type && (
          <div className="flex flex-col gap-[18px]">
            <div className="flex items-center gap-2 font-mono text-[10.5px] tracking-wide text-ink-dim">
              <span className="badge border" style={{ background: type.bg, color: type.text, borderColor: type.border }}>
                {type.label.toUpperCase()}
              </span>
              <span>{sourceOf(item.url)}</span>
              <span>·</span>
              <span>{shortAge(item.published_at)}</span>
            </div>

            <h1 className="font-serif text-[34px] leading-[1.15] tracking-tight text-ink max-w-[700px]">{item.title}</h1>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {SCORE_META.map(({ key, label, color }) => {
                const value = key === "final" ? item.final_score : scores[key];
                if (value === undefined || value === null) return null;
                return (
                  <div key={key} className="px-3.5 py-3 rounded-[10px] bg-surface-card border border-white/[0.08]">
                    <div className="font-mono text-[10px] tracking-wide text-ink-soft mb-1.5">{label}</div>
                    <div className="flex items-baseline gap-2">
                      <span className="font-mono text-[22px] leading-none" style={{ color }}>{Math.round(value * 100)}</span>
                      <span className="flex-1 h-[3px] rounded-full bg-surface-hover">
                        <span className="block h-full rounded-full" style={{ width: `${value * 100}%`, background: color }} />
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-8">
              <div className="flex flex-col gap-3.5 min-w-0">
                <div className="label-mono">Detailed summary</div>
                {paragraphs.length > 0 ? (
                  paragraphs.map((p, i) => (
                    <p key={i} className="font-serif text-[15px] leading-[1.65] text-ink-para">{p}</p>
                  ))
                ) : item.summary_short ? (
                  <p className="font-serif text-[15px] leading-[1.65] text-ink-para">{item.summary_short}</p>
                ) : (
                  <p className="text-sm text-ink-faint">No summary available yet.</p>
                )}
              </div>

              <div className="flex flex-col gap-5">
                {takeaways.length > 0 && (
                  <div>
                    <div className="label-mono mb-2.5">Key takeaways</div>
                    <div className="flex flex-col gap-2 text-[13px] leading-relaxed text-ink-para">
                      {takeaways.map((t, i) => (
                        <div key={i} className="flex gap-2.5">
                          <span className="font-mono text-[11px] text-ink-soft pt-0.5">{String(i + 1).padStart(2, "0")}</span>
                          <span>{t}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {item.topics.length > 0 && (
                  <div>
                    <div className="label-mono mb-2.5">Topics</div>
                    <div className="flex flex-wrap gap-1.5">
                      {item.topics.map((t) => (
                        <span key={t.name} className="px-2 py-1 rounded-md border border-white/10 text-xs text-ink-body">
                          {t.name} <span className="font-mono text-[10px] text-ink-faint">{t.confidence.toFixed(2)}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {item.why_recommended && (
                  <div className="px-3.5 py-3 rounded-[10px] bg-accent-purple/10 text-[12.5px] leading-relaxed text-accent-purpleSoft">
                    <span className="font-mono text-[10px] tracking-wide text-ink-dim mr-1.5">WHY</span>
                    {item.why_recommended}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
