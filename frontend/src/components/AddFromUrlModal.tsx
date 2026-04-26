"use client";
import { useState } from "react";
import { X, Sparkles, Link2, Pencil } from "lucide-react";
import { api, type JobDetail } from "@/lib/api";

interface Props {
  onClose: () => void;
  onCreated: (job: JobDetail) => void;
  /** Tap "Manual entry" to switch to the form modal. */
  onSwitchToManual: () => void;
}

export function AddFromUrlModal({ onClose, onCreated, onSwitchToManual }: Props) {
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!url) return;
    setBusy(true);
    setError(null);
    try {
      const job = await api.createFromUrl(url);
      onCreated(job);
    } catch (e: any) {
      setError(e.message || "Failed to scrape URL");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={onClose}>
      <div
        className="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-5 border-b border-zinc-800">
          <div>
            <div className="text-zinc-100 font-semibold text-sm">Add job</div>
            <div className="text-zinc-500 text-xs mt-0.5">Paste a posting URL — ChatGPT will extract the details</div>
          </div>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-200">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-5 space-y-3">
          <div className="relative">
            <Link2 className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              autoFocus
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://job-boards.greenhouse.io/..."
              className="w-full bg-zinc-950 border border-zinc-800 rounded-md pl-8 pr-3 py-2.5 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-blue-500/40"
              onKeyDown={(e) => e.key === "Enter" && submit()}
            />
          </div>
          {error && (
            <div className="p-3 rounded-md bg-red-500/10 border border-red-500/20 text-xs text-red-300">
              {error}
            </div>
          )}
          <div className="text-[11px] text-zinc-600">
            Note: LinkedIn often blocks scrapers. Greenhouse, Lever, Ashby, and direct company career pages work best.
          </div>
        </div>
        <div className="flex justify-between gap-2 p-5 border-t border-zinc-800">
          <button
            onClick={onSwitchToManual}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200"
          >
            <Pencil className="w-3 h-3" />
            Enter manually instead
          </button>
          <div className="flex gap-2">
            <button onClick={onClose} className="px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200">
              Cancel
            </button>
            <button
              onClick={submit}
              disabled={busy || !url}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-md bg-blue-500 hover:bg-blue-400 text-white text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Sparkles className={`w-3.5 h-3.5 ${busy ? "animate-spin" : ""}`} />
              {busy ? "Scraping..." : "Scrape & Add"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
