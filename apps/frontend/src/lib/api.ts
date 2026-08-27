/**
 * DeepFeed AI - API Client
 * All browser requests go through Next.js /api/* rewrite proxy.
 * This avoids CORS issues and localhost/container confusion.
 */
import axios, { AxiosInstance, InternalAxiosRequestConfig } from "axios";

// Always use relative /api prefix — Next.js rewrites to backend:8000 internally
const BASE_URL = "/api";

// ── Response Types ─────────────────────────────────────────────────────────────
export interface APIResponse<T> {
  trace_id: string;
  data: T;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserProfile {
  id: string;
  user_id: string;
  expertise_level: "beginner" | "intermediate" | "advanced" | "expert";
  preferred_depth: "short" | "medium" | "deep";
  preferred_frequency: "daily" | "weekly" | "realtime";
  updated_at: string;
}

export interface Interest {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  weight: number;
  created_at: string;
}

export interface FeedItem {
  recommendation_id: string;
  title: string;
  url: string;
  source: string;
  source_type: string;
  content_type: string;
  published_at: string | null;
  final_score: number;
  relevance_score: number;
  credibility_score: number;
  freshness_score: number;
  rank_position: number;
  summary_short: string | null;
  why_recommended: string;
  matched_interests: string[];
}

export interface FeedResponse {
  items: FeedItem[];
  limit: number;
  offset: number;
}

export interface TopicPreference {
  topic: string;
  weight: number;
  confidence: number;
  source: string;
}

export interface AdaptationEvent {
  id: string;
  agent: string;
  event_type: string;
  decision: Record<string, unknown>;
  reason: string;
  confidence: number;
  created_at: string;
}

export interface ReflectionReport {
  id: string;
  period: string;
  insights: { insights: string[]; metrics_summary: Record<string, unknown> };
  recommendations: { recommended_actions: Array<{ action: string; reason: string; priority: string }> } | null;
  created_at: string;
}

// ── Client Factory ─────────────────────────────────────────────────────────────
let _accessToken: string | null = null;
// Set once by the auth store, so this module doesn't need to import it back
// (that would be circular — the store already imports setAccessToken etc.
// from here). Called on a 401 to try to silently get a new access token
// before giving up and forcing a real re-login.
let _refreshHandler: (() => Promise<string | null>) | null = null;

export function setAccessToken(token: string) { _accessToken = token; }
export function clearAccessToken() { _accessToken = null; }
export function getAccessToken() { return _accessToken; }
export function setRefreshHandler(fn: () => Promise<string | null>) { _refreshHandler = fn; }

// One shared instance (not a fresh one per call) so the interceptors below
// only need to be registered once.
const client: AxiosInstance = axios.create({ baseURL: BASE_URL, timeout: 30_000 });

client.interceptors.request.use((config) => {
  config.headers.set("Content-Type", "application/json");
  if (_accessToken) config.headers.set("Authorization", `Bearer ${_accessToken}`);
  return config;
});

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined;
    // A 15-minute access token expiring mid-session is routine, not an
    // error — access tokens are short-lived by design (TDS §15.2). Try
    // once, silently, before treating it as a real auth failure.
    if (error.response?.status === 401 && original && !original._retried && _refreshHandler) {
      original._retried = true;
      const newToken = await _refreshHandler();
      if (newToken) {
        original.headers.set("Authorization", `Bearer ${newToken}`);
        return client(original);
      }
    }
    return Promise.reject(error);
  }
);

function api(): AxiosInstance {
  return client;
}

// ── Auth API ──────────────────────────────────────────────────────────────────
export const authAPI = {
  register: (email: string, password: string, fullName?: string) =>
    api().post<APIResponse<{ user_id: string; message: string }>>("/auth/register", {
      email, password, full_name: fullName,
    }),

  login: async (email: string, password: string): Promise<AuthTokens> => {
    const res = await api().post<APIResponse<AuthTokens>>("/auth/login", { email, password });
    const tokens = res.data.data;
    setAccessToken(tokens.access_token);
    return tokens;
  },

  refresh: (refreshToken: string) =>
    api().post<APIResponse<{ access_token: string; token_type: string }>>("/auth/refresh", {
      refresh_token: refreshToken,
    }),
};

// ── Profile API ───────────────────────────────────────────────────────────────
export const profileAPI = {
  getProfile: () =>
    api().get<APIResponse<UserProfile>>("/profile/me"),

  updateProfile: (data: Partial<Pick<UserProfile, "expertise_level" | "preferred_depth" | "preferred_frequency">>) =>
    api().put<APIResponse<UserProfile>>("/profile/me", data),
};

// ── Interests API ─────────────────────────────────────────────────────────────
export const interestsAPI = {
  list: () =>
    api().get<APIResponse<Interest[]>>("/interests"),

  create: (name: string, description: string | null, weight: number) =>
    api().post<APIResponse<Interest>>("/interests", { name, description, weight }),

  update: (id: string, data: Partial<{ name: string; description: string; weight: number }>) =>
    api().put<APIResponse<Interest>>(`/interests/${id}`, data),

  delete: (id: string) =>
    api().delete(`/interests/${id}`),
};

// ── Feed API ──────────────────────────────────────────────────────────────────
export const feedAPI = {
  getFeed: (params?: { limit?: number; offset?: number; content_type?: string; min_score?: number }) =>
    api().get<APIResponse<FeedResponse>>("/feed", { params }),

  getDetail: (recommendationId: string) =>
    api().get<APIResponse<FeedItem & { summary_detailed: string; key_takeaways: unknown; topics: Array<{ name: string; confidence: number }> }>>(`/feed/${recommendationId}`),
};

// ── Feedback API ──────────────────────────────────────────────────────────────
export const feedbackAPI = {
  submit: (recommendationId: string, feedbackType: "like" | "dislike" | "bookmark" | "ignore" | "read") =>
    api().post<APIResponse<{ message: string }>>("/feedback", {
      recommendation_id: recommendationId,
      feedback_type: feedbackType,
    }),

  recordRead: (recommendationId: string, durationSeconds: number) =>
    api().post<APIResponse<{ message: string }>>("/feedback/read", {
      recommendation_id: recommendationId,
      duration_seconds: durationSeconds,
    }),
};

// ── Agent API ─────────────────────────────────────────────────────────────────
export const agentAPI = {
  getProfileInsights: () =>
    api().get<APIResponse<{ strong_interests: string[]; weak_interests: string[]; preferred_sources: string[] }>>("/agent/profile-insights"),

  getTopicPreferences: () =>
    api().get<APIResponse<{ topics: TopicPreference[] }>>("/agent/topic-preferences"),

  correctPreference: (topic: string, newWeight: number) =>
    api().post<APIResponse<{ message: string }>>("/agent/preferences/correct", {
      topic, correction: "user_manual_correction", new_weight: newWeight,
    }),

  generateSearchPlan: () =>
    api().post<APIResponse<{ search_plan_id: string; queries: string[]; sources: string[] }>>("/agent/search-plan/generate"),

  runAdaptation: () =>
    api().post<APIResponse<{ status: string; summary: Record<string, unknown> }>>("/agent/adapt/run", { mode: "full" }),

  getAdaptationEvents: () =>
    api().get<APIResponse<{ events: AdaptationEvent[] }>>("/agent/adaptation-events"),

  runReflection: () =>
    api().post<APIResponse<{ report_id: string; status: string }>>("/agent/reflection/run"),

  getLatestReflection: () =>
    api().get<APIResponse<ReflectionReport>>("/agent/reflection/latest"),
};

// ── Content Discovery API ("Discover Now" button) ──────────────────────────────
export interface DiscoveryRun {
  id: string;
  task_id: string;
  status: "pending" | "running" | "completed" | "failed";
  trigger_type: string;
  new_items_count: number | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface DiscoveryStatus {
  daily: { used: number; limit: number; remaining: number; reset_at: string | null };
  cooldown_seconds_remaining: number;
  next_scheduled_at: string | null;
  last_run: DiscoveryRun | null;
  active_run: DiscoveryRun | null;
}

// The backend returns 200 with either {data: ...} or {error: {code, message}}
// for this endpoint's expected failure modes (quota/cooldown/no-plan) rather
// than an HTTP error status, so callers must check for `error` themselves.
export interface DiscoveryEnvelope<T> {
  trace_id: string;
  data?: T;
  error?: { code: string; message: string; details?: Record<string, unknown> };
}

export const contentAPI = {
  getStatus: () =>
    api().get<DiscoveryEnvelope<DiscoveryStatus>>("/content/discover/status"),

  // Runs discovery -> processing -> ranking synchronously on the backend
  // (no Celery involved — see DiscoveryTriggerService's docstring for why),
  // so this call blocks until the whole pipeline is actually done. Give it
  // a long timeout instead of the client's normal 30s default.
  discover: () =>
    api().post<
      DiscoveryEnvelope<{
        run_id: string;
        task_id: string;
        status: "completed" | "failed";
        new_items_count: number | null;
        error_message: string | null;
        queries: string[];
      }>
    >("/content/discover", undefined, { timeout: 300_000 }),

  getRun: (runId: string) =>
    api().get<DiscoveryEnvelope<DiscoveryRun>>(`/content/discover/runs/${runId}`),
};

// ── Health API ────────────────────────────────────────────────────────────────
export const healthAPI = {
  check: () => api().get<APIResponse<{ status: string }>>("/health"),
  ready: () => api().get<APIResponse<{ status: string; checks: Record<string, string> }>>("/health/ready"),
};
