"use client";
import { Search, Plus, MapPin, Star, X, Sparkles } from "lucide-react";
import type { JobListItem } from "@/lib/api";
import { SuitabilityRing, StatusPill, logoFor } from "./ui";

const STATUSES = ["All", "New", "Applied", "Interviewing", "Offer", "Rejected"];

export function Sidebar({
  jobs, selectedId, onSelect, search, onSearch, statusFilter, onStatusChange, onAddClick, loading,
  isOpen = true, onClose,
  minScore, onMinScoreChange, includeUnscored, onIncludeUnscoredChange,
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
  /** Mobile drawer state. Ignored on md+ screens (always visible). */
  isOpen?: boolean;
  /** Called when a job is selected on mobile (auto-closes drawer). */
  onClose?: () => void;
  /** Minimum AI suitability score. 0 = no filter. */
  minScore: number;
  onMinScoreChange: (v: number) => void;
  /** Whether to include unanalyzed jobs (no score) when minScore > 0. */
  includeUnscored: boolean;
  onIncludeUnscoredChange: (v: boolean) => void;
}) {
  // Compute score distribution from the FULL job set (before this filter is applied).
  // Bands: Excellent 90+, Good 75-89, OK 60-74, Low <60, Unscored null.
  const dist = jobs.reduce(
    (acc, j) => {
      if (j.suitability == null) acc.unscored++;
      else if (j.suitability >= 90) acc.excellent++;
      else if (j.suitability >= 75) acc.good++;
      else if (j.suitability >= 60) acc.ok++;
      else acc.low++;
      return acc;
    },
    { excellent: 0, good: 0, ok: 0, low: 0, unscored: 0 }
  );
  const total = jobs.length || 1; // avoid divide-by-zero in the bar widths
  const bandPct = (n: number) => (n / total) * 100;

  // Apply the score filter to derive what's actually shown
  const filteredJobs = jobs.filter((j) => {
    if (minScore === 0) return true;
    if (j.suitability == null) return includeUnscored;
    return j.suitability >= minScore;
  });

  // Quick-jump: tapping a histogram band sets minScore to its lower edge
  const jumpToBand = (lower: number) => {
    onMinScoreChange(lower);
    if (lower > 0) onIncludeUnscoredChange(false);
  };

  return (
    <>
      {/* Backdrop - mobile only, when drawer is open */}
      {isOpen && (
        <button
          onClick={onClose}
          aria-label="Close menu"
          className="fixed inset-0 bg-black/60 z-30 md:hidden"
        />
      )}

      <aside
        className={`
          fixed md:static inset-y-0 left-0 z-40
          w-[85vw] max-w-[360px] md:w-[360px]
          border-r border-zinc-800/80 flex flex-col bg-zinc-950 shrink-0
          transition-transform duration-200 ease-out
          ${isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
        `}
      >
        <div className="p-4 border-b border-zinc-800/80 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-zinc-200 text-sm font-semibold">Applications</h2>
            <div className="flex items-center gap-2">
              <button
                onClick={onAddClick}
                className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-medium px-2 py-1 -mr-1"
              >
                <Plus className="w-3.5 h-3.5" /> Add
              </button>
              {/* Close button - mobile only */}
              <button
                onClick={onClose}
                aria-label="Close menu"
                className="md:hidden p-1 -mr-2 text-zinc-500 hover:text-zinc-300"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              value={search}
              onChange={(e) => onSearch(e.target.value)}
              placeholder="Search company or role..."
              className="w-full bg-zinc-900/60 border border-zinc-800 rounded-md pl-8 pr-3 py-2.5 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-700 focus:bg-zinc-900"
            />
          </div>
          <div className="flex items-center gap-1.5 overflow-x-auto -mx-1 px-1 pb-1 scrollbar-hide">
            {STATUSES.map((s) => (
              <button
                key={s}
                onClick={() => onStatusChange(s)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap ${
                  statusFilter === s
                    ? "bg-zinc-800 text-zinc-100 border border-zinc-700"
                    : "text-zinc-500 hover:text-zinc-300 border border-transparent"
                }`}
              >
                {s}
              </button>
            ))}
          </div>

          {/* AI score distribution histogram + slider */}
          {jobs.length > 0 && (
            <div className="pt-2 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-[11px] text-zinc-500 uppercase tracking-wider">
                  <Sparkles className="w-3 h-3" /> AI fit score
                </div>
                <div className="text-[11px] text-zinc-400 tabular-nums">
                  {minScore === 0 ? "All" : `${minScore}+`}
                  <span className="text-zinc-600 ml-1">· {filteredJobs.length}/{jobs.length}</span>
                </div>
              </div>

              {/* Histogram - 5 stacked bands as a single horizontal bar */}
              <div className="flex h-2 rounded-md overflow-hidden bg-zinc-900 border border-zinc-800">
                {dist.excellent > 0 && (
                  <button
                    onClick={() => jumpToBand(90)}
                    title={`Excellent (90+): ${dist.excellent}`}
                    className="bg-emerald-500/80 hover:bg-emerald-400 transition-colors"
                    style={{ width: `${bandPct(dist.excellent)}%` }}
                  />
                )}
                {dist.good > 0 && (
                  <button
                    onClick={() => jumpToBand(75)}
                    title={`Good (75-89): ${dist.good}`}
                    className="bg-blue-500/80 hover:bg-blue-400 transition-colors"
                    style={{ width: `${bandPct(dist.good)}%` }}
                  />
                )}
                {dist.ok > 0 && (
                  <button
                    onClick={() => jumpToBand(60)}
                    title={`OK (60-74): ${dist.ok}`}
                    className="bg-amber-500/80 hover:bg-amber-400 transition-colors"
                    style={{ width: `${bandPct(dist.ok)}%` }}
                  />
                )}
                {dist.low > 0 && (
                  <button
                    onClick={() => jumpToBand(0)}
                    title={`Low (<60): ${dist.low}`}
                    className="bg-rose-500/70 hover:bg-rose-400 transition-colors"
                    style={{ width: `${bandPct(dist.low)}%` }}
                  />
                )}
                {dist.unscored > 0 && (
                  <button
                    onClick={() => { onMinScoreChange(0); onIncludeUnscoredChange(true); }}
                    title={`Not yet analyzed: ${dist.unscored}`}
                    className="bg-zinc-700 hover:bg-zinc-600 transition-colors"
                    style={{ width: `${bandPct(dist.unscored)}%` }}
                  />
                )}
              </div>

              {/* Tiny legend */}
              <div className="flex items-center gap-2 text-[10px] flex-wrap">
                {dist.excellent > 0 && (
                  <span className="inline-flex items-center gap-1">
                    <span className="w-2 h-2 rounded-sm bg-emerald-500/80" />
                    <span className="text-zinc-400 tabular-nums">{dist.excellent}</span>
                  </span>
                )}
                {dist.good > 0 && (
                  <span className="inline-flex items-center gap-1">
                    <span className="w-2 h-2 rounded-sm bg-blue-500/80" />
                    <span className="text-zinc-400 tabular-nums">{dist.good}</span>
                  </span>
                )}
                {dist.ok > 0 && (
                  <span className="inline-flex items-center gap-1">
                    <span className="w-2 h-2 rounded-sm bg-amber-500/80" />
                    <span className="text-zinc-400 tabular-nums">{dist.ok}</span>
                  </span>
                )}
                {dist.low > 0 && (
                  <span className="inline-flex items-center gap-1">
                    <span className="w-2 h-2 rounded-sm bg-rose-500/70" />
                    <span className="text-zinc-400 tabular-nums">{dist.low}</span>
                  </span>
                )}
                {dist.unscored > 0 && (
                  <span className="inline-flex items-center gap-1">
                    <span className="w-2 h-2 rounded-sm bg-zinc-700" />
                    <span className="text-zinc-400 tabular-nums">{dist.unscored}?</span>
                  </span>
                )}
              </div>

              {/* Slider */}
              <div className="space-y-1.5">
                <input
                  type="range"
                  min={0}
                  max={95}
                  step={5}
                  value={minScore}
                  onChange={(e) => onMinScoreChange(parseInt(e.target.value, 10))}
                  className="w-full h-1.5 accent-blue-500 cursor-pointer"
                  aria-label="Minimum AI suitability score"
                />
                <div className="flex items-center justify-between text-[10px] text-zinc-600 tabular-nums">
                  <span>All</span>
                  <span className={minScore >= 60 && minScore < 75 ? "text-amber-400 font-medium" : ""}>60+</span>
                  <span className={minScore >= 75 && minScore < 90 ? "text-blue-400 font-medium" : ""}>75+</span>
                  <span className={minScore >= 90 ? "text-emerald-400 font-medium" : ""}>90+</span>
                </div>
              </div>

              {/* Include unscored toggle - only relevant when score filter is on */}
              {minScore > 0 && dist.unscored > 0 && (
                <label className="flex items-center gap-2 text-[11px] text-zinc-400 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={includeUnscored}
                    onChange={(e) => onIncludeUnscoredChange(e.target.checked)}
                    className="accent-blue-500 cursor-pointer"
                  />
                  Include unanalyzed ({dist.unscored})
                </label>
              )}
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto overscroll-contain">
          {loading && jobs.length === 0 && (
            <div className="p-8 text-center text-zinc-500 text-xs">Loading...</div>
          )}
          {!loading && jobs.length === 0 && (
            <div className="p-8 text-center text-zinc-500 text-xs">
              No applications. Tap <span className="text-blue-400">+ Add</span> to track your first one.
            </div>
          )}
          {!loading && jobs.length > 0 && filteredJobs.length === 0 && (
            <div className="p-8 text-center text-zinc-500 text-xs space-y-2">
              <div>No applications match this score filter.</div>
              <button
                onClick={() => { onMinScoreChange(0); onIncludeUnscoredChange(true); }}
                className="text-blue-400 hover:text-blue-300 underline underline-offset-2"
              >
                Clear score filter
              </button>
            </div>
          )}
          {filteredJobs.map((job) => {
            const { letter, color } = logoFor(job.company);
            const active = job.id === selectedId;
            return (
              <button
                key={job.id}
                onClick={() => {
                  onSelect(job.id);
                  // Auto-close drawer on mobile after selection
                  onClose?.();
                }}
                className={`w-full text-left px-4 py-4 border-l-2 transition-all ${
                  active ? "bg-zinc-800/60 border-l-blue-500" : "border-l-transparent hover:bg-zinc-800/30 active:bg-zinc-800/40"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className="w-10 h-10 rounded-md flex items-center justify-center text-base font-bold shrink-0 mt-0.5"
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
    </>
  );
}
