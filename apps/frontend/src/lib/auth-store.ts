/**
 * DeepFeed AI - Auth Store
 * Manages authentication state using Zustand.
 */
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { authAPI, setAccessToken, clearAccessToken } from "@/lib/api";

interface AuthState {
  accessToken: string | null;
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
      isAuthenticated: false,
      isLoading: false,
      error: null,
      hasHydrated: false,

      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const tokens = await authAPI.login(email, password);
          setAccessToken(tokens.access_token);
          set({ accessToken: tokens.access_token, isAuthenticated: true, isLoading: false });
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
        set({ accessToken: null, isAuthenticated: false, error: null });
      },

      clearError: () => set({ error: null }),

      setHasHydrated: (value) => set({ hasHydrated: value }),
    }),
    {
      name: "deepfeed-auth",
      partialize: (state) => ({ accessToken: state.accessToken, isAuthenticated: state.isAuthenticated }),
      onRehydrateStorage: () => (state) => {
        if (state?.accessToken) setAccessToken(state.accessToken);
        // Fires once rehydration finishes, whether or not anything was
        // actually found in storage — that's the signal pages wait on.
        state?.setHasHydrated(true);
      },
    }
  )
);

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
