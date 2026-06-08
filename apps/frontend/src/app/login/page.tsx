"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/auth-store";
import toast from "react-hot-toast";

export default function LoginPage() {
  const { login, isLoading, error, clearError } = useAuthStore();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      await login(email, password);
      toast.success("Welcome back!");
      router.push("/feed");
    } catch {
      // error is set in store
    }
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4">
      <div className="w-full max-w-md animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">D</span>
            </div>
            <span className="text-xl font-bold text-white">DeepFeed AI</span>
          </div>
          <p className="text-slate-400 text-sm">Discover signal. Ignore noise.</p>
        </div>

        <div className="card p-6">
          <h1 className="text-lg font-semibold text-white mb-6">Sign in to your account</h1>

          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-300 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
              <input
                type="email"
                className="input"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
              <input
                type="password"
                className="input"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
            <button type="submit" className="btn-primary w-full" disabled={isLoading}>
              {isLoading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-slate-400">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="text-brand-500 hover:text-brand-400 transition-colors">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
