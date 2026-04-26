"use client";
import { useState } from "react";
import {
  CheckCircle2, AlertTriangle, BarChart3, Globe, Newspaper, Users,
  TrendingUp, Lightbulb, RefreshCw, Sparkles,
} from "lucide-react";
import { api, type JobDetail } from "@/lib/api";
import { ActionButton } from "../ui";

export function AnalysisTab({ job, onUpdate }: { job: JobDetail; onUpdate: (j: JobDetail) => void }) {
  const [analyzing, setAnalyzing] = useState(false);
  const [researching, setResearching] = useState(false);

  async function runAnalysis() {
    setAnalyzing(true);
    try { onUpdate(await api.analyze(job.id)); }
    catch (e: any) { alert(e.message); }
    finally { setAnalyzing(false); }
  }

  async function runResearch() {
    setResearching(true);
    try { onUpdate(await api.research(job.id)); }
    catch (e: any) { alert(e.message); }
    finally { setResearching(false); }
  }

  if (!job.analysis) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-12 text-center">
        <Sparkles className="w-10 h-10 text-zinc-700 mx-auto mb-3" />
        <div className="text-zinc-300 font-medium mb-1">No analysis yet</div>
        <div className="text-zinc-500 text-sm mb-5">
          Run AI analysis to surface strengths, gaps, market salary, and a negotiation range.
        </div>
        <ActionButton icon={Sparkles} label={analyzing ? "Analyzing..." : "Run AI Analysis"} primary onClick={runAnalysis} loading={analyzing} />
      </div>
    );
  }

  const a = job.analysis;
  const market = a.market_salary;
  const neg = a.negotiation;
  const currency = market?.currency || job.currency || "GBP";
  const symbol = currency === "USD" ? "$" : currency === "EUR" ? "€" : "£";

  const maxScale = Math.max(market?.p75 || 0, neg?.ceiling || 0, job.salary_max || 0) * 1.15 || 300;
  const pct = (v: number) => `${Math.min(100, (v / maxScale) * 100)}%`;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-emerald-500/15 bg-emerald-500/[0.03] p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/15 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <div className="text-zinc-100 text-sm font-semibold">Strengths</div>
              <div className="text-zinc-500 text-xs">Where you exceed or match</div>
            </div>
          </div>
          <div className="space-y-2.5">
            {a.strengths.map((s, i) => (
              <div key={i} className="flex items-start gap-3 p-2.5 rounded-lg bg-zinc-900/40 border border-zinc-800/60">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-zinc-200 text-sm font-medium">{s.skill}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      s.level === "Exceeds" ? "bg-emerald-500/15 text-emerald-300" : "bg-blue-500/15 text-blue-300"
                    }`}>
                      {s.level}
                    </span>
                  </div>
                  <div className="text-zinc-500 text-xs mt-1">{s.note}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-amber-500/15 bg-amber-500/[0.03] p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg bg-amber-500/15 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            </div>
            <div>
              <div className="text-zinc-100 text-sm font-semibold">Gaps</div>
              <div className="text-zinc-500 text-xs">Address proactively in your cover note</div>
            </div>
          </div>
          <div className="space-y-2.5">
            {a.gaps.length === 0 && (
              <div className="text-zinc-500 text-xs italic p-2">No significant gaps identified.</div>
            )}
            {a.gaps.map((g, i) => (
              <div key={i} className="flex items-start gap-3 p-2.5 rounded-lg bg-zinc-900/40 border border-zinc-800/60">
                <div className="flex-1 min-w-0">
                  <div className="text-zinc-200 text-sm font-medium">{g.skill}</div>
                  <div className="text-zinc-500 text-xs mt-1">{g.note}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {a.summary && (
        <div className="rounded-xl border border-blue-500/20 bg-blue-500/[0.04] p-4 flex items-start gap-3">
          <Sparkles className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
          <p className="text-sm text-zinc-200 leading-relaxed">{a.summary}</p>
        </div>
      )}

      {market && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-500/15 flex items-center justify-center">
                <BarChart3 className="w-4 h-4 text-blue-400" />
              </div>
              <div>
                <div className="text-zinc-100 text-sm font-semibold">Market Intelligence</div>
                <div className="text-zinc-500 text-xs">{market.source}</div>
              </div>
            </div>
            <button onClick={runAnalysis} disabled={analyzing} className="text-xs text-zinc-400 hover:text-zinc-200 inline-flex items-center gap-1 disabled:opacity-50">
              <RefreshCw className={`w-3 h-3 ${analyzing ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>

          <div className="space-y-1 mb-5">
            <div className="flex items-center justify-between text-[11px] text-zinc-500">
              <span>{symbol}0k</span>
              <span>{symbol}{Math.round(maxScale / 2)}k</span>
              <span>{symbol}{Math.round(maxScale)}k</span>
            </div>
            <div className="relative h-12 rounded-lg bg-zinc-950/60 border border-zinc-800 overflow-hidden">
              {job.salary_min != null && job.salary_max != null && (
                <div
                  className="absolute top-0 bottom-0 bg-blue-500/10 border-x border-blue-500/30"
                  style={{ left: pct(job.salary_min), width: `calc(${pct(job.salary_max)} - ${pct(job.salary_min)})` }}
                >
                  <div className="absolute top-1 left-1 text-[9px] text-blue-300 font-medium uppercase tracking-wide">Listed</div>
                </div>
              )}
              {[
                { v: market.p25, label: "p25" },
                { v: market.p50, label: "median" },
                { v: market.p75, label: "p75" },
              ].map((m, i) => (
                <div key={i} className="absolute top-0 bottom-0 w-px bg-zinc-600" style={{ left: pct(m.v) }}>
                  <div className="absolute top-0 left-1.5 text-[9px] text-zinc-400 font-medium whitespace-nowrap">
                    {m.label} · {symbol}{m.v}k
                  </div>
                </div>
              ))}
              {neg && (
                <div className="absolute top-0 bottom-0 w-0.5 bg-emerald-400" style={{ left: pct(neg.target) }}>
                  <div className="absolute bottom-0 -translate-x-1/2 left-1/2 text-[9px] text-emerald-300 font-semibold whitespace-nowrap">
                    ▼ target {symbol}{neg.target}k
                  </div>
                </div>
              )}
            </div>
          </div>

          {neg && (
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded-lg bg-zinc-950/40 border border-zinc-800">
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider">Floor</div>
                <div className="text-zinc-100 text-lg font-semibold tabular-nums mt-0.5">{symbol}{neg.floor}k</div>
                <div className="text-[10px] text-zinc-500 mt-0.5">walk-away</div>
              </div>
              <div className="p-3 rounded-lg bg-emerald-500/[0.06] border border-emerald-500/30">
                <div className="text-[10px] text-emerald-400 uppercase tracking-wider">Target</div>
                <div className="text-emerald-300 text-lg font-semibold tabular-nums mt-0.5">{symbol}{neg.target}k</div>
                <div className="text-[10px] text-emerald-500/80 mt-0.5">anchor here</div>
              </div>
              <div className="p-3 rounded-lg bg-zinc-950/40 border border-zinc-800">
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider">Ceiling</div>
                <div className="text-zinc-100 text-lg font-semibold tabular-nums mt-0.5">{symbol}{neg.ceiling}k</div>
                <div className="text-[10px] text-zinc-500 mt-0.5">stretch ask</div>
              </div>
            </div>
          )}
          {neg?.rationale && (
            <div className="text-[11px] text-zinc-500 mt-3 italic">{neg.rationale}</div>
          )}
        </div>
      )}

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-violet-500/15 flex items-center justify-center">
              <Globe className="w-4 h-4 text-violet-400" />
            </div>
            <div>
              <div className="text-zinc-100 text-sm font-semibold">Company Research</div>
              <div className="text-zinc-500 text-xs">{job.company_research ? "AI-generated" : "Not yet generated"}</div>
            </div>
          </div>
          <ActionButton
            icon={researching ? RefreshCw : Sparkles}
            label={researching ? "Researching..." : job.company_research ? "Refresh" : "Research"}
            onClick={runResearch}
            loading={researching}
          />
        </div>

        {job.company_research && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <Users className="w-3 h-3" /> Culture
                </div>
                <p className="text-zinc-300 text-xs leading-relaxed">{job.company_research.culture}</p>
              </div>
              <div>
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <TrendingUp className="w-3 h-3" /> Market position
                </div>
                <p className="text-zinc-300 text-xs leading-relaxed">{job.company_research.market}</p>
              </div>
            </div>

            {job.company_research.recent?.length > 0 && (
              <div className="mb-4">
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Newspaper className="w-3 h-3" /> Recent news
                </div>
                <div className="space-y-1.5">
                  {job.company_research.recent.map((n, i) => (
                    <div key={i} className="flex items-start gap-3 text-xs">
                      <span className="text-zinc-500 tabular-nums shrink-0 w-20">{n.date}</span>
                      <span className="text-zinc-300">{n.item}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {job.company_research.talking_points?.length > 0 && (
              <div className="pt-4 border-t border-zinc-800">
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Lightbulb className="w-3 h-3 text-amber-400" /> Talking points
                </div>
                <div className="space-y-2">
                  {job.company_research.talking_points.map((t, i) => (
                    <div key={i} className="flex items-start gap-2.5 p-2.5 rounded-lg bg-amber-500/[0.04] border border-amber-500/15">
                      <div className="w-4 h-4 rounded-full bg-amber-500/20 text-amber-300 flex items-center justify-center text-[10px] font-semibold shrink-0 mt-0.5">
                        {i + 1}
                      </div>
                      <span className="text-zinc-300 text-xs leading-relaxed">{t}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
