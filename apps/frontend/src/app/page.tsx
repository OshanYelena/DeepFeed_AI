"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";

export default function HomePage() {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    router.replace(isAuthenticated ? "/feed" : "/login");
  }, [isAuthenticated, router]);

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center">
      <div className="animate-pulse-slow flex flex-col items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-brand-500" />
        <p className="text-slate-500 text-sm">Loading DeepFeed AI...</p>
      </div>
    </div>
  );
}
