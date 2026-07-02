// =============================================================================
// FRONTEND: CV download buttons (DOCX + PDF)
// =============================================================================
//
// The download endpoint needs the JWT auth header, so we can't use a plain
// <a href> link. Instead we fetch the file as a blob (with auth), then trigger
// a browser download. Below is a self-contained helper + button group.
//
// TWO THINGS TO CHECK / ADJUST for your codebase:
//   (A) API_BASE  - how your app knows the backend URL. Most likely
//                   process.env.NEXT_PUBLIC_API_URL (same as lib/api.ts uses).
//   (B) getToken() - how your app stores the JWT. If lib/api.ts reads it from
//                   localStorage under a specific key, match that key here.
//
// If you paste me your lib/api.ts I'll wire these to match exactly.


// ---- 1. Add this helper to frontend/src/lib/api.ts --------------------------

export async function downloadTailoredCV(
  jobId: number,
  format: "pdf" | "docx",
): Promise<void> {
  // (A) Match however the rest of api.ts builds the base URL:
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // (B) Match however the rest of api.ts reads the JWT.
  // Common patterns - use whichever your app already uses:
  const token =
    (typeof window !== "undefined" && localStorage.getItem("token")) || "";

  const res = await fetch(`${API_BASE}/jobs/${jobId}/cv/download?format=${format}`, {
    method: "GET",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!res.ok) {
    let msg = `Download failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) msg = body.detail;
    } catch {}
    throw new Error(msg);
  }

  // Pull filename from Content-Disposition, fall back to a sensible default
  const cd = res.headers.get("Content-Disposition") || "";
  const match = cd.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : `tailored_cv.${format}`;

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}


// ---- 2. Add the buttons to your Tailored CV tab component -------------------
//
// In the component that renders the tailored CV (likely
// frontend/src/components/tabs/TailoredCV.tsx), import the helper and add two
// buttons. Show them only once a CV has been generated (cv?.content exists).
//
// Example (adapt classNames to your design system):

/*
import { useState } from "react";
import { Download, FileText, Loader2 } from "lucide-react";
import { downloadTailoredCV } from "@/lib/api";

// inside your component, where `jobId` and the generated `cv` object are in scope:

function CvDownloadButtons({ jobId, hasCv }: { jobId: number; hasCv: boolean }) {
  const [busy, setBusy] = useState<"pdf" | "docx" | null>(null);
  const [err, setErr] = useState<string | null>(null);

  if (!hasCv) return null;

  async function handle(format: "pdf" | "docx") {
    setErr(null);
    setBusy(format);
    try {
      await downloadTailoredCV(jobId, format);
    } catch (e: any) {
      setErr(e?.message || "Download failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex items-center gap-2 mt-3">
      <button
        onClick={() => handle("pdf")}
        disabled={busy !== null}
        className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm px-3 py-1.5"
      >
        {busy === "pdf" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
        Download PDF
      </button>
      <button
        onClick={() => handle("docx")}
        disabled={busy !== null}
        className="inline-flex items-center gap-1.5 rounded-md bg-zinc-700 hover:bg-zinc-600 disabled:opacity-50 text-white text-sm px-3 py-1.5"
      >
        {busy === "docx" ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
        Download DOCX
      </button>
      {err && <span className="text-rose-400 text-xs">{err}</span>}
    </div>
  );
}

// Then render <CvDownloadButtons jobId={job.id} hasCv={!!cv?.content} /> near
// the top of your Tailored CV tab, above or below the rendered markdown.
*/
