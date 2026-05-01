"use client";
import { useEffect, useState } from "react";
import { Eye, Github } from "lucide-react";
import { api } from "@/lib/api";

let cachedDemoMode: boolean | null = null;

/** Hook returning whether the backend is in demo mode. Cached per-session. */
export function useDemoMode(): boolean {
  const [val, setVal] = useState<boolean>(cachedDemoMode ?? false);
  useEffect(() => {
    if (cachedDemoMode !== null) {
      setVal(cachedDemoMode);
      return;
    }
    api.demoInfo()
      .then((r) => { cachedDemoMode = r.demo_mode; setVal(r.demo_mode); })
      .catch(() => { cachedDemoMode = false; setVal(false); });
  }, []);
  return val;
}

/** Banner shown across the top of every page when in demo mode. */
export function DemoBanner() {
  const isDemo = useDemoMode();
  if (!isDemo) return null;
  return (
    <div className="bg-blue-500/10 border-b border-blue-500/30 text-blue-100 px-4 py-2 text-xs flex items-center justify-center gap-3 flex-wrap">
      <Eye className="w-3.5 h-3.5 shrink-0" />
      <span className="text-blue-200">
        Public demo · read-only · AI analyses pre-computed · no edits
      </span>
      <a
        href="https://github.com/sawthunaing/stn-job-hunting-dashboard-with-ai"
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1 text-blue-300 hover:text-blue-200 underline underline-offset-2"
      >
        <Github className="w-3 h-3" /> Source
      </a>
    </div>
  );
}
