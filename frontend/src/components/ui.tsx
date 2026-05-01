"use client";
import { type LucideIcon } from "lucide-react";

export const STATUS_STYLES: Record<string, { dot: string; text: string; bg: string; border: string }> = {
  New: { dot: "bg-blue-400", text: "text-blue-300", bg: "bg-blue-500/10", border: "border-blue-500/20" },
  Applied: { dot: "bg-amber-400", text: "text-amber-300", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  Interviewing: { dot: "bg-emerald-400", text: "text-emerald-300", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  Offer: { dot: "bg-violet-400", text: "text-violet-300", bg: "bg-violet-500/10", border: "border-violet-500/20" },
  Rejected: { dot: "bg-zinc-500", text: "text-zinc-400", bg: "bg-zinc-500/10", border: "border-zinc-500/20" },
};

export function scoreColor(score: number) {
  if (score >= 85) return { text: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/30", ring: "stroke-emerald-400" };
  if (score >= 70) return { text: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/30", ring: "stroke-amber-400" };
  return { text: "text-zinc-400", bg: "bg-zinc-500/10", border: "border-zinc-500/30", ring: "stroke-zinc-400" };
}

export function SuitabilityRing({ score, size = 40 }: { score: number; size?: number }) {
  const c = scoreColor(score);
  const r = (size - 6) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} strokeWidth="3" className="stroke-zinc-800" fill="none" />
        <circle
          cx={size / 2} cy={size / 2} r={r} strokeWidth="3" fill="none"
          className={c.ring}
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className={`absolute inset-0 flex items-center justify-center text-[10px] font-semibold tabular-nums ${c.text}`}>
        {score}
      </div>
    </div>
  );
}

export function StatusPill({ status }: { status: string }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.New;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium ${s.bg} ${s.text} ${s.border} border`}>
      <span className={`w-1 h-1 rounded-full ${s.dot}`} />
      {status}
    </span>
  );
}

export function MetaChip({ icon: Icon, label, accent }: { icon: LucideIcon; label: string; accent?: string }) {
  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-800/60 border border-zinc-700/60 text-xs">
      <Icon className={`w-3.5 h-3.5 ${accent || "text-zinc-400"}`} />
      <span className="text-zinc-300">{label}</span>
    </div>
  );
}

export function ActionButton({
  icon: Icon, label, primary, danger, onClick, loading, disabled, hidden,
}: {
  icon: LucideIcon; label: string; primary?: boolean; danger?: boolean; onClick?: () => void; loading?: boolean; disabled?: boolean; hidden?: boolean;
}) {
  if (hidden) return null;
  const cls = primary
    ? "bg-blue-500 hover:bg-blue-400 text-white shadow-lg shadow-blue-500/20"
    : danger
    ? "bg-red-500/10 hover:bg-red-500/20 text-red-300 border border-red-500/20"
    : "bg-zinc-800/60 hover:bg-zinc-800 text-zinc-200 border border-zinc-700/60";
  return (
    <button
      onClick={onClick}
      disabled={loading || disabled}
      className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed ${cls}`}
    >
      <Icon className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
      {label}
    </button>
  );
}

export function logoFor(company: string): { letter: string; color: string } {
  const palette = ["#635BFF", "#D97757", "#5E6AD2", "#F24E1E", "#3ECF8E", "#632CA6", "#FF6B6B", "#06B6D4"];
  const letter = (company || "?").charAt(0).toUpperCase();
  let h = 0;
  for (const ch of company) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return { letter, color: palette[h % palette.length] };
}
