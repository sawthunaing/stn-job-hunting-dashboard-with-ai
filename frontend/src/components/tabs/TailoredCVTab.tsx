"use client";
import { useState } from "react";
import { RefreshCw, Sparkles, Copy, FileText, Download } from "lucide-react";
import { api, type JobDetail } from "@/lib/api";
import { ActionButton } from "../ui";

type DocType = "cv" | "cover_letter" | "recruiter_email";

const DOC_LABELS: Record<DocType, string> = {
  cv: "Tailored CV",
  cover_letter: "Cover Letter",
  recruiter_email: "Recruiter Email",
};

export function TailoredCVTab({ job, onUpdate }: { job: JobDetail; onUpdate: (j: JobDetail) => void }) {
  const [docType, setDocType] = useState<DocType>("cv");
  const [busy, setBusy] = useState(false);
  const [downloading, setDownloading] = useState<"pdf" | "docx" | null>(null);

  const doc = job.tailored_docs?.[docType];

  async function generate() {
    setBusy(true);
    try { onUpdate(await api.tailor(job.id, docType)); }
    catch (e: any) { alert(e.message); }
    finally { setBusy(false); }
  }

  async function download(format: "pdf" | "docx") {
    setDownloading(format);
    try { await api.downloadCV(job.id, format); }
    catch (e: any) { alert(e.message); }
    finally { setDownloading(null); }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="inline-flex p-1 bg-zinc-900/60 border border-zinc-800 rounded-lg">
          {(Object.keys(DOC_LABELS) as DocType[]).map((t) => (
            <button
              key={t}
              onClick={() => setDocType(t)}
              className={`px-3.5 py-1.5 text-xs font-medium rounded-md transition-colors ${
                docType === t ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {DOC_LABELS[t]}
            </button>
          ))}
        </div>
        <ActionButton
          icon={doc ? RefreshCw : Sparkles}
          label={busy ? "Generating..." : doc ? "Regenerate" : "Generate"}
          primary={!doc}
          onClick={generate}
          loading={busy}
        />
      </div>

      {!doc && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-12 text-center">
          <FileText className="w-10 h-10 text-zinc-700 mx-auto mb-3" />
          <div className="text-zinc-300 font-medium mb-1">No {DOC_LABELS[docType]} yet</div>
          <div className="text-zinc-500 text-sm">Generate one tuned to this specific job.</div>
        </div>
      )}

      {doc && (
        <>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-6">
            <div className="flex items-start justify-between mb-5 pb-5 border-b border-zinc-800 gap-3 flex-wrap">
              <div>
                <div className="text-zinc-100 text-base font-semibold">Tailored for: {job.role}</div>
                <div className="text-zinc-500 text-xs mt-0.5">{job.company}-specific tone</div>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <div className="px-2 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-[10px] text-emerald-300 font-medium">
                  ATS Match: {doc.ats_match_pct ?? "—"}%
                </div>
                <div className="px-2 py-1 rounded bg-blue-500/10 border border-blue-500/20 text-[10px] text-blue-300 font-medium">
                  Keywords: {(doc.keywords_matched?.length ?? 0)}/{(doc.keywords_matched?.length ?? 0) + (doc.keywords_missing?.length ?? 0)}
                </div>
                {/* Download buttons - only for CV doc type */}
                {docType === "cv" && (
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => download("pdf")}
                      disabled={!!downloading}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-600 text-zinc-200 text-[11px] font-medium border border-zinc-700/60 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Download CV as PDF"
                    >
                      <Download className="w-3 h-3" />
                      {downloading === "pdf" ? "..." : "PDF"}
                    </button>
                    <button
                      onClick={() => download("docx")}
                      disabled={!!downloading}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-600 text-zinc-200 text-[11px] font-medium border border-zinc-700/60 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Download CV as Word"
                    >
                      <Download className="w-3 h-3" />
                      {downloading === "docx" ? "..." : "DOCX"}
                    </button>
                  </div>
                )}
                <button
                  onClick={() => navigator.clipboard.writeText(doc.content)}
                  className="text-zinc-500 hover:text-zinc-200 p-1.5 rounded hover:bg-zinc-800/60"
                  title="Copy markdown"
                >
                  <Copy className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-zinc-300 bg-transparent p-0">
              {doc.content}
            </pre>
          </div>

          {(doc.keywords_missing?.length ?? 0) > 0 && (
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/[0.04] p-4">
              <div className="text-[10px] text-amber-400 uppercase tracking-wider mb-2">Keywords missing from your profile</div>
              <div className="flex flex-wrap gap-1.5">
                {doc.keywords_missing!.map((k, i) => (
                  <span key={i} className="text-[11px] px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-200">
                    {k}
                  </span>
                ))}
              </div>
            </div>
          )}

          {(doc.suggestions?.length ?? 0) > 0 && (
            <div className="rounded-xl border border-blue-500/20 bg-blue-500/[0.04] p-4">
              <div className="flex items-start gap-3">
                <Sparkles className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                <div className="text-xs text-zinc-300 space-y-1.5">
                  <div className="text-blue-300 font-medium">AI suggestions</div>
                  {doc.suggestions!.map((s, i) => (
                    <div key={i}>• {s}</div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
