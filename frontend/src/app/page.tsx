"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Target, Sparkles, TrendingUp, Clock, AlertCircle, ChevronRight,
  Plus, User, LogOut, ListChecks, Layers,
} from "lucide-react";
import { api, type JobListItem } from "@/lib/api";
import { AuthGuard } from "@/components/AuthGuard";
import { AddFromUrlModal } from "@/components/AddFromUrlModal";
import { JobFormModal } from "@/components/JobFormModal";
import { StatusPill, scoreColor, logoFor } from "@/components/ui";

// Stages of the funnel, in order. Anything else (Rejected, etc.) shows separately.
const FUNNEL_STAGES = [
  { key: "New",          label: "New",         color: "bg-zinc-500/30",   text: "text-zinc-300",     bar: "bg-zinc-400" },
  { key: "Applied",      label: "Applied",     color: "bg-amber-500/20",  text: "text-amber-300",    bar: "bg-amber-400" },
  { key: "Interviewing", label: "Interviewing", color: "bg-emerald-500/20", text: "text-emerald-300", bar: "bg-emerald-400" },
  { key: "Offer",        label: "Offer",       color: "bg-blue-500/20",   text: "text-blue-300",     bar: "bg-blue-400" },
];

const REJECTED = { key: "Rejected", label: "Rejected", color: "bg-rose-500/15", text: "text-rose-300", bar: "bg-rose-500/70" };

const DAY_MS = 24 * 60 * 60 * 1000;

function PageInner() {
  const router = useRouter();
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddUrl, setShowAddUrl] = useState(false);
  const [showAddManual, setShowAddManual] = useState(false);

  useEffect(() => {
    api.list({ status: "All", q: "" })
      .then(setJobs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // ============ COMPUTED VIEWS ============

  // Pipeline counts
  const pipeline = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const j of jobs) counts[j.status] = (counts[j.status] || 0) + 1;
    return counts;
  }, [jobs]);

  const totalActive = jobs.length - (pipeline["Rejected"] || 0);
  const maxFunnelCount = Math.max(1, ...FUNNEL_STAGES.map(s => pipeline[s.key] || 0));

  // Conversion rates between funnel stages (forward only)
  const conversions = useMemo(() => {
    const out: { from: string; to: string; rate: number; numerator: number; denominator: number }[] = [];
    for (let i = 0; i < FUNNEL_STAGES.length - 1; i++) {
      const from = FUNNEL_STAGES[i];
      const to = FUNNEL_STAGES[i + 1];
      // "Reached `to` or beyond" / "Reached `from` or beyond"
      const reachedFrom = FUNNEL_STAGES.slice(i).reduce((sum, s) => sum + (pipeline[s.key] || 0), 0);
      const reachedTo = FUNNEL_STAGES.slice(i + 1).reduce((sum, s) => sum + (pipeline[s.key] || 0), 0);
      out.push({
        from: from.label,
        to: to.label,
        numerator: reachedTo,
        denominator: reachedFrom,
        rate: reachedFrom > 0 ? Math.round((reachedTo / reachedFrom) * 100) : 0,
      });
    }
    return out;
  }, [pipeline]);

  // Top 3 opportunities: highest score, not yet applied
  const topOpportunities = useMemo(() => {
    return jobs
      .filter(j => j.suitability != null && j.status === "New")
      .sort((a, b) => (b.suitability ?? 0) - (a.suitability ?? 0))
      .slice(0, 3);
  }, [jobs]);

  // Recent activity: jobs added in last 7 days, max 5
  const recent = useMemo(() => {
    const cutoff = Date.now() - 7 * DAY_MS;
    return jobs
      .filter(j => new Date(j.created_at).getTime() >= cutoff)
      .slice(0, 5);
  }, [jobs]);

  // Needs attention: applied >14 days ago, still in "Applied"
  const needsAttention = useMemo(() => {
    const cutoff = Date.now() - 14 * DAY_MS;
    return jobs.filter(j =>
      j.status === "Applied" && new Date(j.created_at).getTime() < cutoff
    ).slice(0, 5);
  }, [jobs]);

  // Score average
  const avgScore = useMemo(() => {
    const scored = jobs.filter(j => j.suitability != null);
    if (!scored.length) return 0;
    return Math.round(scored.reduce((a, j) => a + (j.suitability || 0), 0) / scored.length);
  }, [jobs]);

  // ============ NAVIGATION ============

  function goToApplications(filter?: string) {
    if (filter) {
      router.push(`/applications?status=${encodeURIComponent(filter)}`);
    } else {
      router.push("/applications");
    }
  }

  function openJob(id: number) {
    router.push(`/applications?job=${id}`);
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <header className="h-14 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur sticky top-0 z-20 flex items-center justify-between px-3 md:px-5">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-7 h-7 rounded-md bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center shrink-0">
            <Target className="w-4 h-4 text-white" />
          </div>
          <span className="text-zinc-100 font-semibold text-sm tracking-tight truncate">
            <span className="md:hidden">Job Hunt</span>
            <span className="hidden md:inline">Ko Saw&apos;s Job Hunting Dashboard</span>
          </span>
          {/* Nav tabs */}
          <nav className="hidden md:flex items-center gap-1 ml-6">
            <Link href="/" className="px-3 py-1.5 rounded-md bg-zinc-800/60 text-zinc-100 text-xs font-medium">
              Overview
            </Link>
            <Link href="/applications" className="px-3 py-1.5 rounded-md hover:bg-zinc-800/40 text-zinc-400 hover:text-zinc-200 text-xs font-medium">
              Applications
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-1 md:gap-2 shrink-0">
          {/* Add button - prominent on overview page */}
          <button
            onClick={() => setShowAddUrl(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-blue-500 hover:bg-blue-400 text-white text-xs font-medium shadow-lg shadow-blue-500/20"
          >
            <Plus className="w-3.5 h-3.5" /> <span className="hidden sm:inline">Add</span>
          </button>
          <Link
            href="/profile"
            className="inline-flex items-center gap-1.5 px-2.5 py-2 rounded-md hover:bg-zinc-800/60 text-zinc-400 hover:text-zinc-200 text-xs"
            title="Profile"
          >
            <User className="w-4 h-4" />
            <span className="hidden md:inline">Profile</span>
          </Link>
          <button
            onClick={() => { api.logout(); router.replace("/login"); }}
            className="inline-flex items-center gap-1.5 px-2.5 py-2 rounded-md hover:bg-zinc-800/60 text-zinc-400 hover:text-zinc-200 text-xs"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden md:inline">Sign out</span>
          </button>
        </div>
      </header>

      {/* Mobile nav (visible below md) */}
      <nav className="md:hidden flex items-center gap-1 px-3 py-2 border-b border-zinc-800/80 bg-zinc-950">
        <Link href="/" className="px-3 py-1.5 rounded-md bg-zinc-800/60 text-zinc-100 text-xs font-medium">
          Overview
        </Link>
        <Link href="/applications" className="px-3 py-1.5 rounded-md hover:bg-zinc-800/40 text-zinc-400 text-xs font-medium">
          Applications
        </Link>
      </nav>

      <main className="max-w-6xl mx-auto px-4 md:px-6 py-6 md:py-8 space-y-6 md:space-y-8">
        {loading && (
          <div className="text-zinc-500 text-sm">Loading your pipeline...</div>
        )}

        {!loading && jobs.length === 0 && (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-12 text-center">
            <Target className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
            <h2 className="text-zinc-100 text-lg font-semibold mb-1">Nothing here yet</h2>
            <p className="text-zinc-400 text-sm mb-5 max-w-md mx-auto">
              Paste a job URL or add an application manually to start tracking. The AI will analyse fit, prep questions, and tailor a CV.
            </p>
            <button
              onClick={() => setShowAddUrl(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-blue-500 hover:bg-blue-400 text-white text-sm font-medium"
            >
              <Plus className="w-4 h-4" /> Add your first application
            </button>
          </div>
        )}

        {!loading && jobs.length > 0 && (
          <>
            {/* TOP STATS ROW */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatCard icon={Layers}    label="Active"       value={String(totalActive)}      />
              <StatCard icon={ListChecks} label="Total"        value={String(jobs.length)}      />
              <StatCard icon={Sparkles}   label="Avg fit"      value={avgScore ? `${avgScore}` : "—"} accent={avgScore ? scoreColor(avgScore).text : ""} />
              <StatCard icon={TrendingUp} label="Interviewing" value={String(pipeline["Interviewing"] || 0)} accent="text-emerald-400" />
            </div>

            {/* PIPELINE FUNNEL */}
            <section>
              <h2 className="text-zinc-100 text-base font-semibold mb-3">Pipeline</h2>
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 md:p-6">
                <div className="space-y-2">
                  {FUNNEL_STAGES.map((s) => {
                    const count = pipeline[s.key] || 0;
                    const widthPct = (count / maxFunnelCount) * 100;
                    return (
                      <button
                        key={s.key}
                        onClick={() => goToApplications(s.key)}
                        className="w-full text-left group"
                      >
                        <div className="flex items-center gap-3 py-1.5">
                          <div className={`shrink-0 w-28 md:w-32 text-xs md:text-sm font-medium ${s.text}`}>{s.label}</div>
                          <div className="flex-1 h-7 rounded bg-zinc-900/60 overflow-hidden relative">
                            <div
                              className={`absolute inset-y-0 left-0 ${s.bar} transition-all group-hover:brightness-110`}
                              style={{ width: `${Math.max(widthPct, count > 0 ? 4 : 0)}%` }}
                            />
                            <div className="relative px-3 h-full flex items-center text-xs font-medium tabular-nums text-zinc-50">
                              {count}
                            </div>
                          </div>
                          <ChevronRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 shrink-0" />
                        </div>
                      </button>
                    );
                  })}

                  {(pipeline["Rejected"] || 0) > 0 && (
                    <button
                      onClick={() => goToApplications("Rejected")}
                      className="w-full text-left group pt-2 mt-2 border-t border-zinc-800"
                    >
                      <div className="flex items-center gap-3 py-1">
                        <div className={`shrink-0 w-28 md:w-32 text-xs md:text-sm font-medium ${REJECTED.text}`}>{REJECTED.label}</div>
                        <div className="flex-1 h-6 rounded bg-zinc-900/60 overflow-hidden relative">
                          <div
                            className={`absolute inset-y-0 left-0 ${REJECTED.bar}`}
                            style={{ width: `${((pipeline["Rejected"] || 0) / maxFunnelCount) * 100}%` }}
                          />
                          <div className="relative px-3 h-full flex items-center text-xs font-medium tabular-nums text-zinc-50">
                            {pipeline["Rejected"] || 0}
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 shrink-0" />
                      </div>
                    </button>
                  )}
                </div>

                {/* Conversion rates */}
                {conversions.some(c => c.denominator > 0) && (
                  <div className="mt-5 pt-4 border-t border-zinc-800 grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {conversions.map((c) => (
                      <div key={c.from} className="text-xs">
                        <div className="text-zinc-500">{c.from} → {c.to}</div>
                        <div className="text-zinc-100 font-medium tabular-nums mt-0.5">
                          {c.rate}%
                          <span className="text-zinc-600 font-normal ml-1.5">
                            ({c.numerator}/{c.denominator})
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>

            {/* TOP OPPORTUNITIES + NEEDS ATTENTION (side-by-side on md) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Top opportunities */}
              <section>
                <h2 className="text-zinc-100 text-base font-semibold mb-3 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-emerald-400" />
                  Top opportunities
                </h2>
                {topOpportunities.length === 0 ? (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-5 text-zinc-500 text-sm">
                    No analysed opportunities yet. Add a job and run the AI fit analysis.
                  </div>
                ) : (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 divide-y divide-zinc-800/80">
                    {topOpportunities.map((j) => <JobMiniRow key={j.id} job={j} onClick={() => openJob(j.id)} />)}
                  </div>
                )}
              </section>

              {/* Needs attention */}
              <section>
                <h2 className="text-zinc-100 text-base font-semibold mb-3 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-400" />
                  Needs follow-up
                </h2>
                {needsAttention.length === 0 ? (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-5 text-zinc-500 text-sm">
                    Nothing waiting too long. Keep applying!
                  </div>
                ) : (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 divide-y divide-zinc-800/80">
                    {needsAttention.map((j) => (
                      <JobMiniRow key={j.id} job={j} onClick={() => openJob(j.id)} subtitle={`Applied ${daysAgo(j.created_at)} days ago`} />
                    ))}
                  </div>
                )}
              </section>
            </div>

            {/* RECENT ACTIVITY */}
            {recent.length > 0 && (
              <section>
                <h2 className="text-zinc-100 text-base font-semibold mb-3 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-zinc-400" />
                  Recent activity (last 7 days)
                </h2>
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 divide-y divide-zinc-800/80">
                  {recent.map((j) => (
                    <JobMiniRow key={j.id} job={j} onClick={() => openJob(j.id)} subtitle={`Added ${daysAgo(j.created_at)} days ago`} />
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </main>

      {showAddUrl && (
        <AddFromUrlModal
          onClose={() => setShowAddUrl(false)}
          onCreated={(job) => {
            setShowAddUrl(false);
            openJob(job.id);
          }}
          onSwitchToManual={() => {
            setShowAddUrl(false);
            setShowAddManual(true);
          }}
        />
      )}

      {showAddManual && (
        <JobFormModal
          onClose={() => setShowAddManual(false)}
          onSaved={(job) => {
            setShowAddManual(false);
            openJob(job.id);
          }}
        />
      )}
    </div>
  );
}

// ============ SMALL COMPONENTS ============

function StatCard({ icon: Icon, label, value, accent }: { icon: any; label: string; value: string; accent?: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
      <div className="flex items-center gap-2 text-zinc-500 text-[10px] uppercase tracking-wider">
        <Icon className="w-3.5 h-3.5" />
        {label}
      </div>
      <div className={`text-2xl font-semibold tabular-nums mt-1 ${accent || "text-zinc-100"}`}>
        {value}
      </div>
    </div>
  );
}

function JobMiniRow({ job, onClick, subtitle }: { job: JobListItem; onClick: () => void; subtitle?: string }) {
  const { letter, color } = logoFor(job.company);
  const c = job.suitability != null ? scoreColor(job.suitability) : null;
  return (
    <button onClick={onClick} className="w-full text-left px-4 py-3 hover:bg-zinc-800/30 active:bg-zinc-800/40 transition-colors">
      <div className="flex items-center gap-3">
        <div
          className="w-9 h-9 rounded-md flex items-center justify-center text-sm font-bold shrink-0"
          style={{ backgroundColor: `${color}20`, color, border: `1px solid ${color}30` }}
        >
          {letter}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-zinc-100 text-sm font-medium truncate">{job.role}</span>
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-zinc-500 text-xs truncate">{job.company}</span>
            {subtitle && (
              <>
                <span className="text-zinc-700">·</span>
                <span className="text-zinc-500 text-xs truncate">{subtitle}</span>
              </>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {job.suitability != null && c && (
            <div className={`px-2 py-1 rounded text-[11px] font-medium tabular-nums ${c.bg} ${c.text} ${c.border} border`}>
              {job.suitability}
            </div>
          )}
          <StatusPill status={job.status} />
          <ChevronRight className="w-4 h-4 text-zinc-600" />
        </div>
      </div>
    </button>
  );
}

function daysAgo(iso: string): number {
  return Math.floor((Date.now() - new Date(iso).getTime()) / DAY_MS);
}

export default function Page() {
  return (
    <AuthGuard>
      <PageInner />
    </AuthGuard>
  );
}
