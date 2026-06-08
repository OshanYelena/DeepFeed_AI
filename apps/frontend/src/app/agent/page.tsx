"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { agentAPI, type AdaptationEvent } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { useRouter } from "next/navigation";
import { ArrowLeft, Brain, Sparkles, RefreshCw, Target, Activity, AlertCircle, CheckCircle } from "lucide-react";
import toast from "react-hot-toast";

function AgentEventRow({ event }: { event: AdaptationEvent }) {
  const colorMap: Record<string, string> = {
    topic_weight_update: "text-yellow-400",
    search_plan_generated: "text-blue-400",
    full_cycle_completed: "text-emerald-400",
    reflection_completed: "text-purple-400",
  };
  const color = colorMap[event.event_type] ?? "text-slate-400";

  return (
    <div className="flex items-start gap-3 py-3 border-b border-surface-border last:border-0">
      <Activity className={`w-4 h-4 mt-0.5 shrink-0 ${color}`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-xs font-medium text-slate-300">{event.agent}</span>
          <span className={`text-xs ${color}`}>{event.event_type.replace(/_/g, " ")}</span>
          <span className="ml-auto text-xs text-slate-600">
            {Math.round(event.confidence * 100)}% confidence
          </span>
        </div>
        <p className="text-xs text-slate-500 line-clamp-2">{event.reason}</p>
      </div>
    </div>
  );
}

export default function AgentPage() {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  const { data: insightsData, isLoading: insightsLoading } = useQuery({
    queryKey: ["agent-insights"],
    queryFn: () => agentAPI.getProfileInsights(),
    enabled: isAuthenticated,
  });

  const { data: topicsData } = useQuery({
    queryKey: ["agent-topics"],
    queryFn: () => agentAPI.getTopicPreferences(),
    enabled: isAuthenticated,
  });

  const { data: eventsData } = useQuery({
    queryKey: ["agent-events"],
    queryFn: () => agentAPI.getAdaptationEvents(),
    enabled: isAuthenticated,
  });

  const { data: reflectionData } = useQuery({
    queryKey: ["agent-reflection"],
    queryFn: () => agentAPI.getLatestReflection(),
    enabled: isAuthenticated,
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

  const insights = insightsData?.data.data;
  const topics = topicsData?.data.data?.topics ?? [];
  const events = eventsData?.data.data?.events ?? [];
  const reflection = reflectionData?.data.data;

  if (!isAuthenticated) { router.push("/login"); return null; }

  return (
    <div className="min-h-screen bg-surface">
      <nav className="sticky top-0 z-40 bg-surface/80 backdrop-blur-sm border-b border-surface-border">
        <div className="max-w-2xl mx-auto px-4 h-14 flex items-center gap-3">
          <button onClick={() => router.push("/feed")} className="btn-ghost p-2">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <Brain className="w-5 h-5 text-brand-400" />
          <h1 className="font-semibold text-white">Agent Insights</h1>
        </div>
      </nav>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-5">
        {/* Action buttons */}
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => runAdaptation.mutate()}
            disabled={runAdaptation.isPending}
            className="btn-primary text-xs flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${runAdaptation.isPending ? "animate-spin" : ""}`} />
            Run Adaptation
          </button>
          <button
            onClick={() => generatePlan.mutate()}
            disabled={generatePlan.isPending}
            className="btn-ghost text-xs flex items-center gap-1.5 border border-surface-border"
          >
            <Target className="w-3.5 h-3.5" />
            Generate Search Plan
          </button>
          <button
            onClick={() => runReflection.mutate()}
            disabled={runReflection.isPending}
            className="btn-ghost text-xs flex items-center gap-1.5 border border-surface-border"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Run Reflection
          </button>
        </div>

        {/* Profile Insights */}
        {insights && (
          <section className="card p-5">
            <h2 className="font-semibold text-white mb-3 flex items-center gap-2">
              <Brain className="w-4 h-4 text-brand-400" /> Learned Profile
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-slate-500 mb-2">Strong interests</p>
                <div className="flex flex-wrap gap-1.5">
                  {insights.strong_interests.length === 0
                    ? <span className="text-xs text-slate-600">None yet</span>
                    : insights.strong_interests.map((i) => (
                        <span key={i} className="badge bg-brand-900/40 text-brand-300 border border-brand-800">{i}</span>
                      ))
                  }
                </div>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-2">Preferred sources</p>
                <div className="flex flex-wrap gap-1.5">
                  {insights.preferred_sources.length === 0
                    ? <span className="text-xs text-slate-600">None yet</span>
                    : insights.preferred_sources.map((s) => (
                        <span key={s} className="badge bg-emerald-900/40 text-emerald-300 border border-emerald-800">{s}</span>
                      ))
                  }
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Topic Preferences */}
        {topics.length > 0 && (
          <section className="card p-5">
            <h2 className="font-semibold text-white mb-3">Topic Weight Map</h2>
            <div className="space-y-2">
              {topics.slice(0, 10).map((topic) => (
                <div key={topic.topic} className="flex items-center gap-3">
                  <span className="text-sm text-slate-300 w-40 truncate">{topic.topic}</span>
                  <div className="flex-1 score-bar">
                    <div
                      className="score-fill"
                      style={{
                        width: `${topic.weight * 100}%`,
                        background: `hsl(${topic.weight * 120}, 70%, 50%)`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-slate-500 w-8 text-right">{(topic.weight * 100).toFixed(0)}%</span>
                  <span className="badge bg-slate-800 text-slate-500 border border-slate-700 text-xs">{topic.source}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Latest Reflection */}
        {reflection && (
          <section className="card p-5">
            <h2 className="font-semibold text-white mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" /> Latest Reflection ({reflection.period})
            </h2>
            <div className="space-y-2">
              {reflection.insights.insights.map((insight, i) => (
                <div key={i} className="flex items-start gap-2">
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                  <p className="text-sm text-slate-300">{insight}</p>
                </div>
              ))}
            </div>
            {reflection.recommendations?.recommended_actions && reflection.recommendations.recommended_actions.length > 0 && (
              <div className="mt-4 pt-3 border-t border-surface-border">
                <p className="text-xs text-slate-500 mb-2">Recommended actions</p>
                {reflection.recommendations.recommended_actions.map((action, i) => (
                  <div key={i} className="flex items-start gap-2 mb-2">
                    <AlertCircle className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${
                      action.priority === "high" ? "text-red-400" : action.priority === "medium" ? "text-yellow-400" : "text-slate-400"
                    }`} />
                    <div>
                      <span className="text-xs font-medium text-slate-300">{action.action.replace(/_/g, " ")}</span>
                      <p className="text-xs text-slate-500">{action.reason}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* Adaptation Events */}
        {events.length > 0 && (
          <section className="card p-5">
            <h2 className="font-semibold text-white mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-400" /> Recent Adaptations
            </h2>
            <div>
              {events.map((event) => (
                <AgentEventRow key={event.id} event={event} />
              ))}
            </div>
          </section>
        )}

        {events.length === 0 && !insightsLoading && (
          <div className="card p-8 text-center">
            <Brain className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <p className="text-white font-medium mb-2">No adaptation history yet</p>
            <p className="text-slate-400 text-sm">
              Use the feed, provide feedback, then run an adaptation cycle to see the agent at work.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
