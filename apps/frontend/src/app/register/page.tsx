"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/auth-store";
import { Logo } from "@/components/Logo";
import { Eye, EyeOff } from "lucide-react";
import toast from "react-hot-toast";

export default function RegisterPage() {
  const { register, login, isLoading, error, clearError } = useAuthStore();
  const router = useRouter();
  const [form, setForm] = useState({ fullName: "", email: "", password: "", confirmPassword: "" });
  const [localError, setLocalError] = useState("");
  const [showPassword, setShowPassword] = useState(false);

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
    if (!/[A-Z]/.test(form.password) || !/[a-z]/.test(form.password) || !/\d/.test(form.password)) {
      setLocalError("Password needs an uppercase letter, a lowercase letter, and a digit");
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
          <div className="font-serif text-[26px] leading-tight text-ink">Create your account</div>
          <div className="text-[13.5px] text-ink-dim">Start discovering relevant knowledge.</div>
        </div>

        {(error || localError) && (
          <div className="px-3.5 py-3 bg-red-900/30 border border-red-800 rounded-lg text-red-300 text-sm">
            {localError || error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-2.5">
          <input
            type="text"
            className="input"
            placeholder="Full name (optional)"
            value={form.fullName}
            onChange={(e) => setForm((f) => ({ ...f, fullName: e.target.value }))}
          />
          <input
            type="email"
            className="input"
            placeholder="you@example.com"
            value={form.email}
            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            required
          />
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              className="input pr-16"
              placeholder="Password (12+ chars, Aa1)"
              value={form.password}
              onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
              required
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
          <input
            type={showPassword ? "text" : "password"}
            className="input"
            placeholder="Confirm password"
            value={form.confirmPassword}
            onChange={(e) => setForm((f) => ({ ...f, confirmPassword: e.target.value }))}
            required
          />
          <button type="submit" className="btn-primary w-full mt-1" disabled={isLoading}>
            {isLoading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="text-center text-[12.5px] text-ink-dim">
          Already have an account?{" "}
          <Link href="/login" className="text-accent-purpleText font-semibold hover:text-white transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
