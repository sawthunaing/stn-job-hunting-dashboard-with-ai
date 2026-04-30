"use client";
import { useState, useEffect } from "react";
import { X, Save } from "lucide-react";
import { api, type JobInput, type JobDetail, type Status, type WorkType } from "@/lib/api";

interface Props {
  onClose: () => void;
  onSaved: (job: JobDetail) => void;
  /** If provided, the modal is in edit mode. */
  editing?: JobDetail | null;
}

const STATUSES: Status[] = ["New", "Applied", "Interviewing", "Offer", "Rejected"];
const WORK_TYPES: WorkType[] = ["Remote", "Hybrid", "Onsite"];

export function JobFormModal({ onClose, onSaved, editing }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<JobInput>({
    company: "",
    role: "",
    location: "",
    work_type: undefined,
    platform: "",
    source_url: "",
    description: "",
    salary_min: undefined,
    salary_max: undefined,
    currency: "GBP",
    status: "New",
    notes: "",
  });

  // When editing, prefill the form from the job
  useEffect(() => {
    if (!editing) return;
    setForm({
      company: editing.company,
      role: editing.role,
      location: editing.location || "",
      work_type: editing.work_type || undefined,
      platform: editing.platform || "",
      source_url: editing.source_url || "",
      description: editing.description || "",
      salary_min: editing.salary_min || undefined,
      salary_max: editing.salary_max || undefined,
      currency: editing.currency || "GBP",
      status: editing.status,
      notes: editing.notes || "",
    });
  }, [editing]);

  function set<K extends keyof JobInput>(key: K, value: JobInput[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit() {
    if (!form.company.trim() || !form.role.trim()) {
      setError("Company and role are required");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      // Strip empty strings so they don't overwrite with ""
      const cleaned: JobInput = { ...form };
      (Object.keys(cleaned) as (keyof JobInput)[]).forEach((k) => {
        if (cleaned[k] === "") delete cleaned[k];
      });

      const job = editing
        ? await api.update(editing.id, cleaned as Partial<JobDetail>)
        : await api.create(cleaned);
      onSaved(job);
    } catch (e: any) {
      setError(e.message || "Save failed");
    } finally {
      setBusy(false);
    }
  }

  const inputClass =
    "w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-blue-500/40";
  const labelClass = "block text-[11px] uppercase tracking-wider text-zinc-500 mb-1.5";

  return (
    <div
      className="fixed inset-0 z-50 flex items-stretch md:items-center justify-center bg-black/60 backdrop-blur-sm md:p-4"
      onClick={onClose}
    >
      <div
        className="w-full md:max-w-2xl bg-zinc-900 md:border border-zinc-800 md:rounded-xl shadow-2xl h-screen md:h-auto md:max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-5 border-b border-zinc-800 shrink-0">
          <div>
            <div className="text-zinc-100 font-semibold text-sm">
              {editing ? "Edit job" : "Add job"}
            </div>
            <div className="text-zinc-500 text-xs mt-0.5">
              {editing ? "Update the application details" : "Track a new application"}
            </div>
          </div>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-4 overflow-y-auto">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass}>Company *</label>
              <input
                autoFocus={!editing}
                value={form.company}
                onChange={(e) => set("company", e.target.value)}
                className={inputClass}
                placeholder="Stripe"
              />
            </div>
            <div>
              <label className={labelClass}>Role *</label>
              <input
                value={form.role}
                onChange={(e) => set("role", e.target.value)}
                className={inputClass}
                placeholder="Senior Backend Engineer"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass}>Location</label>
              <input
                value={form.location || ""}
                onChange={(e) => set("location", e.target.value)}
                className={inputClass}
                placeholder="London, UK"
              />
            </div>
            <div>
              <label className={labelClass}>Work type</label>
              <select
                value={form.work_type || ""}
                onChange={(e) => set("work_type", (e.target.value || undefined) as WorkType | undefined)}
                className={inputClass}
              >
                <option value="">—</option>
                {WORK_TYPES.map((w) => (
                  <option key={w} value={w}>{w}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass}>Platform</label>
              <input
                value={form.platform || ""}
                onChange={(e) => set("platform", e.target.value)}
                className={inputClass}
                placeholder="LinkedIn / Greenhouse / referral"
              />
            </div>
            <div>
              <label className={labelClass}>Status</label>
              <select
                value={form.status || "New"}
                onChange={(e) => set("status", e.target.value as Status)}
                className={inputClass}
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className={labelClass}>Listing URL</label>
            <input
              value={form.source_url || ""}
              onChange={(e) => set("source_url", e.target.value)}
              className={inputClass}
              placeholder="https://..."
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className={labelClass}>Salary min (k/year)</label>
              <input
                type="number"
                value={form.salary_min ?? ""}
                onChange={(e) => set("salary_min", e.target.value ? parseInt(e.target.value) : undefined)}
                className={inputClass}
                placeholder="120"
              />
            </div>
            <div>
              <label className={labelClass}>Salary max (k/year)</label>
              <input
                type="number"
                value={form.salary_max ?? ""}
                onChange={(e) => set("salary_max", e.target.value ? parseInt(e.target.value) : undefined)}
                className={inputClass}
                placeholder="160"
              />
            </div>
            <div>
              <label className={labelClass}>Currency</label>
              <select
                value={form.currency || "GBP"}
                onChange={(e) => set("currency", e.target.value)}
                className={inputClass}
              >
                <option value="GBP">GBP £</option>
                <option value="USD">USD $</option>
                <option value="EUR">EUR €</option>
              </select>
            </div>
          </div>

          <div>
            <label className={labelClass}>Description</label>
            <textarea
              value={form.description || ""}
              onChange={(e) => set("description", e.target.value)}
              className={`${inputClass} font-mono text-xs`}
              rows={5}
              placeholder="Paste the job description here (optional)"
            />
          </div>

          <div>
            <label className={labelClass}>Personal notes</label>
            <textarea
              value={form.notes || ""}
              onChange={(e) => set("notes", e.target.value)}
              className={inputClass}
              rows={3}
              placeholder="Recruiter contact, next steps, prep ideas..."
            />
          </div>

          {error && (
            <div className="p-3 rounded-md bg-red-500/10 border border-red-500/20 text-xs text-red-300">
              {error}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 p-5 border-t border-zinc-800 shrink-0">
          <button onClick={onClose} className="px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200">
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={busy}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-md bg-blue-500 hover:bg-blue-400 text-white text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="w-3.5 h-3.5" />
            {busy ? "Saving..." : editing ? "Save changes" : "Create"}
          </button>
        </div>
      </div>
    </div>
  );
}
