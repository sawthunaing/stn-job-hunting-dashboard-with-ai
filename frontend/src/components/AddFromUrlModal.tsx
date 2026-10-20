"use client";
import { useState } from "react";
import Link from "next/link";
import { X, Sparkles, Link2, Pencil } from "lucide-react";
import { api, ApiError, type JobDetail } from "@/lib/api";

const INDEED_RE = /^https?:\/\/([^/]*\.)?indeed\.[a-z.]+\//i;
const CVLIBRARY_RE = /^https?:\/\/(www\.)?cv-library\.co\.uk\//i;

/** Job boards with their own import route: dedup by job id, paste-text fallback. */
const BOARDS = {
  indeed: { name: "Indeed", re: INDEED_RE, create: api.createFromIndeed },
  cvlibrary: { name: "CV-Library", re: CVLIBRARY_RE, create: api.importFromCVLibrary },
};

function boardFor(url: string) {
  return Object.values(BOARDS).find((b) => b.re.test(url)) ?? null;
}

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
  const [pasteText, setPasteText] = useState("");
  const [needsPaste, setNeedsPaste] = useState(false);
  const [existingJobId, setExistingJobId] = useState<number | null>(null);
  const board = boardFor(url.trim());

  async function submit() {
    if (!url) return;
    setBusy(true);
    setError(null);
    setExistingJobId(null);
    try {
      const job = board
        ? await board.create(url.trim(), pasteText)
        : await api.createFromUrl(url.trim());
      onCreated(job);
    } catch (e: any) {
      if (e instanceof ApiError && board && e.status === 422) {
        setNeedsPaste(true);
        setError(typeof e.detail === "string" ? e.detail : `${board.name} blocked automated access.`);
      } else if (e instanceof ApiError && e.status === 409) {
        setError("Already imported.");
        setExistingJobId(typeof e.detail?.job_id === "number" ? e.detail.job_id : null);
      } else if (e instanceof ApiError && typeof e.detail === "string") {
        setError(e.detail);
      } else {
        setError(e.message || "Failed to scrape URL");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-stretch md:items-center justify-center bg-black/60 backdrop-blur-sm md:p-4" onClick={onClose}>
      <div
        className="w-full md:max-w-lg bg-zinc-900 md:border border-zinc-800 md:rounded-xl shadow-2xl h-dvh md:h-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-5 border-b border-zinc-800">
          <div>
            <div className="text-zinc-100 font-semibold text-sm">Add job</div>
            <div className="text-zinc-500 text-xs mt-0.5">Paste a posting URL — Claude will extract the details</div>
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
          {board && needsPaste && (
            <textarea
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              rows={8}
              placeholder={`Open the ${board.name} posting in your browser, select all, copy, and paste the text here`}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2.5 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-blue-500/40"
            />
          )}
          {error && (
            <div className="p-3 rounded-md bg-red-500/10 border border-red-500/20 text-xs text-red-300">
              {error}
              {existingJobId !== null && (
                <>
                  {" "}
                  <Link href={`/applications?job=${existingJobId}`} onClick={onClose} className="underline hover:text-red-200">
                    Open the existing job
                  </Link>
                </>
              )}
            </div>
          )}
          <div className="text-[11px] text-zinc-600">
            Indeed and CV-Library links are imported by job id; if the site blocks the server you can paste the posting text instead. LinkedIn also often blocks scrapers. Greenhouse, Lever, Ashby, and direct company career pages work best.
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
              {busy ? "Importing..." : needsPaste && pasteText ? "Import pasted text" : "Scrape & Add"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
