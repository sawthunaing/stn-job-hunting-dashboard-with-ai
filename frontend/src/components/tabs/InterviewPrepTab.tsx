"use client";
import { useState } from "react";
import { RefreshCw, Brain, Zap, Copy, Sparkles } from "lucide-react";
import { api, type JobDetail } from "@/lib/api";
import { ActionButton } from "../ui";

export function InterviewPrepTab({ job, onUpdate }: { job: JobDetail; onUpdate: (j: JobDetail) => void }) {
  const [section, setSection] = useState<"technical" | "behavioral">("technical");
  const [busy, setBusy] = useState(false);

  async function generate() {
    setBusy(true);
    try { onUpdate(await api.prep(job.id)); }
    catch (e: any) { alert(e.message); }
    finally { setBusy(false); }
  }

  if (!job.interview_prep) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-12 text-center">
        <Brain className="w-10 h-10 text-zinc-700 mx-auto mb-3" />
        <div className="text-zinc-300 font-medium mb-1">No interview prep yet</div>
        <div className="text-zinc-500 text-sm mb-5">
          Generate questions tailored to this specific job and your background.
        </div>
        <ActionButton
          icon={Sparkles}
          label={busy ? "Generating..." : "Generate Prep"}
          primary
          onClick={generate}
          loading={busy}
        />
      </div>
    );
  }

  const items = job.interview_prep[section] || [];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="inline-flex p-1 bg-zinc-900/60 border border-zinc-800 rounded-lg">
          <button
            onClick={() => setSection("technical")}
            className={`px-3.5 py-1.5 text-xs font-medium rounded-md transition-colors ${
              section === "technical" ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            Technical · {job.interview_prep.technical?.length || 0}
          </button>
          <button
            onClick={() => setSection("behavioral")}
            className={`px-3.5 py-1.5 text-xs font-medium rounded-md transition-colors ${
              section === "behavioral" ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            Behavioral · {job.interview_prep.behavioral?.length || 0}
          </button>
        </div>
        <button onClick={generate} disabled={busy} className="inline-flex items-center gap-1.5 text-xs text-zinc-400 hover:text-zinc-200 disabled:opacity-50">
          <RefreshCw className={`w-3 h-3 ${busy ? "animate-spin" : ""}`} /> Regenerate
        </button>
      </div>

      <div className="space-y-3">
        {items.map((item, i) => (
          <div key={i} className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5 hover:border-zinc-700 transition-colors group">
            <div className="flex items-start gap-3 mb-3">
              <div className="w-7 h-7 rounded-lg bg-blue-500/15 text-blue-300 flex items-center justify-center text-xs font-semibold shrink-0">
                {String(i + 1).padStart(2, "0")}
              </div>
              <p className="text-zinc-100 text-sm leading-relaxed flex-1">{item.q}</p>
              <button
                onClick={() => navigator.clipboard.writeText(item.q)}
                className="opacity-0 group-hover:opacity-100 transition-opacity text-zinc-500 hover:text-zinc-200 shrink-0"
              >
                <Copy className="w-4 h-4" />
              </button>
            </div>
            <div className="ml-10 space-y-2">
              <div className="flex items-start gap-2 text-xs">
                <Brain className="w-3.5 h-3.5 text-violet-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-violet-300 font-medium">Why this is likely: </span>
                  <span className="text-zinc-400">{item.why}</span>
                </div>
              </div>
              {item.framework && (
                <div className="flex items-start gap-2 text-xs">
                  <Zap className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="text-amber-300 font-medium">Approach: </span>
                    <span className="text-zinc-400">{item.framework}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
