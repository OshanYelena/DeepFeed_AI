/**
 * DeepFeed AI - Auth Store
 * Manages authentication state using Zustand.
 */
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { authAPI, setAccessToken, clearAccessToken, setRefreshHandler } from "@/lib/api";

interface AuthState {
  accessToken: string | null;
  // Never sent on ordinary requests — only used to mint a new access token
  // when one expires (15 min lifetime, TDS §15.2) without forcing a full
  // re-login every time.
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  // Zustand's persist middleware reads localStorage asynchronously, so on
  // every fresh page load isAuthenticated starts false and only becomes
  // true a tick later once rehydration finishes. Pages must wait for
  // hasHydrated before treating isAuthenticated as trustworthy, or a
  // logged-in user gets bounced to /login on every refresh.
  hasHydrated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  setHasHydrated: (value: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      hasHydrated: false,

      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const tokens = await authAPI.login(email, password);
          setAccessToken(tokens.access_token);
          set({
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (err: any) {
          const msg = err?.response?.data?.detail?.error?.message ?? err?.message ?? "Login failed";
          set({ error: msg, isLoading: false });
          throw err;
        }
      },

      register: async (email, password, fullName) => {
        set({ isLoading: true, error: null });
        try {
          await authAPI.register(email, password, fullName);
          set({ isLoading: false });
        } catch (err: any) {
          const msg = err?.response?.data?.detail?.error?.message ?? err?.message ?? "Registration failed";
          set({ error: msg, isLoading: false });
          throw err;
        }
      },

      logout: () => {
        clearAccessToken();
        set({ accessToken: null, refreshToken: null, isAuthenticated: false, error: null });
      },

      clearError: () => set({ error: null }),

      setHasHydrated: (value) => set({ hasHydrated: value }),
    }),
    {
      name: "deepfeed-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.accessToken) setAccessToken(state.accessToken);
        // Fires once rehydration finishes, whether or not anything was
        // actually found in storage — that's the signal pages wait on.
        state?.setHasHydrated(true);
      },
    }
  )
);

// Wired into api.ts's response interceptor: on a 401, try this once before
// giving up. Registered here (not in api.ts) to avoid a circular import —
// api.ts exports the primitives this store already depends on.
setRefreshHandler(async () => {
  const { refreshToken, logout } = useAuthStore.getState();
  if (!refreshToken) {
    logout();
    return null;
  }
  try {
    const res = await authAPI.refresh(refreshToken);
    const newAccessToken = res.data.data.access_token;
    setAccessToken(newAccessToken);
    useAuthStore.setState({ accessToken: newAccessToken });
    return newAccessToken;
  } catch {
    // Refresh token itself is invalid/expired (30-day lifetime) — this is
    // a real re-login, not a routine expiry.
    logout();
    return null;
  }
});

/**
 * Gates a protected page until the persisted token has actually been read
 * back from storage. Redirects to /login only once hydration is done and
 * we genuinely know there's no session — never during the brief window
 * right after a page load where isAuthenticated defaults to false.
 * Returns true once it's safe to render the authenticated page.
 */
export function useRequireAuth(): boolean {
  const { isAuthenticated, hasHydrated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (hasHydrated && !isAuthenticated) router.push("/login");
  }, [hasHydrated, isAuthenticated, router]);

  return hasHydrated && isAuthenticated;
}
