// API client with username/password auth.

export type Status = "New" | "Applied" | "Interviewing" | "Offer" | "Rejected";
export type WorkType = "Remote" | "Hybrid" | "Onsite";

export interface JobListItem {
  id: number;
  company: string;
  role: string;
  location: string | null;
  platform: string | null;
  status: Status;
  suitability: number | null;
  starred: boolean;
  created_at: string;
}

export interface AnalysisStrength { skill: string; level: "Exceeds" | "Match"; note: string; }
export interface AnalysisGap { skill: string; note: string; }
export interface MarketSalary { p25: number; p50: number; p75: number; currency: string; source: string; }
export interface Negotiation { floor: number; target: number; ceiling: number; rationale: string; }
export interface Analysis {
  suitability: number;
  summary: string;
  strengths: AnalysisStrength[];
  gaps: AnalysisGap[];
  market_salary: MarketSalary;
  negotiation: Negotiation;
}

export interface PrepQuestion { q: string; why: string; framework?: string; }
export interface InterviewPrep { technical: PrepQuestion[]; behavioral: PrepQuestion[]; }

export interface CompanyResearch {
  culture: string;
  market: string;
  recent: { date: string; item: string }[];
  talking_points: string[];
}

export interface TailoredDoc {
  content: string;
  ats_match_pct?: number;
  keywords_matched?: string[];
  keywords_missing?: string[];
  suggestions?: string[];
}

export interface JobDetail {
  id: number;
  company: string;
  role: string;
  location: string | null;
  work_type: WorkType | null;
  platform: string | null;
  source_url: string | null;
  description: string | null;
  salary_min: number | null;
  salary_max: number | null;
  currency: string | null;
  status: Status;
  notes: string | null;
  starred: boolean;
  applied_date: string | null;
  suitability: number | null;
  analysis: Analysis | null;
  interview_prep: InterviewPrep | null;
  company_research: CompanyResearch | null;
  tailored_docs: Record<string, TailoredDoc> | null;
  created_at: string;
  updated_at: string;
  analyzed_at: string | null;
}

export interface JobInput {
  company: string;
  role: string;
  location?: string;
  work_type?: WorkType;
  platform?: string;
  source_url?: string;
  description?: string;
  salary_min?: number;
  salary_max?: number;
  currency?: string;
  status?: Status;
  notes?: string;
}

export interface Profile {
  full_name?: string | null;
  headline?: string | null;
  location?: string | null;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  linkedin?: string | null;
  github?: string | null;
  hackerrank?: string | null;
  title?: string | null;
  summary?: string | null;
  experience?: string | null;
  skills?: string | null;
  education?: string | null;
  achievements?: string | null;
  target_roles?: string | null;
  target_salary?: string | null;
  deal_breakers?: string | null;
  private_notes?: string | null;
  updated_at?: string | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "ksaw.token";

// --- Token management ---
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(t: string) {
  window.localStorage.setItem(TOKEN_KEY, t);
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

export class AuthError extends Error {
  constructor() { super("not authenticated"); this.name = "AuthError"; }
}

async function req<T>(path: string, init: RequestInit = {}, options: { skipAuth?: boolean } = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> || {}),
  };
  if (!options.skipAuth) {
    const tok = getToken();
    if (!tok) throw new AuthError();
    headers["Authorization"] = `Bearer ${tok}`;
  }

  const res = await fetch(`${API_URL}${path}`, { ...init, headers, cache: "no-store" });

  if (res.status === 401 && !options.skipAuth) {
    clearToken();
    throw new AuthError();
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text || res.statusText}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // --- Auth ---
  login: async (username: string, password: string) => {
    const r = await req<{ token: string; username: string }>(
      "/auth/login",
      { method: "POST", body: JSON.stringify({ username, password }) },
      { skipAuth: true }
    );
    setToken(r.token);
    return r;
  },
  logout: () => clearToken(),
  me: () => req<{ username: string }>("/auth/me"),

  // --- Profile ---
  getProfile: () => req<Profile>("/profile"),
  saveProfile: (p: Profile) => req<Profile>("/profile", { method: "PUT", body: JSON.stringify(p) }),

  // --- Jobs ---
  list: (params?: { status?: string; q?: string }) => {
    const qs = new URLSearchParams();
    if (params?.status && params.status !== "All") qs.set("status_filter", params.status);
    if (params?.q) qs.set("q", params.q);
    const s = qs.toString();
    return req<JobListItem[]>(`/jobs${s ? "?" + s : ""}`);
  },
  get: (id: number) => req<JobDetail>(`/jobs/${id}`),
  create: (payload: JobInput) =>
    req<JobDetail>("/jobs", { method: "POST", body: JSON.stringify(payload) }),
  createFromUrl: (url: string) =>
    req<JobDetail>("/jobs/from-url", { method: "POST", body: JSON.stringify({ url }) }),
  update: (id: number, patch: Partial<JobDetail>) =>
    req<JobDetail>(`/jobs/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
  delete: (id: number) => req<void>(`/jobs/${id}`, { method: "DELETE" }),
  analyze: (id: number) => req<JobDetail>(`/jobs/${id}/analyze`, { method: "POST" }),
  prep: (id: number) => req<JobDetail>(`/jobs/${id}/prep`, { method: "POST" }),
  research: (id: number) => req<JobDetail>(`/jobs/${id}/research`, { method: "POST" }),
  tailor: (id: number, doc_type: "cv" | "cover_letter" | "recruiter_email") =>
    req<JobDetail>(`/jobs/${id}/tailor`, {
      method: "POST",
      body: JSON.stringify({ doc_type }),
    }),

  /**
   * Download the AI-tailored CV as PDF or DOCX. Triggers a browser download
   * via a temporary anchor click. Returns the suggested filename for display.
   */
  downloadCV: async (id: number, format: "pdf" | "docx"): Promise<string> => {
    const token = typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;
    const r = await fetch(`${API_URL}/jobs/${id}/cv?format=${format}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!r.ok) {
      const text = await r.text();
      try {
        const j = JSON.parse(text);
        throw new Error(j.detail || `HTTP ${r.status}`);
      } catch {
        throw new Error(text || `HTTP ${r.status}`);
      }
    }

    // Pull filename from Content-Disposition if present
    let filename = `cv.${format}`;
    const cd = r.headers.get("Content-Disposition") || "";
    const m = cd.match(/filename="?([^"]+)"?/i);
    if (m) filename = m[1];

    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    return filename;
  },

  /** Public endpoint - returns { demo_mode: boolean } so the UI can adapt. */
  demoInfo: () => req<{ demo_mode: boolean }>("/demo-info"),
};
