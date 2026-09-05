"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/auth-store";
import { Logo } from "@/components/Logo";
import { Eye, EyeOff } from "lucide-react";
import toast from "react-hot-toast";

export default function LoginPage() {
  const { login, isLoading, error, clearError } = useAuthStore();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

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
    <div
      className="min-h-screen flex items-center justify-center px-4 font-sans"
      style={{
        background:
          "radial-gradient(ellipse at 50% 110%, rgba(124,92,246,.22), transparent 60%), #0a0c1a",
      }}
    >
      <div className="w-full max-w-[380px] flex flex-col gap-[22px] animate-fade-in">
        <div className="flex flex-col items-center gap-3.5">
          <Logo size={56} />
          <div className="font-serif text-[26px] leading-tight text-ink">Welcome back</div>
          <div className="text-[13.5px] text-ink-dim">Your brief is waiting.</div>
        </div>

        {error && (
          <div className="px-3.5 py-3 bg-red-900/30 border border-red-800 rounded-lg text-red-300 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-2.5">
          <input
            type="email"
            className="input"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              className="input pr-16"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-ink-dim hover:text-ink flex items-center gap-1"
            >
              {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
          <button type="submit" className="btn-primary w-full mt-1" disabled={isLoading}>
            {isLoading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <div className="flex items-center justify-between text-[12.5px] text-ink-dim">
          <span className="cursor-default">Forgot password?</span>
          <span>
            New here?{" "}
            <Link href="/register" className="text-accent-purpleText font-semibold hover:text-white transition-colors">
              Create account
            </Link>
          </span>
        </div>
      </div>
    </div>
  );
}
