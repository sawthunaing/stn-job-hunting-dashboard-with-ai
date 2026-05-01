"use client";
import { useEffect, useMemo, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Target, MapPin, Briefcase, DollarSign, Clock, ExternalLink,
  Sparkles, Mail, MessageSquare, FileText, RefreshCw, Star, Pencil, Trash2,
  User, LogOut, Menu, ArrowLeft, Home,
} from "lucide-react";
import { api, type JobListItem, type JobDetail, type Status } from "@/lib/api";
import { Sidebar } from "@/components/Sidebar";
import { JobFormModal } from "@/components/JobFormModal";
import { AddFromUrlModal } from "@/components/AddFromUrlModal";
import { AuthGuard } from "@/components/AuthGuard";
import { StatusPill, MetaChip, ActionButton, scoreColor, logoFor } from "@/components/ui";
import { DemoBanner, useDemoMode } from "@/components/DemoMode";
import { DescriptionTab } from "@/components/tabs/DescriptionTab";
import { AnalysisTab } from "@/components/tabs/AnalysisTab";
import { InterviewPrepTab } from "@/components/tabs/InterviewPrepTab";
import { TailoredCVTab } from "@/components/tabs/TailoredCVTab";

type TabId = "description" | "analysis" | "prep" | "cv" | "notes";

const STATUS_CYCLE: Status[] = ["New", "Applied", "Interviewing", "Offer", "Rejected"];

function PageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialStatus = searchParams.get("status") || "All";
  const initialJobId = searchParams.get("job") ? parseInt(searchParams.get("job")!, 10) : null;
  const isDemo = false;
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(initialJobId);
  const [selected, setSelected] = useState<JobDetail | null>(null);
  const [tab, setTab] = useState<TabId>("description");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState(initialStatus);
  const [loading, setLoading] = useState(true);
  const [showAddUrl, setShowAddUrl] = useState(false);
  const [showAddManual, setShowAddManual] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [savingNotes, setSavingNotes] = useState(false);
  const [notesDraft, setNotesDraft] = useState("");
  // Mobile-only drawer state
  const [sidebarOpen, setSidebarOpen] = useState(false);
  // AI score filter
  const [minScore, setMinScore] = useState(0);
  const [includeUnscored, setIncludeUnscored] = useState(true);

  const refreshList = useCallback(async () => {
    try {
      const list = await api.list({ status: statusFilter, q: search });
      setJobs(list);
      if (list.length > 0 && (selectedId == null || !list.find((j) => j.id === selectedId))) {
        setSelectedId(list[0].id);
      } else if (list.length === 0) {
        setSelectedId(null);
        setSelected(null);
      }
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, search, selectedId]);

  useEffect(() => { refreshList(); }, [refreshList]);

  useEffect(() => {
    if (selectedId == null) { setSelected(null); return; }
    let cancelled = false;
    api.get(selectedId).then((j) => {
      if (!cancelled) { setSelected(j); setNotesDraft(j.notes || ""); }
    }).catch(console.error);
    return () => { cancelled = true; };
  }, [selectedId]);

  function applyDetail(j: JobDetail) {
    setSelected(j);
    setNotesDraft(j.notes || "");
    setJobs((prev) => prev.map((row) =>
      row.id === j.id
        ? {
            ...row,
            company: j.company, role: j.role, location: j.location, platform: j.platform,
            status: j.status, starred: j.starred, suitability: j.suitability,
          }
        : row
    ));
  }

  async function cycleStatus() {
    if (!selected) return;
    const idx = STATUS_CYCLE.indexOf(selected.status);
    const next = STATUS_CYCLE[(idx + 1) % STATUS_CYCLE.length];
    try { applyDetail(await api.update(selected.id, { status: next })); }
    catch (e: any) { alert(e.message); }
  }

  async function toggleStar() {
    if (!selected) return;
    try { applyDetail(await api.update(selected.id, { starred: !selected.starred })); }
    catch (e: any) { alert(e.message); }
  }

  async function reanalyze() {
    if (!selected) return;
    setAnalyzing(true);
    try { applyDetail(await api.analyze(selected.id)); }
    catch (e: any) { alert(e.message); }
    finally { setAnalyzing(false); }
  }

  async function saveNotes() {
    if (!selected) return;
    setSavingNotes(true);
    try { applyDetail(await api.update(selected.id, { notes: notesDraft })); }
    catch (e: any) { alert(e.message); }
    finally { setSavingNotes(false); }
  }

  async function deleteJob() {
    if (!selected) return;
    if (!confirm(`Delete the application for ${selected.role} at ${selected.company}?`)) return;
    try {
      await api.delete(selected.id);
      setSelectedId(null);
      setSelected(null);
      refreshList();
    } catch (e: any) { alert(e.message); }
  }

  const stats = useMemo(() => {
    const scored = jobs.filter(j => j.suitability != null);
    return {
      total: jobs.length,
      interviewing: jobs.filter((j) => j.status === "Interviewing").length,
      applied: jobs.filter((j) => j.status === "Applied").length,
      avgScore: scored.length
        ? Math.round(scored.reduce((a, j) => a + (j.suitability || 0), 0) / scored.length)
        : 0,
    };
  }, [jobs]);

  const c = selected?.suitability != null ? scoreColor(selected.suitability) : null;
  const symbol = selected?.currency === "USD" ? "$" : selected?.currency === "EUR" ? "€" : "£";
  const notesDirty = selected ? notesDraft !== (selected.notes || "") : false;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <DemoBanner />
      {/* HEADER - compact on mobile */}
      <header className="h-14 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur sticky top-0 z-20 flex items-center justify-between px-3 md:px-5">
        <div className="flex items-center gap-2 md:gap-3 min-w-0">
          {/* Hamburger - mobile only */}
          <button
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
            className="md:hidden p-2 -ml-2 text-zinc-300 hover:text-zinc-100 active:bg-zinc-800/40 rounded-md"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="w-7 h-7 rounded-md bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center shrink-0">
            <Target className="w-4 h-4 text-white" />
          </div>
          <span className="text-zinc-100 font-semibold text-sm tracking-tight truncate">
            <span className="md:hidden">Job Hunt</span>
            <span className="hidden md:inline">Ko Saw&apos;s Job Hunting Dashboard</span>
          </span>
          {/* Nav tabs */}
          <nav className="hidden md:flex items-center gap-1 ml-4">
            <Link href="/" className="px-3 py-1.5 rounded-md hover:bg-zinc-800/40 text-zinc-400 hover:text-zinc-200 text-xs font-medium">
              Overview
            </Link>
            <Link href="/applications" className="px-3 py-1.5 rounded-md bg-zinc-800/60 text-zinc-100 text-xs font-medium">
              Applications
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-2 md:gap-5 shrink-0">
          {/* Stats - desktop only */}
          <div className="hidden lg:flex items-center gap-5 text-xs">
            <div><span className="text-zinc-500">Active</span> <span className="text-zinc-100 font-medium tabular-nums ml-1">{stats.total}</span></div>
            <div><span className="text-zinc-500">Interviewing</span> <span className="text-emerald-400 font-medium tabular-nums ml-1">{stats.interviewing}</span></div>
            <div><span className="text-zinc-500">Applied</span> <span className="text-amber-400 font-medium tabular-nums ml-1">{stats.applied}</span></div>
            <div><span className="text-zinc-500">Avg fit</span> <span className="text-zinc-100 font-medium tabular-nums ml-1">{stats.avgScore || "—"}</span></div>
          </div>
          <Link
            href="/profile"
            className={`inline-flex items-center gap-1.5 px-2.5 py-2 rounded-md hover:bg-zinc-800/60 text-zinc-400 hover:text-zinc-200 text-xs ${isDemo ? "hidden" : ""}`}
            title="Profile"
          >
            <User className="w-4 h-4" />
            <span className="hidden md:inline">Profile</span>
          </Link>
          <button
            onClick={() => { api.logout(); router.replace("/login"); }}
            className={`inline-flex items-center gap-1.5 px-2.5 py-2 rounded-md hover:bg-zinc-800/60 text-zinc-400 hover:text-zinc-200 text-xs ${isDemo ? "hidden" : ""}`}
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden md:inline">Sign out</span>
          </button>
        </div>
      </header>

      <div className="flex h-[calc(100vh-3.5rem)] h-[calc(100dvh-3.5rem)]">
        <Sidebar
          jobs={jobs}
          selectedId={selectedId}
          onSelect={setSelectedId}
          search={search}
          onSearch={setSearch}
          statusFilter={statusFilter}
          onStatusChange={setStatusFilter}
          onAddClick={() => setShowAddUrl(true)}
          loading={loading}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          minScore={minScore}
          onMinScoreChange={setMinScore}
          includeUnscored={includeUnscored}
          onIncludeUnscoredChange={setIncludeUnscored}
          hideAdd={isDemo}
        />

        <main className="flex-1 overflow-y-auto bg-zinc-950">
          {!selected && !loading && (
            <div className="flex items-center justify-center h-full p-8 text-center">
              <div className="space-y-3">
                <div className="text-zinc-400 text-sm">No application selected</div>
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="md:hidden inline-flex items-center gap-2 px-4 py-2 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-sm"
                >
                  <Menu className="w-4 h-4" /> Open list
                </button>
              </div>
            </div>
          )}

          {selected && (
            <div className="max-w-5xl mx-auto px-4 md:px-8 py-4 md:py-6">
              {/* MOBILE BACK BUTTON */}
              <button
                onClick={() => setSidebarOpen(true)}
                className="md:hidden inline-flex items-center gap-1.5 text-zinc-400 hover:text-zinc-200 text-sm mb-4 -ml-2 px-2 py-1"
              >
                <ArrowLeft className="w-4 h-4" /> All applications
              </button>

              {/* JOB HEADER - stacks on mobile */}
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 md:gap-6 mb-5">
                <div className="flex items-start gap-3 md:gap-4 min-w-0">
                  {(() => {
                    const { letter, color } = logoFor(selected.company);
                    return (
                      <div
                        className="w-12 h-12 md:w-14 md:h-14 rounded-xl flex items-center justify-center text-xl md:text-2xl font-bold shrink-0"
                        style={{ backgroundColor: `${color}20`, color, border: `1px solid ${color}40` }}
                      >
                        {letter}
                      </div>
                    );
                  })()}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="text-zinc-400 text-sm">{selected.company}</span>
                      <span className="text-zinc-700">·</span>
                      <button onClick={cycleStatus} title="Tap to cycle status" className="touch-manipulation">
                        <StatusPill status={selected.status} />
                      </button>
                    </div>
                    <h1 className="text-xl md:text-2xl font-semibold text-zinc-50 tracking-tight leading-tight break-words">{selected.role}</h1>
                    <div className="flex items-center gap-2 mt-3 flex-wrap">
                      {selected.location && <MetaChip icon={MapPin} label={selected.location} />}
                      {selected.work_type && <MetaChip icon={Briefcase} label={selected.work_type} />}
                      {selected.salary_min != null && selected.salary_max != null && (
                        <MetaChip icon={DollarSign} label={`${symbol}${selected.salary_min}–${selected.salary_max}k`} accent="text-emerald-400" />
                      )}
                      <MetaChip icon={Clock} label={`Added ${new Date(selected.created_at).toLocaleDateString()}`} />
                      {selected.platform && <MetaChip icon={ExternalLink} label={selected.platform} />}
                    </div>
                  </div>
                </div>

                {selected.suitability != null && c && (
                  <div className={`rounded-xl border ${c.border} ${c.bg} p-3 md:p-4 shrink-0 text-center md:min-w-[140px] flex md:block items-center gap-3 md:gap-0`}>
                    <div className="md:hidden flex-shrink-0">
                      <div className={`text-3xl font-semibold tabular-nums ${c.text} leading-none`}>{selected.suitability}</div>
                    </div>
                    <div className="flex-1 md:flex-initial">
                      <div className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1 flex items-center justify-center gap-1">
                        <Sparkles className="w-3 h-3" /> Suitability
                      </div>
                      <div className={`hidden md:block text-4xl font-semibold tabular-nums ${c.text} leading-none`}>{selected.suitability}</div>
                      <div className="text-[10px] text-zinc-500 mt-1 hidden md:block">/ 100 · AI-scored</div>
                      <div className="text-[10px] text-zinc-500 md:hidden">/ 100 · AI-scored</div>
                    </div>
                  </div>
                )}
              </div>

              {/* ACTION BUTTONS - wrap better on mobile */}
              <div className="flex items-center gap-2 mb-6 flex-wrap pb-5 border-b border-zinc-800/80">
                {selected.source_url && (
                  <a
                    href={selected.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium bg-zinc-800/60 hover:bg-zinc-800 active:bg-zinc-700 text-zinc-200 border border-zinc-700/60"
                  >
                    <ExternalLink className="w-4 h-4" /> <span className="hidden sm:inline">Open Listing</span><span className="sm:hidden">Open</span>
                  </a>
                )}
                <ActionButton icon={RefreshCw} label={analyzing ? "Analyzing..." : "AI Re-analyze"} onClick={reanalyze} loading={analyzing} disabled={isDemo} hidden={isDemo} />
                <ActionButton icon={FileText} label="Tailored CV" primary onClick={() => setTab("cv")} />
                <ActionButton icon={MessageSquare} label="Prep" onClick={() => setTab("prep")} />
                <ActionButton icon={Pencil} label="Edit" onClick={() => setShowEdit(true)} hidden={isDemo} />
                <ActionButton icon={Trash2} label="Delete" danger onClick={deleteJob} hidden={isDemo} />
                <div className="ml-auto flex items-center gap-1">
                  <button
                    onClick={toggleStar}
                    className={`w-10 h-10 rounded-md flex items-center justify-center hover:bg-zinc-800/60 active:bg-zinc-800/80 ${
                      selected.starred ? "text-amber-400" : "text-zinc-400"
                    }`}
                    title={selected.starred ? "Unstar" : "Star"}
                  >
                    <Star className="w-5 h-5" fill={selected.starred ? "currentColor" : "none"} />
                  </button>
                </div>
              </div>

              {/* TABS - horizontally scrollable on mobile */}
              <div className="flex items-center gap-1 border-b border-zinc-800/80 mb-6 overflow-x-auto scrollbar-hide -mx-4 px-4 md:mx-0 md:px-0">
                {([
                  ["description", "Description"],
                  ["analysis", "Analysis"],
                  ["prep", "Interview Prep"],
                  ["cv", "Tailored CV"],
                  ["notes", "Notes"],
                ] as const).map(([id, label]) => (
                  <button
                    key={id}
                    onClick={() => setTab(id)}
                    className={`relative px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap shrink-0 ${
                      tab === id ? "text-zinc-100" : "text-zinc-500 hover:text-zinc-300"
                    }`}
                  >
                    {label}
                    {tab === id && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 rounded-t-full" />}
                  </button>
                ))}
              </div>

              <div className="pb-12">
                {tab === "description" && <DescriptionTab job={selected} />}
                {tab === "analysis" && <AnalysisTab job={selected} onUpdate={applyDetail} />}
                {tab === "prep" && <InterviewPrepTab job={selected} onUpdate={applyDetail} />}
                {tab === "cv" && <TailoredCVTab job={selected} onUpdate={applyDetail} />}
                {tab === "notes" && (
                  <div className="space-y-3">
                    <textarea
                      value={notesDraft}
                      onChange={(e) => setNotesDraft(e.target.value)}
                      placeholder="Recruiter contacts, interview prep ideas, salary research, follow-up reminders..."
                      className="w-full bg-zinc-900/40 border border-zinc-800 rounded-lg px-4 py-3 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-700 leading-relaxed"
                      rows={15}
                    />
                    <div className="flex items-center justify-between">
                      <div className="text-[11px] text-zinc-500">
                        {notesDirty ? "Unsaved changes" : "Saved"}
                      </div>
                      <button
                        onClick={saveNotes}
                        disabled={!notesDirty || savingNotes}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-blue-500 hover:bg-blue-400 active:bg-blue-600 text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        {savingNotes ? "Saving..." : "Save notes"}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>

      {showAddUrl && (
        <AddFromUrlModal
          onClose={() => setShowAddUrl(false)}
          onCreated={(job) => {
            setShowAddUrl(false);
            refreshList();
            setSelectedId(job.id);
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
            refreshList();
            setSelectedId(job.id);
          }}
        />
      )}

      {showEdit && selected && (
        <JobFormModal
          editing={selected}
          onClose={() => setShowEdit(false)}
          onSaved={(job) => {
            setShowEdit(false);
            applyDetail(job);
            refreshList();
          }}
        />
      )}
    </div>
  );
}

export default function Page() {
  return (
    <AuthGuard>
      <PageInner />
    </AuthGuard>
  );
}
