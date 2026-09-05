/**
 * DeepFeed AI - Library Store
 *
 * The backend has no endpoints for a saved-items list, semantic search, or
 * settings persistence (see /saved, /search, /settings in the design —
 * they're new pages the product doesn't have a backend for yet). Rather than
 * inventing fake server state, this store keeps that per-browser bookkeeping
 * (which recommendations are bookmarked/liked locally, and recent search
 * queries) in localStorage so the new pages have something real to read.
 *
 * Feedback is still always submitted to the real backend via feedbackAPI —
 * this only tracks *which ids* to show back to the user client-side.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface LibraryState {
  bookmarks: Record<string, string>; // recommendation_id -> ISO timestamp saved
  liked: Record<string, true>;
  recentSearches: string[];
  setBookmarked: (id: string, bookmarked: boolean) => void;
  setLiked: (id: string, liked: boolean) => void;
  addRecentSearch: (query: string) => void;
}

export const useLibraryStore = create<LibraryState>()(
  persist(
    (set) => ({
      bookmarks: {},
      liked: {},
      recentSearches: [],

      setBookmarked: (id, bookmarked) =>
        set((state) => {
          const next = { ...state.bookmarks };
          if (bookmarked) next[id] = new Date().toISOString();
          else delete next[id];
          return { bookmarks: next };
        }),

      setLiked: (id, liked) =>
        set((state) => {
          const next = { ...state.liked };
          if (liked) next[id] = true;
          else delete next[id];
          return { liked: next };
        }),

      addRecentSearch: (query) =>
        set((state) => {
          const trimmed = query.trim();
          if (!trimmed) return state;
          const deduped = [trimmed, ...state.recentSearches.filter((q) => q !== trimmed)];
          return { recentSearches: deduped.slice(0, 5) };
        }),
    }),
    { name: "deepfeed-library" }
  )
);
