"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { profileAPI, interestsAPI, type Interest } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth-store";
import { AppShell } from "@/components/layout/AppShell";
import { Segmented } from "@/components/Segmented";
import { WeightSlider } from "@/components/WeightSlider";
import { Plus, X } from "lucide-react";
import toast from "react-hot-toast";

const EXPERTISE_OPTIONS = ["Beginner", "Intermediate", "Advanced", "Expert"];
const DEPTH_OPTIONS = ["Short", "Medium", "Deep"];
const FREQUENCY_OPTIONS = ["Daily", "Weekly", "Real-time"];

function EditInterestForm({
  initial,
  onCancel,
  onSave,
  saving,
}: {
  initial: { name: string; description: string; weight: number };
  onCancel: () => void;
  onSave: (v: { name: string; description: string; weight: number }) => void;
  saving: boolean;
}) {
  const [name, setName] = useState(initial.name);
  const [description, setDescription] = useState(initial.description);
  const [weight, setWeight] = useState(initial.weight);

  return (
    <div className="px-4 py-3.5 rounded-xl bg-surface-card border border-accent-purple/40 flex flex-col gap-2.5">
      <div className="grid grid-cols-1 sm:grid-cols-[1fr_1.6fr] gap-2.5">
        <input
          className="input text-sm"
          placeholder="Interest name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          disabled={Boolean(initial.name)}
        />
        <input
          className="input text-sm"
          placeholder="Description (optional) — helps the agent plan searches"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>
      <div className="flex items-center gap-3.5">
        <span className="font-mono text-[11px] text-ink-soft shrink-0">WEIGHT {weight.toFixed(2)}</span>
        <WeightSlider value={weight} onChange={setWeight} />
        <button
          onClick={() => onSave({ name, description, weight })}
          disabled={!name.trim() || saving}
          className="px-3 py-1.5 rounded-lg bg-brand-gradient text-white text-xs font-bold disabled:opacity-50 shrink-0"
        >
          Save
        </button>
        <button onClick={onCancel} className="text-xs text-ink-dim hover:text-ink shrink-0">Cancel</button>
      </div>
    </div>
  );
}

function InterestRow({ interest, editing, onEdit, onDelete }: {
  interest: Interest;
  editing: boolean;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const pct = `${interest.weight * 100}%`;
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_160px_40px_24px] gap-4 items-center py-[13px] border-t border-white/[0.08]">
      <button onClick={onEdit} className="text-left min-w-0">
        <div className={`text-[14.5px] font-semibold ${editing ? "text-accent-purpleText" : "text-ink"}`}>{interest.name}</div>
        {interest.description && <div className="text-xs text-ink-soft mt-0.5 truncate">{interest.description}</div>}
      </button>
      <span className="relative h-1 rounded-full bg-surface-hover">
        <span className="absolute inset-y-0 left-0 rounded-full bg-accent-purple" style={{ width: pct }} />
        <span className="absolute top-1/2 w-3.5 h-3.5 rounded-full bg-white" style={{ left: pct, transform: "translate(-50%,-50%)" }} />
      </span>
      <span className="font-mono text-[13px] text-accent-purpleText text-right">{interest.weight.toFixed(1)}</span>
      <button onClick={onDelete} className="text-ink-faint hover:text-red-400 text-center transition-colors">
        <X className="w-3.5 h-3.5 mx-auto" />
      </button>
    </div>
  );
}

export default function ProfilePage() {
  const ready = useRequireAuth();
  const qc = useQueryClient();
  const [editingId, setEditingId] = useState<string | "new" | null>(null);

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
    mutationFn: (data: Parameters<typeof profileAPI.updateProfile>[0]) => profileAPI.updateProfile(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["profile"] });
      toast.success("Profile updated");
    },
  });

  const createInterest = useMutation({
    mutationFn: (v: { name: string; description: string; weight: number }) =>
      interestsAPI.create(v.name, v.description || null, v.weight),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["interests"] });
      setEditingId(null);
      toast.success("Interest added");
    },
    onError: () => toast.error("Failed to add interest"),
  });

  const editInterest = useMutation({
    mutationFn: ({ id, v }: { id: string; v: { name: string; description: string; weight: number } }) =>
      interestsAPI.update(id, { description: v.description, weight: v.weight }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["interests"] });
      setEditingId(null);
      toast.success("Interest updated");
    },
  });

  const deleteInterest = useMutation({
    mutationFn: (id: string) => interestsAPI.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["interests"] });
      toast.success("Interest removed");
    },
  });

  if (!ready) return null;

  return (
    <AppShell>
      <div className="px-9 pt-7 pb-14 grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_340px] gap-10 max-w-[1180px]">
        <div className="flex flex-col gap-[22px] min-w-0">
          <div>
            <h1 className="font-serif text-[30px] leading-tight text-ink m-0">Profile &amp; interests</h1>
            <div className="mt-1.5 text-[13px] text-ink-dim">
              Interest weights feed the ranker directly. The agent adjusts them over time; you can always override.
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="label-mono">Interests · {interests.length}</div>
            {editingId !== "new" && (
              <button
                onClick={() => setEditingId("new")}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white text-surface text-[12.5px] font-bold"
              >
                <Plus className="w-3.5 h-3.5" /> Add interest
              </button>
            )}
          </div>

          {editingId === "new" && (
            <EditInterestForm
              initial={{ name: "", description: "", weight: 0.7 }}
              saving={createInterest.isPending}
              onCancel={() => setEditingId(null)}
              onSave={(v) => createInterest.mutate(v)}
            />
          )}

          {interests.length === 0 ? (
            <div className="card p-6 text-center">
              <p className="text-ink-muted text-sm">No interests yet. Add some to personalize your feed.</p>
            </div>
          ) : (
            <div className="flex flex-col">
              {interests.map((interest) =>
                editingId === interest.id ? (
                  <div key={interest.id} className="py-2">
                    <EditInterestForm
                      initial={{ name: interest.name, description: interest.description ?? "", weight: interest.weight }}
                      saving={editInterest.isPending}
                      onCancel={() => setEditingId(null)}
                      onSave={(v) => editInterest.mutate({ id: interest.id, v })}
                    />
                  </div>
                ) : (
                  <InterestRow
                    key={interest.id}
                    interest={interest}
                    editing={false}
                    onEdit={() => setEditingId(interest.id)}
                    onDelete={() => deleteInterest.mutate(interest.id)}
                  />
                )
              )}
            </div>
          )}
        </div>

        {profile && (
          <div className="flex flex-col gap-4 pt-2 lg:pt-16">
            <div className="card px-5 py-[18px] flex flex-col gap-4">
              <div className="label-mono">Reading preferences</div>
              <div>
                <div className="text-[12.5px] text-ink-muted mb-2">Expertise level</div>
                <Segmented
                  options={EXPERTISE_OPTIONS}
                  value={profile.expertise_level}
                  onChange={(v) => updateProfile.mutate({ expertise_level: v.toLowerCase() as any })}
                />
              </div>
              <div>
                <div className="text-[12.5px] text-ink-muted mb-2">Content depth</div>
                <Segmented
                  options={DEPTH_OPTIONS}
                  value={profile.preferred_depth}
                  onChange={(v) => updateProfile.mutate({ preferred_depth: v.toLowerCase() as any })}
                />
              </div>
              <div>
                <div className="text-[12.5px] text-ink-muted mb-2">Frequency</div>
                <Segmented
                  options={FREQUENCY_OPTIONS}
                  value={profile.preferred_frequency === "realtime" ? "Real-time" : profile.preferred_frequency}
                  onChange={(v) => updateProfile.mutate({ preferred_frequency: v.toLowerCase().replace("-", "") as any })}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
