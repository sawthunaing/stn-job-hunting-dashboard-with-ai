"use client";
import { Search, Plus, MapPin, Star } from "lucide-react";
import type { JobListItem } from "@/lib/api";
import { SuitabilityRing, StatusPill, logoFor } from "./ui";

const STATUSES = ["All", "New", "Applied", "Interviewing", "Offer", "Rejected"];

export function Sidebar({
  jobs, selectedId, onSelect, search, onSearch, statusFilter, onStatusChange, onAddClick, loading,
}: {
  jobs: JobListItem[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  search: string;
  onSearch: (s: string) => void;
  statusFilter: string;
  onStatusChange: (s: string) => void;
  onAddClick: () => void;
  loading: boolean;
}) {
  return (
    <aside className="w-[360px] border-r border-zinc-800/80 flex flex-col bg-zinc-950 shrink-0">
      <div className="p-4 border-b border-zinc-800/80 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-zinc-200 text-sm font-semibold">Applications</h2>
          <button
            onClick={onAddClick}
            className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-medium"
          >
            <Plus className="w-3.5 h-3.5" /> Add
          </button>
        </div>
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            placeholder="Search company or role..."
            className="w-full bg-zinc-900/60 border border-zinc-800 rounded-md pl-8 pr-3 py-2 text-xs text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-700 focus:bg-zinc-900"
          />
        </div>
        <div className="flex items-center gap-1.5 overflow-x-auto -mx-1 px-1 pb-1 scrollbar-hide">
          {STATUSES.map((s) => (
            <button
              key={s}
              onClick={() => onStatusChange(s)}
              className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors whitespace-nowrap ${
                statusFilter === s
                  ? "bg-zinc-800 text-zinc-100 border border-zinc-700"
                  : "text-zinc-500 hover:text-zinc-300 border border-transparent"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        {loading && jobs.length === 0 && (
          <div className="p-8 text-center text-zinc-500 text-xs">Loading...</div>
        )}
        {!loading && jobs.length === 0 && (
          <div className="p-8 text-center text-zinc-500 text-xs">
            No applications. Click <span className="text-blue-400">+ Add</span> to track your first one.
          </div>
        )}
        {jobs.map((job) => {
          const { letter, color } = logoFor(job.company);
          const active = job.id === selectedId;
          return (
            <button
              key={job.id}
              onClick={() => onSelect(job.id)}
              className={`w-full text-left px-4 py-3.5 border-l-2 transition-all ${
                active ? "bg-zinc-800/60 border-l-blue-500" : "border-l-transparent hover:bg-zinc-800/30"
              }`}
            >
              <div className="flex items-start gap-3">
                <div
                  className="w-9 h-9 rounded-md flex items-center justify-center text-sm font-bold shrink-0 mt-0.5"
                  style={{ backgroundColor: `${color}20`, color, border: `1px solid ${color}30` }}
                >
                  {letter}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-zinc-100 text-sm font-medium truncate">{job.company}</span>
                        {job.starred && <Star className="w-3 h-3 text-amber-400 shrink-0" fill="currentColor" />}
                      </div>
                      <div className="text-zinc-400 text-xs truncate mt-0.5">{job.role}</div>
                    </div>
                    {job.suitability != null && <SuitabilityRing score={job.suitability} size={36} />}
                  </div>
                  {job.location && (
                    <div className="flex items-center gap-2 mt-2 text-[11px] text-zinc-500">
                      <MapPin className="w-3 h-3" />
                      <span className="truncate">{job.location}</span>
                    </div>
                  )}
                  <div className="flex items-center justify-between mt-2">
                    <StatusPill status={job.status} />
                    {job.platform && <span className="text-[10px] text-zinc-600">{job.platform}</span>}
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  );
}
