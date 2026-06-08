"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/auth-store";
import toast from "react-hot-toast";

export default function RegisterPage() {
  const { register, login, isLoading, error, clearError } = useAuthStore();
  const router = useRouter();
  const [form, setForm] = useState({ fullName: "", email: "", password: "", confirmPassword: "" });
  const [localError, setLocalError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setLocalError("");

    if (form.password !== form.confirmPassword) {
      setLocalError("Passwords do not match");
      return;
    }
    if (form.password.length < 12) {
      setLocalError("Password must be at least 12 characters");
      return;
    }

    try {
      await register(form.email, form.password, form.fullName || undefined);
      await login(form.email, form.password);
      toast.success("Account created! Welcome to DeepFeed AI.");
      router.push("/onboarding");
    } catch {
      // error handled in store
    }
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4">
      <div className="w-full max-w-md animate-fade-in">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">D</span>
            </div>
            <span className="text-xl font-bold text-white">DeepFeed AI</span>
          </div>
          <p className="text-slate-400 text-sm">Start discovering relevant knowledge.</p>
        </div>

        <div className="card p-6">
          <h1 className="text-lg font-semibold text-white mb-6">Create your account</h1>

          {(error || localError) && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-300 text-sm">
              {localError || error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Full name (optional)</label>
              <input
                type="text"
                className="input"
                placeholder="Ada Lovelace"
                value={form.fullName}
                onChange={(e) => setForm((f) => ({ ...f, fullName: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
              <input
                type="email"
                className="input"
                placeholder="you@example.com"
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Password <span className="text-slate-500 font-normal">(min 12 chars)</span>
              </label>
              <input
                type="password"
                className="input"
                placeholder="••••••••••••"
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Confirm password</label>
              <input
                type="password"
                className="input"
                placeholder="••••••••••••"
                value={form.confirmPassword}
                onChange={(e) => setForm((f) => ({ ...f, confirmPassword: e.target.value }))}
                required
              />
            </div>
            <button type="submit" className="btn-primary w-full" disabled={isLoading}>
              {isLoading ? "Creating account..." : "Create account"}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-slate-400">
            Already have an account?{" "}
            <Link href="/login" className="text-brand-500 hover:text-brand-400 transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
