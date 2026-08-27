"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { profileAPI, interestsAPI, type Interest } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth-store";
import { useRouter } from "next/navigation";
import { Plus, Trash2, ArrowLeft, Save } from "lucide-react";
import toast from "react-hot-toast";

function InterestCard({ interest, onDelete, onUpdate }: {
  interest: Interest;
  onDelete: (id: string) => void;
  onUpdate: (id: string, weight: number) => void;
}) {
  return (
    <div className="card p-4 flex items-center gap-3">
      <div className="flex-1">
        <div className="font-medium text-white text-sm">{interest.name}</div>
        {interest.description && (
          <div className="text-xs text-slate-500 mt-0.5 line-clamp-1">{interest.description}</div>
        )}
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-500">Weight</span>
        <input
          type="range"
          min="0" max="1" step="0.1"
          value={interest.weight}
          onChange={(e) => onUpdate(interest.id, parseFloat(e.target.value))}
          className="w-20 accent-brand-500"
        />
        <span className="text-xs text-brand-400 w-6 text-right">{interest.weight.toFixed(1)}</span>
        <button
          onClick={() => onDelete(interest.id)}
          className="btn-ghost p-1.5 text-slate-500 hover:text-red-400"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const ready = useRequireAuth();
  const router = useRouter();
  const qc = useQueryClient();
  const [newInterest, setNewInterest] = useState({ name: "", description: "", weight: 0.7 });
  const [showAddForm, setShowAddForm] = useState(false);

  const { data: profileData } = useQuery({
    queryKey: ["profile"],
    queryFn: () => profileAPI.getProfile(),
    enabled: ready,
  });

  const { data: interestsData } = useQuery({
    queryKey: ["interests"],
    queryFn: () => interestsAPI.list(),
    enabled: ready,
  });

  const profile = profileData?.data.data;
  const interests = interestsData?.data.data ?? [];

  const updateProfile = useMutation({
    mutationFn: (data: Parameters<typeof profileAPI.updateProfile>[0]) =>
      profileAPI.updateProfile(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["profile"] });
      toast.success("Profile updated");
    },
  });

  const createInterest = useMutation({
    mutationFn: () =>
      interestsAPI.create(newInterest.name, newInterest.description || null, newInterest.weight),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["interests"] });
      setNewInterest({ name: "", description: "", weight: 0.7 });
      setShowAddForm(false);
      toast.success("Interest added");
    },
    onError: () => toast.error("Failed to add interest"),
  });

  const deleteInterest = useMutation({
    mutationFn: (id: string) => interestsAPI.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["interests"] });
      toast.success("Interest removed");
    },
  });

  const updateInterest = useMutation({
    mutationFn: ({ id, weight }: { id: string; weight: number }) =>
      interestsAPI.update(id, { weight }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["interests"] }),
  });

  if (!ready) return null;

  return (
    <div className="min-h-screen bg-surface">
      <nav className="sticky top-0 z-40 bg-surface/80 backdrop-blur-sm border-b border-surface-border">
        <div className="max-w-2xl mx-auto px-4 h-14 flex items-center gap-3">
          <button onClick={() => router.push("/feed")} className="btn-ghost p-2">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <h1 className="font-semibold text-white">Profile & Interests</h1>
        </div>
      </nav>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* Preferences */}
        {profile && (
          <section className="card p-5">
            <h2 className="font-semibold text-white mb-4">Reading Preferences</h2>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1.5">Expertise level</label>
                <select
                  className="input text-sm"
                  value={profile.expertise_level}
                  onChange={(e) => updateProfile.mutate({ expertise_level: e.target.value as any })}
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                  <option value="expert">Expert</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1.5">Content depth</label>
                <select
                  className="input text-sm"
                  value={profile.preferred_depth}
                  onChange={(e) => updateProfile.mutate({ preferred_depth: e.target.value as any })}
                >
                  <option value="short">Short</option>
                  <option value="medium">Medium</option>
                  <option value="deep">Deep</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1.5">Frequency</label>
                <select
                  className="input text-sm"
                  value={profile.preferred_frequency}
                  onChange={(e) => updateProfile.mutate({ preferred_frequency: e.target.value as any })}
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="realtime">Real-time</option>
                </select>
              </div>
            </div>
          </section>
        )}

        {/* Interests */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-white">Interests</h2>
            <button onClick={() => setShowAddForm(!showAddForm)} className="btn-primary text-xs flex items-center gap-1.5">
              <Plus className="w-3.5 h-3.5" /> Add interest
            </button>
          </div>

          {showAddForm && (
            <div className="card p-4 mb-3 space-y-3 animate-slide-up">
              <input
                className="input text-sm"
                placeholder="Interest name (e.g. AI Agents)"
                value={newInterest.name}
                onChange={(e) => setNewInterest((f) => ({ ...f, name: e.target.value }))}
              />
              <input
                className="input text-sm"
                placeholder="Description (optional)"
                value={newInterest.description}
                onChange={(e) => setNewInterest((f) => ({ ...f, description: e.target.value }))}
              />
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-400">Weight: {newInterest.weight.toFixed(1)}</span>
                <input
                  type="range" min="0.1" max="1.0" step="0.1"
                  value={newInterest.weight}
                  onChange={(e) => setNewInterest((f) => ({ ...f, weight: parseFloat(e.target.value) }))}
                  className="flex-1 accent-brand-500"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => createInterest.mutate()}
                  disabled={!newInterest.name.trim() || createInterest.isPending}
                  className="btn-primary text-xs flex items-center gap-1.5"
                >
                  <Save className="w-3 h-3" /> Save
                </button>
                <button onClick={() => setShowAddForm(false)} className="btn-ghost text-xs">Cancel</button>
              </div>
            </div>
          )}

          {interests.length === 0 ? (
            <div className="card p-6 text-center">
              <p className="text-slate-400 text-sm">No interests yet. Add some to personalize your feed.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {interests.map((interest) => (
                <InterestCard
                  key={interest.id}
                  interest={interest}
                  onDelete={(id) => deleteInterest.mutate(id)}
                  onUpdate={(id, weight) => updateInterest.mutate({ id, weight })}
                />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
