/**
 * DeepFeed AI - Auth Store
 * Manages authentication state using Zustand.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { authAPI, setAccessToken, clearAccessToken } from "@/lib/api";

interface AuthState {
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

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
    }),
    {
      name: "deepfeed-auth",
      partialize: (state) => ({ accessToken: state.accessToken, isAuthenticated: state.isAuthenticated }),
      onRehydrateStorage: () => (state) => {
        if (state?.accessToken) setAccessToken(state.accessToken);
      },
    }
  )
);
