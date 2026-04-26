"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Target, Save, ArrowLeft, User, Lock, CheckCircle2 } from "lucide-react";
import { api, type Profile } from "@/lib/api";
import { AuthGuard } from "@/components/AuthGuard";

const inputCls = "w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-blue-500/40";
const labelCls = "block text-[11px] uppercase tracking-wider text-zinc-500 mb-1.5";
const textareaCls = `${inputCls} font-mono text-xs leading-relaxed`;

function ProfilePageInner() {
  const [profile, setProfile] = useState<Profile>({});
  const [loaded, setLoaded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getProfile()
      .then((p) => { setProfile(p); setLoaded(true); })
      .catch((e) => { setError(e.message); setLoaded(true); });
  }, []);

  function set<K extends keyof Profile>(key: K, value: Profile[K]) {
    setProfile((p) => ({ ...p, [key]: value }));
    setSavedAt(null);
  }

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const saved = await api.saveProfile(profile);
      setProfile(saved);
      setSavedAt(new Date());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  if (!loaded) {
    return <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-zinc-500 text-sm">Loading profile...</div>;
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="h-14 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur sticky top-0 z-20 flex items-center justify-between px-5">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-zinc-500 hover:text-zinc-200 text-xs inline-flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" /> Back
          </Link>
          <div className="w-7 h-7 rounded-md bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
            <Target className="w-4 h-4 text-white" />
          </div>
          <span className="text-zinc-100 font-semibold text-sm tracking-tight">Profile</span>
        </div>
        <button
          onClick={save}
          disabled={saving}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-md bg-blue-500 hover:bg-blue-400 text-white text-xs font-medium disabled:opacity-50"
        >
          <Save className="w-3.5 h-3.5" />
          {saving ? "Saving..." : "Save profile"}
        </button>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8 space-y-8">
        {error && (
          <div className="p-3 rounded-md bg-red-500/10 border border-red-500/20 text-xs text-red-300">
            {error}
          </div>
        )}

        {savedAt && (
          <div className="p-3 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 inline-flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Saved at {savedAt.toLocaleTimeString()}
          </div>
        )}

        <p className="text-zinc-500 text-sm leading-relaxed">
          Your profile is the AI&apos;s view of you. Every analysis, suitability score, and tailored CV is generated from what you put here. Be specific.
        </p>

        {/* IDENTITY */}
        <section className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <User className="w-4 h-4 text-blue-400" />
            <h2 className="text-zinc-100 font-semibold text-sm">Identity</h2>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Full name</label>
              <input className={inputCls} value={profile.full_name || ""} onChange={(e) => set("full_name", e.target.value)} placeholder="Ko Saw" />
            </div>
            <div>
              <label className={labelCls}>Headline</label>
              <input className={inputCls} value={profile.headline || ""} onChange={(e) => set("headline", e.target.value)} placeholder="Senior Backend Engineer" />
            </div>
            <div>
              <label className={labelCls}>Location</label>
              <input className={inputCls} value={profile.location || ""} onChange={(e) => set("location", e.target.value)} placeholder="London, UK" />
            </div>
            <div>
              <label className={labelCls}>Email</label>
              <input className={inputCls} value={profile.email || ""} onChange={(e) => set("email", e.target.value)} placeholder="you@example.com" />
            </div>
            <div>
              <label className={labelCls}>Phone</label>
              <input className={inputCls} value={profile.phone || ""} onChange={(e) => set("phone", e.target.value)} placeholder="optional" />
            </div>
            <div>
              <label className={labelCls}>Website</label>
              <input className={inputCls} value={profile.website || ""} onChange={(e) => set("website", e.target.value)} placeholder="https://..." />
            </div>
            <div>
              <label className={labelCls}>LinkedIn</label>
              <input className={inputCls} value={profile.linkedin || ""} onChange={(e) => set("linkedin", e.target.value)} placeholder="linkedin.com/in/..." />
            </div>
            <div>
              <label className={labelCls}>GitHub</label>
              <input className={inputCls} value={profile.github || ""} onChange={(e) => set("github", e.target.value)} placeholder="github.com/..." />
            </div>
          </div>
        </section>

        {/* PUBLIC SECTIONS */}
        <section className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 space-y-4">
          <div>
            <h2 className="text-zinc-100 font-semibold text-sm">Professional content</h2>
            <p className="text-zinc-500 text-xs mt-1">These sections appear in tailored CVs and cover letters. Markdown is supported.</p>
          </div>

          <div>
            <label className={labelCls}>Professional summary</label>
            <textarea
              className={textareaCls}
              rows={5}
              value={profile.summary || ""}
              onChange={(e) => set("summary", e.target.value)}
              placeholder="A 2-3 paragraph elevator pitch. Mention your seniority, your domain, your favorite stack, and what you're looking for next. The AI weights this heavily."
            />
          </div>

          <div>
            <label className={labelCls}>Experience</label>
            <textarea
              className={textareaCls}
              rows={12}
              value={profile.experience || ""}
              onChange={(e) => set("experience", e.target.value)}
              placeholder={`### Senior Backend Engineer · CompanyCo · 2022–Present
- Owned the migration of the pricing service from Ruby to Elixir, processing 200M req/day with zero downtime.
- Led a team of 5 engineers shipping the new tax calculation engine.

### Backend Engineer · OldCompany · 2019–2022
- ...`}
            />
          </div>

          <div>
            <label className={labelCls}>Skills</label>
            <textarea
              className={textareaCls}
              rows={5}
              value={profile.skills || ""}
              onChange={(e) => set("skills", e.target.value)}
              placeholder={`**Languages:** Python (6y), Go (3y), TypeScript
**Infra:** AWS, Kubernetes, Postgres, Kafka, Terraform
**Domain:** Distributed systems, financial systems`}
            />
          </div>

          <div>
            <label className={labelCls}>Education</label>
            <textarea
              className={textareaCls}
              rows={3}
              value={profile.education || ""}
              onChange={(e) => set("education", e.target.value)}
              placeholder="BSc Computer Science, University of X, 2015"
            />
          </div>

          <div>
            <label className={labelCls}>Achievements (optional)</label>
            <textarea
              className={textareaCls}
              rows={4}
              value={profile.achievements || ""}
              onChange={(e) => set("achievements", e.target.value)}
              placeholder="Awards, conference talks, OSS contributions, patents..."
            />
          </div>
        </section>

        {/* PRIVATE TARGETING */}
        <section className="rounded-xl border border-amber-500/15 bg-amber-500/[0.03] p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-amber-400" />
            <h2 className="text-zinc-100 font-semibold text-sm">Private targeting</h2>
          </div>
          <p className="text-zinc-500 text-xs">
            The AI uses these for suitability scoring and salary negotiation calibration, but they will never appear in tailored CVs / cover letters / emails. Be candid.
          </p>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Target roles</label>
              <input className={inputCls} value={profile.target_roles || ""} onChange={(e) => set("target_roles", e.target.value)} placeholder="Senior backend, prefer staff IC over EM" />
            </div>
            <div>
              <label className={labelCls}>Target salary</label>
              <input className={inputCls} value={profile.target_salary || ""} onChange={(e) => set("target_salary", e.target.value)} placeholder="£180-220k London or fully remote" />
            </div>
          </div>

          <div>
            <label className={labelCls}>Deal breakers</label>
            <textarea className={inputCls} rows={2} value={profile.deal_breakers || ""} onChange={(e) => set("deal_breakers", e.target.value)} placeholder="No on-call rotation, no early-stage equity-only deals, no return-to-office" />
          </div>

          <div>
            <label className={labelCls}>Other notes for the AI</label>
            <textarea className={inputCls} rows={3} value={profile.private_notes || ""} onChange={(e) => set("private_notes", e.target.value)} placeholder="Strong on systems design, weaker on frontend. Currently employed, not actively desperate." />
          </div>
        </section>

        <div className="sticky bottom-4 flex justify-end">
          <button
            onClick={save}
            disabled={saving}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500 hover:bg-blue-400 text-white text-sm font-medium disabled:opacity-50 shadow-xl shadow-blue-500/30"
          >
            <Save className="w-4 h-4" />
            {saving ? "Saving..." : "Save profile"}
          </button>
        </div>
      </main>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <AuthGuard>
      <ProfilePageInner />
    </AuthGuard>
  );
}
