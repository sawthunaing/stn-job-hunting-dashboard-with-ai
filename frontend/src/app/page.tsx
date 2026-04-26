"use client";
import { useEffect, useMemo, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Target, MapPin, Briefcase, DollarSign, Clock, ExternalLink,
  Sparkles, Mail, MessageSquare, FileText, RefreshCw, Star, Pencil, Trash2,
  User, LogOut,
} from "lucide-react";
import { api, type JobListItem, type JobDetail, type Status } from "@/lib/api";
import { Sidebar } from "@/components/Sidebar";
import { JobFormModal } from "@/components/JobFormModal";
import { AddFromUrlModal } from "@/components/AddFromUrlModal";
import { AuthGuard } from "@/components/AuthGuard";
import { StatusPill, MetaChip, ActionButton, scoreColor, logoFor } from "@/components/ui";
import { DescriptionTab } from "@/components/tabs/DescriptionTab";
import { AnalysisTab } from "@/components/tabs/AnalysisTab";
import { InterviewPrepTab } from "@/components/tabs/InterviewPrepTab";
import { TailoredCVTab } from "@/components/tabs/TailoredCVTab";

type TabId = "description" | "analysis" | "prep" | "cv" | "notes";

const STATUS_CYCLE: Status[] = ["New", "Applied", "Interviewing", "Offer", "Rejected"];

function PageInner() {
  const router = useRouter();
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selected, setSelected] = useState<JobDetail | null>(null);
  const [tab, setTab] = useState<TabId>("description");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [loading, setLoading] = useState(true);
  const [showAddUrl, setShowAddUrl] = useState(false);
  const [showAddManual, setShowAddManual] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [savingNotes, setSavingNotes] = useState(false);
  const [notesDraft, setNotesDraft] = useState("");

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
      <header className="h-14 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur sticky top-0 z-20 flex items-center justify-between px-5">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-md bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
            <Target className="w-4 h-4 text-white" />
          </div>
          <span className="text-zinc-100 font-semibold text-sm tracking-tight">Ko Saw&apos;s Job Hunting Dashboard</span>
        </div>
        <div className="flex items-center gap-5">
          <div className="hidden md:flex items-center gap-5 text-xs">
            <div><span className="text-zinc-500">Active</span> <span className="text-zinc-100 font-medium tabular-nums ml-1">{stats.total}</span></div>
            <div><span className="text-zinc-500">Interviewing</span> <span className="text-emerald-400 font-medium tabular-nums ml-1">{stats.interviewing}</span></div>
            <div><span className="text-zinc-500">Applied</span> <span className="text-amber-400 font-medium tabular-nums ml-1">{stats.applied}</span></div>
            <div><span className="text-zinc-500">Avg fit</span> <span className="text-zinc-100 font-medium tabular-nums ml-1">{stats.avgScore || "—"}</span></div>
          </div>
          <Link
            href="/profile"
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md hover:bg-zinc-800/60 text-zinc-400 hover:text-zinc-200 text-xs"
            title="Profile"
          >
            <User className="w-3.5 h-3.5" />
            Profile
          </Link>
          <button
            onClick={() => { api.logout(); router.replace("/login"); }}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md hover:bg-zinc-800/60 text-zinc-400 hover:text-zinc-200 text-xs"
            title="Sign out"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign out
          </button>
        </div>
      </header>

      <div className="flex h-[calc(100vh-3.5rem)]">
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
        />

        <main className="flex-1 overflow-y-auto">
          {!selected && !loading && (
            <div className="h-full flex items-center justify-center text-zinc-500 text-sm">
              {jobs.length === 0 ? "Click + Add to track your first application." : "Select a job from the sidebar."}
            </div>
          )}

          {selected && (
            <div className="max-w-5xl mx-auto px-8 py-6">
              <div className="flex items-start justify-between gap-6 mb-5">
                <div className="flex items-start gap-4 min-w-0">
                  {(() => {
                    const { letter, color } = logoFor(selected.company);
                    return (
                      <div
                        className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl font-bold shrink-0"
                        style={{ backgroundColor: `${color}20`, color, border: `1px solid ${color}40` }}
                      >
                        {letter}
                      </div>
                    );
                  })()}
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-zinc-400 text-sm">{selected.company}</span>
                      <span className="text-zinc-700">·</span>
                      <button onClick={cycleStatus} title="Click to cycle status">
                        <StatusPill status={selected.status} />
                      </button>
                    </div>
                    <h1 className="text-2xl font-semibold text-zinc-50 tracking-tight leading-tight">{selected.role}</h1>
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
                  <div className={`rounded-xl border ${c.border} ${c.bg} p-4 shrink-0 text-center min-w-[140px]`}>
                    <div className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1 flex items-center justify-center gap-1">
                      <Sparkles className="w-3 h-3" /> Suitability
                    </div>
                    <div className={`text-4xl font-semibold tabular-nums ${c.text} leading-none`}>{selected.suitability}</div>
                    <div className="text-[10px] text-zinc-500 mt-1">/ 100 · AI-scored</div>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2 mb-6 flex-wrap pb-5 border-b border-zinc-800/80">
                {selected.source_url && (
                  <a
                    href={selected.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium bg-zinc-800/60 hover:bg-zinc-800 text-zinc-200 border border-zinc-700/60"
                  >
                    <ExternalLink className="w-4 h-4" /> Open Listing
                  </a>
                )}
                <ActionButton icon={RefreshCw} label={analyzing ? "Analyzing..." : "AI Re-analyze"} onClick={reanalyze} loading={analyzing} />
                <ActionButton icon={Mail} label="Draft Email" onClick={() => setTab("cv")} />
                <ActionButton icon={MessageSquare} label="Interview Prep" onClick={() => setTab("prep")} />
                <ActionButton icon={FileText} label="Tailored CV" primary onClick={() => setTab("cv")} />
                <ActionButton icon={Pencil} label="Edit" onClick={() => setShowEdit(true)} />
                <ActionButton icon={Trash2} label="Delete" danger onClick={deleteJob} />
                <div className="ml-auto flex items-center gap-1">
                  <button
                    onClick={toggleStar}
                    className={`w-8 h-8 rounded-md flex items-center justify-center hover:bg-zinc-800/60 ${
                      selected.starred ? "text-amber-400" : "text-zinc-400"
                    }`}
                    title={selected.starred ? "Unstar" : "Star"}
                  >
                    <Star className="w-4 h-4" fill={selected.starred ? "currentColor" : "none"} />
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-1 border-b border-zinc-800/80 mb-6">
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
                    className={`relative px-4 py-2.5 text-sm font-medium transition-colors ${
                      tab === id ? "text-zinc-100" : "text-zinc-500 hover:text-zinc-300"
                    }`}
                  >
                    {label}
                    {tab === id && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 rounded-t-full" />}
                  </button>
                ))}
              </div>

              <div>
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
                      rows={20}
                    />
                    <div className="flex items-center justify-between">
                      <div className="text-[11px] text-zinc-500">
                        {notesDirty ? "Unsaved changes" : "Saved"}
                      </div>
                      <button
                        onClick={saveNotes}
                        disabled={!notesDirty || savingNotes}
                        className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-md bg-blue-500 hover:bg-blue-400 text-white text-xs font-medium disabled:opacity-40 disabled:cursor-not-allowed"
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
