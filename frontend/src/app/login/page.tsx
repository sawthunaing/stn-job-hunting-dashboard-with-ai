"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Target, LogIn } from "lucide-react";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.login(username, password);
      router.push("/");
    } catch (err: any) {
      const msg = err?.message || "login failed";
      // Friendlier message for the most common case
      if (msg.includes("401")) setError("Invalid username or password");
      else setError(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className="w-9 h-9 rounded-md bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
            <Target className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="text-zinc-100 font-semibold text-base tracking-tight">Ko Saw&apos;s Job Hunting Dashboard</div>
            <div className="text-zinc-500 text-xs">Sign in to continue</div>
          </div>
        </div>

        <form onSubmit={submit} className="space-y-4 bg-zinc-900/40 border border-zinc-800 rounded-xl p-6">
          <div>
            <label className="block text-[11px] uppercase tracking-wider text-zinc-500 mb-1.5">Username</label>
            <input
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-blue-500/40"
              autoComplete="username"
            />
          </div>
          <div>
            <label className="block text-[11px] uppercase tracking-wider text-zinc-500 mb-1.5">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-blue-500/40"
              autoComplete="current-password"
            />
          </div>

          {error && (
            <div className="p-3 rounded-md bg-red-500/10 border border-red-500/20 text-xs text-red-300">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={busy || !username || !password}
            className="w-full inline-flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-400 text-white text-sm font-medium px-4 py-2 rounded-md disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20"
          >
            <LogIn className="w-4 h-4" />
            {busy ? "Signing in..." : "Sign in"}
          </button>

          <div className="text-[11px] text-zinc-600 text-center pt-2">
            Default credentials are set in <code className="text-zinc-400">backend/config.json</code>
          </div>
        </form>
      </div>
    </div>
  );
}
