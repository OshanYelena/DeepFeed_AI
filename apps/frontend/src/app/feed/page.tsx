"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { feedAPI, feedbackAPI, type FeedItem } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { useRouter } from "next/navigation";
import { Bookmark, ThumbsUp, ThumbsDown, ExternalLink, Brain, Zap, Shield, Clock } from "lucide-react";
import toast from "react-hot-toast";
import { formatDistanceToNow } from "date-fns";

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="score-bar w-16">
      <div className="score-fill" style={{ width: `${value * 100}%`, background: color }} />
    </div>
  );
}

function FeedCard({ item }: { item: FeedItem }) {
  const qc = useQueryClient();
  const [dismissed, setDismissed] = useState(false);

  const feedbackMutation = useMutation({
    mutationFn: (type: "like" | "dislike" | "bookmark" | "ignore") =>
      feedbackAPI.submit(item.recommendation_id, type),
    onSuccess: (_, type) => {
      if (type === "dislike" || type === "ignore") setDismissed(true);
      if (type === "like") toast.success("Liked!");
      if (type === "bookmark") toast.success("Bookmarked!");
      qc.invalidateQueries({ queryKey: ["feed"] });
    },
    onError: () => toast.error("Failed to record feedback"),
  });

  if (dismissed) return null;

  const contentTypeBadge = {
    paper: { label: "Paper", bg: "bg-purple-900/40 text-purple-300 border-purple-800" },
    article: { label: "Article", bg: "bg-blue-900/40 text-blue-300 border-blue-800" },
    blog: { label: "Blog", bg: "bg-emerald-900/40 text-emerald-300 border-emerald-800" },
    docs: { label: "Docs", bg: "bg-amber-900/40 text-amber-300 border-amber-800" },
    news: { label: "News", bg: "bg-rose-900/40 text-rose-300 border-rose-800" },
  }[item.content_type] ?? { label: item.content_type, bg: "bg-slate-800 text-slate-300 border-slate-700" };

  return (
    <div className="card p-5 hover:border-slate-600 transition-colors duration-200 animate-slide-up group">
      {/* Header row */}
      <div className="flex items-start gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className={`badge border ${contentTypeBadge.bg}`}>{contentTypeBadge.label}</span>
            <span className="text-slate-500 text-xs">{item.source}</span>
            {item.published_at && (
              <span className="text-slate-600 text-xs">
                {formatDistanceToNow(new Date(item.published_at), { addSuffix: true })}
              </span>
            )}
          </div>
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-white font-medium leading-snug hover:text-brand-400 transition-colors line-clamp-2 group-hover:text-brand-300"
            onClick={() => feedbackAPI.submit(item.recommendation_id, "read")}
          >
            {item.title}
            <ExternalLink className="inline-block ml-1.5 w-3.5 h-3.5 text-slate-500 -translate-y-px" />
          </a>
        </div>

        {/* Score badge */}
        <div className="shrink-0 text-right">
          <div className="text-lg font-bold text-brand-400">{Math.round(item.final_score * 100)}</div>
          <div className="text-xs text-slate-500">score</div>
        </div>
      </div>

      {/* Summary */}
      {item.summary_short && (
        <p className="text-slate-400 text-sm leading-relaxed mb-3 line-clamp-3">{item.summary_short}</p>
      )}

      {/* Why recommended */}
      <div className="flex items-start gap-2 mb-3 p-2.5 bg-brand-900/20 border border-brand-900/40 rounded-lg">
        <Brain className="w-3.5 h-3.5 text-brand-400 mt-0.5 shrink-0" />
        <p className="text-xs text-brand-300">{item.why_recommended}</p>
      </div>

      {/* Score breakdown */}
      <div className="flex items-center gap-4 mb-3">
        <div className="flex items-center gap-1.5">
          <Zap className="w-3 h-3 text-yellow-400" />
          <span className="text-xs text-slate-500">Relevance</span>
          <ScoreBar value={item.relevance_score} color="#eab308" />
        </div>
        <div className="flex items-center gap-1.5">
          <Shield className="w-3 h-3 text-emerald-400" />
          <span className="text-xs text-slate-500">Credibility</span>
          <ScoreBar value={item.credibility_score} color="#10b981" />
        </div>
        <div className="flex items-center gap-1.5">
          <Clock className="w-3 h-3 text-blue-400" />
          <span className="text-xs text-slate-500">Fresh</span>
          <ScoreBar value={item.freshness_score} color="#3b82f6" />
        </div>
      </div>

      {/* Matched interests */}
      {item.matched_interests.length > 0 && (
        <div className="flex gap-1.5 flex-wrap mb-3">
          {item.matched_interests.slice(0, 4).map((interest) => (
            <span key={interest} className="badge bg-slate-800 text-slate-400 border border-slate-700">
              {interest}
            </span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-1 pt-2 border-t border-surface-border">
        <button
          onClick={() => feedbackMutation.mutate("like")}
          disabled={feedbackMutation.isPending}
          className="btn-ghost flex items-center gap-1.5 text-xs"
        >
          <ThumbsUp className="w-3.5 h-3.5" /> Like
        </button>
        <button
          onClick={() => feedbackMutation.mutate("bookmark")}
          disabled={feedbackMutation.isPending}
          className="btn-ghost flex items-center gap-1.5 text-xs"
        >
          <Bookmark className="w-3.5 h-3.5" /> Bookmark
        </button>
        <button
          onClick={() => feedbackMutation.mutate("dislike")}
          disabled={feedbackMutation.isPending}
          className="btn-ghost flex items-center gap-1.5 text-xs text-slate-500"
        >
          <ThumbsDown className="w-3.5 h-3.5" /> Not relevant
        </button>
      </div>
    </div>
  );
}

export default function FeedPage() {
  const { isAuthenticated, logout } = useAuthStore();
  const router = useRouter();
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
    enabled: isAuthenticated,
  });

  if (!isAuthenticated) {
    router.push("/login");
    return null;
  }

  const feed = data?.data.data;

  return (
    <div className="min-h-screen bg-surface">
      {/* Nav */}
      <nav className="sticky top-0 z-40 bg-surface/80 backdrop-blur-sm border-b border-surface-border">
        <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-brand-600 flex items-center justify-center">
              <span className="text-white font-bold text-xs">D</span>
            </div>
            <span className="font-bold text-white">DeepFeed</span>
          </div>
          <div className="flex items-center gap-1">
            <button onClick={() => router.push("/profile")} className="btn-ghost text-xs">Profile</button>
            <button onClick={() => router.push("/agent")} className="btn-ghost text-xs">
              <Brain className="w-3.5 h-3.5 mr-1 inline" />Agent
            </button>
            <button onClick={logout} className="btn-ghost text-xs text-slate-500">Sign out</button>
          </div>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-4 py-6">
        {/* Filters */}
        <div className="flex items-center gap-2 mb-5 flex-wrap">
          {["", "paper", "article", "blog"].map((type) => (
            <button
              key={type}
              onClick={() => { setContentTypeFilter(type); setOffset(0); }}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                contentTypeFilter === type
                  ? "bg-brand-600 text-white"
                  : "bg-surface-card text-slate-400 hover:text-white border border-surface-border"
              }`}
            >
              {type === "" ? "All" : type.charAt(0).toUpperCase() + type.slice(1) + "s"}
            </button>
          ))}
        </div>

        {/* Feed items */}
        {isLoading && (
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
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
            <p className="text-slate-400">Failed to load feed. Please try again.</p>
          </div>
        )}

        {!isLoading && feed && feed.items.length === 0 && (
          <div className="text-center py-16 card p-8">
            <Brain className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h2 className="text-white font-semibold mb-2">No recommendations yet</h2>
            <p className="text-slate-400 text-sm mb-4">
              Add interests to your profile so DeepFeed can discover relevant content.
            </p>
            <button onClick={() => router.push("/profile")} className="btn-primary text-sm">
              Set up interests
            </button>
          </div>
        )}

        {feed && feed.items.length > 0 && (
          <div className="space-y-4">
            {feed.items.map((item) => (
              <FeedCard key={item.recommendation_id} item={item} />
            ))}
          </div>
        )}

        {/* Pagination */}
        {feed && (feed.items.length === LIMIT || offset > 0) && (
          <div className="flex items-center justify-center gap-3 mt-6">
            <button
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}
              disabled={offset === 0}
              className="btn-ghost text-sm disabled:opacity-30"
            >
              ← Previous
            </button>
            <span className="text-slate-500 text-sm">Page {Math.floor(offset / LIMIT) + 1}</span>
            <button
              onClick={() => setOffset(offset + LIMIT)}
              disabled={feed.items.length < LIMIT}
              className="btn-ghost text-sm disabled:opacity-30"
            >
              Next →
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
