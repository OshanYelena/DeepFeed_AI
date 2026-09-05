"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { interestsAPI, profileAPI } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth-store";
import { Logo } from "@/components/Logo";
import { Segmented } from "@/components/Segmented";
import { Check, ChevronRight, Plus } from "lucide-react";
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
];

const EXPERTISE_OPTIONS = ["Beginner", "Intermediate", "Advanced", "Expert"];
const DEPTH_OPTIONS = ["Short", "Medium", "Deep"];
const FREQUENCY_OPTIONS = ["Daily", "Weekly", "Real-time"];

export default function OnboardingPage() {
  const ready = useRequireAuth();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [customInterests, setCustomInterests] = useState<{ name: string; description: string; weight: number }[]>([]);
  const [addingCustom, setAddingCustom] = useState(false);
  const [customName, setCustomName] = useState("");
  const [expertise, setExpertise] = useState("Advanced");
  const [depth, setDepth] = useState("Deep");
  const [frequency, setFrequency] = useState("Daily");

  const allInterests = [...SUGGESTED_INTERESTS, ...customInterests];

  const createInterests = useMutation({
    mutationFn: async () => {
      const chosen = allInterests.filter((i) => selected.has(i.name));
      for (const interest of chosen) {
        await interestsAPI.create(interest.name, interest.description || null, interest.weight);
      }
      await profileAPI.updateProfile({
        expertise_level: expertise.toLowerCase() as any,
        preferred_depth: depth.toLowerCase() as any,
        preferred_frequency: frequency.toLowerCase().replace("-", "") as any,
      });
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

  const addCustom = () => {
    const name = customName.trim();
    if (!name) return;
    setCustomInterests((prev) => [...prev, { name, description: "", weight: 0.7 }]);
    setSelected((prev) => new Set(prev).add(name));
    setCustomName("");
    setAddingCustom(false);
  };

  if (!ready) return null;

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_560px] bg-surface font-sans">
      <div
        className="hidden lg:flex flex-col justify-between p-14 border-r border-white/[0.08]"
        style={{
          background: "radial-gradient(ellipse at 20% 30%, rgba(124,92,246,.18), transparent 55%), #0a0c1a",
        }}
      >
        <div className="flex items-center gap-2.5">
          <Logo size={28} />
          <span className="font-bold text-[15px] text-white">
            DeepFeed{" "}
            <span className="bg-gradient-to-r from-accent-pink to-accent-blue bg-clip-text text-transparent">AI</span>
          </span>
        </div>
        <div>
          <div className="font-serif text-[44px] leading-[1.1] tracking-tight text-ink max-w-[520px]">
            Less searching.
            <br />
            More signal.
          </div>
          <p className="mt-[18px] text-[15px] leading-[1.55] text-ink-muted max-w-[440px]">
            Pick your interests, tell us how deep you like to go, and the research agent starts pulling papers,
            articles and posts that match — with a reason attached to each one.
          </p>
        </div>
        <div className="font-mono text-[11px] text-ink-faint">STEP {step} OF 2 · {step === 1 ? "INTERESTS" : "PREFERENCES"}</div>
      </div>

      <div className="p-8 lg:p-14 flex flex-col gap-[22px] overflow-y-auto">
        <div className="flex gap-1.5">
          {[1, 2].map((s) => (
            <span
              key={s}
              className="flex-1 h-[3px] rounded-full"
              style={{
                background: s <= step ? "linear-gradient(90deg, #d946ef, #7c5cf6)" : "#1c2040",
              }}
            />
          ))}
        </div>

        {step === 1 && (
          <>
            <div>
              <h1 className="font-serif text-[26px] leading-tight text-ink m-0">What are you interested in?</h1>
              <div className="mt-1.5 text-[13.5px] text-ink-dim">
                Pick a few. You can add your own and adjust weights later.
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {allInterests.map((interest) => {
                const on = selected.has(interest.name);
                return (
                  <button
                    key={interest.name}
                    type="button"
                    onClick={() => toggle(interest.name)}
                    className={`text-left px-[13px] py-[11px] rounded-[10px] border flex justify-between gap-2 transition-colors ${
                      on ? "border-accent-purple/80 bg-accent-purple/[0.18]" : "border-white/10 bg-surface-card hover:border-white/20"
                    }`}
                  >
                    <div className="min-w-0">
                      <div className={`text-[13.5px] font-semibold ${on ? "text-white" : "text-ink-para"}`}>{interest.name}</div>
                      {interest.description && (
                        <div className="text-[11.5px] text-ink-soft mt-0.5 truncate">{interest.description}</div>
                      )}
                    </div>
                    {on && <Check className="w-3.5 h-3.5 text-accent-purpleText shrink-0 mt-0.5" />}
                  </button>
                );
              })}
            </div>

            {addingCustom ? (
              <div className="flex gap-2">
                <input
                  autoFocus
                  className="input text-sm"
                  placeholder='e.g. "speculative decoding"'
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && addCustom()}
                />
                <button onClick={addCustom} className="btn-outline shrink-0">Add</button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setAddingCustom(true)}
                className="px-[13px] py-[11px] rounded-[10px] border border-dashed border-white/[0.16] text-[13px] text-ink-faint text-left flex items-center gap-1.5 hover:text-ink-dim hover:border-white/30 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" /> Something else, e.g. &quot;speculative decoding&quot;
              </button>
            )}

            <button
              onClick={() => setStep(2)}
              disabled={selected.size === 0}
              className="mt-auto p-3.5 rounded-[10px] bg-white text-surface text-center font-bold text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
            >
              Continue · {selected.size} selected <ChevronRight className="w-4 h-4" />
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <div>
              <h1 className="font-serif text-[26px] leading-tight text-ink m-0">How do you like to read?</h1>
              <div className="mt-1.5 text-[13.5px] text-ink-dim">
                This calibrates content depth, technical level and how often we look for new items.
              </div>
            </div>

            <div className="card p-5 flex flex-col gap-5">
              <div>
                <div className="text-[12.5px] text-ink-muted mb-2">Expertise level</div>
                <Segmented options={EXPERTISE_OPTIONS} value={expertise} onChange={setExpertise} />
              </div>
              <div>
                <div className="text-[12.5px] text-ink-muted mb-2">Content depth</div>
                <Segmented options={DEPTH_OPTIONS} value={depth} onChange={setDepth} />
              </div>
              <div>
                <div className="text-[12.5px] text-ink-muted mb-2">Frequency</div>
                <Segmented options={FREQUENCY_OPTIONS} value={frequency} onChange={setFrequency} />
              </div>
            </div>

            <div className="mt-auto flex gap-3">
              <button onClick={() => setStep(1)} className="btn-outline flex-1">Back</button>
              <button
                onClick={() => createInterests.mutate()}
                disabled={createInterests.isPending}
                className="btn-primary flex-1"
              >
                {createInterests.isPending ? "Setting up…" : "Start discovering"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
