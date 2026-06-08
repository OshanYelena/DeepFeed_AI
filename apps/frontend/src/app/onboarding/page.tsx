"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { interestsAPI, profileAPI } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { Check, ChevronRight } from "lucide-react";
import toast from "react-hot-toast";

const SUGGESTED_INTERESTS = [
  { name: "AI Agents", description: "Agentic AI, LLM orchestration, multi-agent systems", weight: 0.9 },
  { name: "Large Language Models", description: "LLMs, transformers, foundation models", weight: 0.85 },
  { name: "Machine Learning", description: "ML research, algorithms, training techniques", weight: 0.8 },
  { name: "Deep Learning", description: "Neural networks, architectures, training", weight: 0.75 },
  { name: "Reinforcement Learning", description: "RL algorithms, RLHF, reward modeling", weight: 0.75 },
  { name: "Software Architecture", description: "System design, distributed systems, patterns", weight: 0.7 },
  { name: "Natural Language Processing", description: "NLP tasks, text understanding, generation", weight: 0.8 },
  { name: "Computer Vision", description: "Image models, vision transformers, multimodal", weight: 0.7 },
  { name: "MLOps", description: "ML infrastructure, deployment, monitoring", weight: 0.65 },
  { name: "Research Papers", description: "Academic publications, arXiv, preprints", weight: 0.8 },
  { name: "Cloud Computing", description: "AWS, GCP, Azure, cloud-native patterns", weight: 0.6 },
  { name: "Open Source", description: "OSS projects, contributions, tools", weight: 0.6 },
];

const EXPERTISE_OPTIONS = [
  { value: "beginner", label: "Beginner", desc: "New to AI/ML" },
  { value: "intermediate", label: "Intermediate", desc: "Some experience" },
  { value: "advanced", label: "Advanced", desc: "Deep practitioner" },
  { value: "expert", label: "Expert", desc: "Researcher/Lead" },
];

export default function OnboardingPage() {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [expertise, setExpertise] = useState("intermediate");

  const createInterests = useMutation({
    mutationFn: async () => {
      const chosen = SUGGESTED_INTERESTS.filter((i) => selected.has(i.name));
      for (const interest of chosen) {
        await interestsAPI.create(interest.name, interest.description, interest.weight);
      }
      await profileAPI.updateProfile({ expertise_level: expertise as any });
    },
    onSuccess: () => {
      toast.success("Profile set up! Your feed is being personalized.");
      router.push("/feed");
    },
    onError: () => toast.error("Setup failed, please try again"),
  });

  const toggle = (name: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  };

  if (!isAuthenticated) { router.push("/login"); return null; }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4">
      <div className="w-full max-w-xl animate-fade-in">
        {/* Progress */}
        <div className="flex items-center gap-2 mb-8">
          {[1, 2].map((s) => (
            <div
              key={s}
              className={`h-1 flex-1 rounded-full transition-colors ${
                s <= step ? "bg-brand-500" : "bg-surface-hover"
              }`}
            />
          ))}
        </div>

        {step === 1 && (
          <div>
            <h1 className="text-2xl font-bold text-white mb-2">What are you interested in?</h1>
            <p className="text-slate-400 mb-6">Select topics to personalize your feed. You can always add more later.</p>
            <div className="grid grid-cols-2 gap-2 mb-6">
              {SUGGESTED_INTERESTS.map((interest) => (
                <button
                  key={interest.name}
                  onClick={() => toggle(interest.name)}
                  className={`text-left p-3 rounded-lg border transition-colors ${
                    selected.has(interest.name)
                      ? "bg-brand-900/40 border-brand-600 text-white"
                      : "card hover:border-slate-600 text-slate-300"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-sm font-medium">{interest.name}</div>
                      <div className="text-xs text-slate-500 mt-0.5 line-clamp-1">{interest.description}</div>
                    </div>
                    {selected.has(interest.name) && (
                      <Check className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
                    )}
                  </div>
                </button>
              ))}
            </div>
            <button
              onClick={() => setStep(2)}
              disabled={selected.size === 0}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              Continue ({selected.size} selected) <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {step === 2 && (
          <div>
            <h1 className="text-2xl font-bold text-white mb-2">Your expertise level</h1>
            <p className="text-slate-400 mb-6">This helps us calibrate content depth and technical complexity.</p>
            <div className="space-y-3 mb-6">
              {EXPERTISE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setExpertise(opt.value)}
                  className={`w-full text-left p-4 rounded-lg border transition-colors ${
                    expertise === opt.value
                      ? "bg-brand-900/40 border-brand-600"
                      : "card hover:border-slate-600"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-white">{opt.label}</div>
                      <div className="text-sm text-slate-500">{opt.desc}</div>
                    </div>
                    {expertise === opt.value && <Check className="w-5 h-5 text-brand-400" />}
                  </div>
                </button>
              ))}
            </div>
            <div className="flex gap-3">
              <button onClick={() => setStep(1)} className="btn-ghost border border-surface-border flex-1">
                Back
              </button>
              <button
                onClick={() => createInterests.mutate()}
                disabled={createInterests.isPending}
                className="btn-primary flex-1"
              >
                {createInterests.isPending ? "Setting up..." : "Start discovering"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
