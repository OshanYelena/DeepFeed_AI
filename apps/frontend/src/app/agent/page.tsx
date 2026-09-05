"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { agentAPI, type AdaptationEvent } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth-store";
import { AppShell } from "@/components/layout/AppShell";
import { shortAge } from "@/lib/format";
import { RefreshCw, Target, Sparkles, Brain } from "lucide-react";
import toast from "react-hot-toast";

const EVENT_COLOR: Record<string, string> = {
  topic_weight_update: "#eab308",
  search_plan_generated: "#3b82f6",
  full_cycle_completed: "#10b981",
  reflection_completed: "#b9a6ff",
};

function AgentEventRow({ event }: { event: AdaptationEvent }) {
  const color = EVENT_COLOR[event.event_type] ?? "#9aa0b8";
  return (
    <div className="grid grid-cols-[8px_minmax(0,1fr)_44px] gap-3 py-[11px] border-t border-white/[0.06] first:border-t-0">
      <span className="w-2 h-2 rounded-full mt-1.5" style={{ background: color }} />
      <div className="min-w-0">
        <div className="flex gap-2 font-mono text-[10.5px] tracking-wide">
          <span className="text-ink-body">{event.agent}</span>
          <span style={{ color }}>{event.event_type.replace(/_/g, " ")}</span>
          <span className="ml-auto text-ink-faint">{shortAge(event.created_at)}</span>
        </div>
        <div className="text-[12.5px] leading-snug text-ink-muted mt-1">{event.reason}</div>
      </div>
      <span className="font-mono text-[11px] text-ink-soft text-right">{Math.round(event.confidence * 100)}%</span>
    </div>
  );
}

export default function AgentPage() {
  const ready = useRequireAuth();

  const { data: insightsData } = useQuery({
    queryKey: ["agent-insights"],
    queryFn: () => agentAPI.getProfileInsights(),
    enabled: ready,
  });
  const { data: topicsData } = useQuery({
    queryKey: ["agent-topics"],
    queryFn: () => agentAPI.getTopicPreferences(),
    enabled: ready,
  });
  const { data: eventsData } = useQuery({
    queryKey: ["agent-events"],
    queryFn: () => agentAPI.getAdaptationEvents(),
    enabled: ready,
  });
  const { data: reflectionData } = useQuery({
    queryKey: ["agent-reflection"],
    queryFn: () => agentAPI.getLatestReflection(),
    enabled: ready,
    retry: false,
  });

  const runAdaptation = useMutation({
    mutationFn: () => agentAPI.runAdaptation(),
    onSuccess: () => toast.success("Adaptation cycle started"),
    onError: () => toast.error("Failed to start adaptation"),
  });
  const generatePlan = useMutation({
    mutationFn: () => agentAPI.generateSearchPlan(),
    onSuccess: () => toast.success("Search plan generated"),
    onError: () => toast.error("Failed to generate plan"),
  });
  const runReflection = useMutation({
    mutationFn: () => agentAPI.runReflection(),
    onSuccess: () => toast.success("Reflection report generated"),
    onError: () => toast.error("Reflection failed"),
  });

  if (!ready) return null;

  const insights = insightsData?.data.data;
  const topics = topicsData?.data.data?.topics ?? [];
  const events = eventsData?.data.data?.events ?? [];
  const reflection = reflectionData?.data.data;

  return (
    <AppShell>
      <div className="px-9 pt-7 pb-14 flex flex-col gap-5 max-w-[1120px]">
        <div className="flex items-end justify-between gap-4 flex-wrap">
          <div>
            <h1 className="font-serif text-[30px] leading-tight text-ink m-0">Agent</h1>
            <div className="mt-1.5 text-[13px] text-ink-dim">What DeepFeed has learned about you, and every change it made.</div>
          </div>
          <div className="flex gap-2 text-[12.5px] font-semibold flex-wrap">
            <button
              onClick={() => runAdaptation.mutate()}
              disabled={runAdaptation.isPending}
              className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-[9px] bg-brand-gradient text-white disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${runAdaptation.isPending ? "animate-spin" : ""}`} />
              Run adaptation
            </button>
            <button
              onClick={() => generatePlan.mutate()}
              disabled={generatePlan.isPending}
              className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-[9px] border border-white/[0.14] text-ink-para disabled:opacity-50"
            >
              <Target className="w-3.5 h-3.5" />
              Generate search plan
            </button>
            <button
              onClick={() => runReflection.mutate()}
              disabled={runReflection.isPending}
              className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-[9px] border border-white/[0.14] text-ink-para disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Run reflection
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] gap-5">
          <div className="flex flex-col gap-5 min-w-0">
            {topics.length > 0 && (
              <div className="card px-5 py-[18px]">
                <div className="label-mono mb-3">Topic weight map · learned vs. set</div>
                <div className="flex flex-col gap-2.5">
                  {topics.slice(0, 10).map((t) => (
                    <div key={t.topic} className="grid grid-cols-[minmax(0,140px)_minmax(0,1fr)_36px_70px] gap-3 items-center text-[13px]">
                      <span className="text-ink-para truncate">{t.topic}</span>
                      <span className="h-[5px] rounded-full bg-surface-hover relative overflow-hidden">
                        <span className="absolute inset-y-0 left-0 rounded-full bg-brand-gradient-h" style={{ width: `${t.weight * 100}%` }} />
                      </span>
                      <span className="font-mono text-[11px] text-ink-muted text-right">{t.weight.toFixed(2)}</span>
                      <span className="font-mono text-[10px] text-right" style={{ color: t.source === "behavioral" ? "#b9a6ff" : "#5d6280" }}>
                        {t.source.toUpperCase()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {insights && (
              <div className="card px-5 py-[18px] grid grid-cols-2 gap-[18px]">
                <div>
                  <div className="label-mono mb-2.5">Strong interests</div>
                  <div className="flex flex-wrap gap-1.5">
                    {insights.strong_interests.length === 0
                      ? <span className="text-xs text-ink-faint">None yet</span>
                      : insights.strong_interests.map((i) => (
                          <span key={i} className="px-2 py-1 rounded-md bg-accent-purple/[0.18] text-accent-purpleSoft text-xs border border-accent-purple/35">{i}</span>
                        ))}
                  </div>
                </div>
                <div>
                  <div className="label-mono mb-2.5">Preferred sources</div>
                  <div className="flex flex-wrap gap-1.5">
                    {insights.preferred_sources.length === 0
                      ? <span className="text-xs text-ink-faint">None yet</span>
                      : insights.preferred_sources.map((s) => (
                          <span key={s} className="px-2 py-1 rounded-md bg-accent-green/[0.14] text-emerald-300 text-xs border border-accent-green/30">{s}</span>
                        ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="flex flex-col gap-5 min-w-0">
            {reflection && (
              <div className="relative card px-5 py-[18px] overflow-hidden" style={{ background: "linear-gradient(180deg, rgba(124,92,246,.12), rgba(124,92,246,.03))" }}>
                <span className="absolute inset-y-0 left-0 w-0.5 bg-rail-gradient" />
                <div className="flex justify-between font-mono text-[10px] tracking-wide text-accent-purpleText mb-2.5">
                  <span>LATEST REFLECTION · {reflection.period.toUpperCase()}</span>
                  <span className="text-ink-faint">{shortAge(reflection.created_at)}</span>
                </div>
                <div className="flex flex-col gap-2 text-[13px] leading-relaxed text-ink-para">
                  {reflection.insights.insights.map((insight, i) => (
                    <div key={i} className="flex gap-2.5">
                      <span className="text-accent-green">✓</span>
                      {insight}
                    </div>
                  ))}
                  {reflection.recommendations?.recommended_actions?.map((action, i) => (
                    <div key={i} className="flex gap-2.5">
                      <span className="text-accent-yellow">!</span>
                      <span>
                        <b className="text-white">{action.action.replace(/_/g, " ")}:</b> {action.reason}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="card px-5 py-[18px] flex-1">
              <div className="label-mono mb-2">Adaptation events</div>
              {events.length > 0 ? (
                <div>{events.map((e) => <AgentEventRow key={e.id} event={e} />)}</div>
              ) : (
                <div className="text-center py-10">
                  <Brain className="w-8 h-8 text-ink-faint mx-auto mb-3" />
                  <p className="text-ink font-medium text-sm mb-1.5">No adaptation history yet</p>
                  <p className="text-ink-muted text-xs">Use the feed, give feedback, then run an adaptation cycle.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
