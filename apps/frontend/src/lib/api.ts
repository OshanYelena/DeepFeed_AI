/**
 * DeepFeed AI - API Client
 * All browser requests go through Next.js /api/* rewrite proxy.
 * This avoids CORS issues and localhost/container confusion.
 */
import axios, { AxiosInstance } from "axios";

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

export function setAccessToken(token: string) { _accessToken = token; }
export function clearAccessToken() { _accessToken = null; }
export function getAccessToken() { return _accessToken; }

function api(): AxiosInstance {
  return axios.create({
    baseURL: BASE_URL,
    headers: {
      "Content-Type": "application/json",
      ...(_accessToken ? { Authorization: `Bearer ${_accessToken}` } : {}),
    },
    timeout: 30_000,
  });
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

// ── Health API ────────────────────────────────────────────────────────────────
export const healthAPI = {
  check: () => api().get<APIResponse<{ status: string }>>("/health"),
  ready: () => api().get<APIResponse<{ status: string; checks: Record<string, string> }>>("/health/ready"),
};
