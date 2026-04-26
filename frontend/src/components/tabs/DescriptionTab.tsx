"use client";
import type { JobDetail } from "@/lib/api";

export function DescriptionTab({ job }: { job: JobDetail }) {
  if (!job.description) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-12 text-center text-zinc-500 text-sm">
        No description saved. Click <span className="text-blue-400">Edit</span> to paste one in.
      </div>
    );
  }
  return (
    <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-zinc-300 bg-transparent p-0">
      {job.description}
    </pre>
  );
}
