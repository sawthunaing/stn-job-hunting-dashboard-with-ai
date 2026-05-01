"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getToken } from "@/lib/api";

/**
 * Wrap protected pages with this. It checks for a token on mount and
 * redirects to /login if missing or invalid.
 *
 * In demo mode the backend exposes read endpoints publicly, so we skip
 * the auth check entirely.
 *
 * Renders nothing while verifying so we never flash protected content.
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    api.demoInfo()
      .then((info) => {
        if (cancelled) return;
        if (info.demo_mode) {
          // Demo mode - no login needed, render immediately
          setReady(true);
          return;
        }
        // Normal mode - require token
        if (!getToken()) {
          router.replace("/login");
          return;
        }
        api.me()
          .then(() => { if (!cancelled) setReady(true); })
          .catch(() => { if (!cancelled) router.replace("/login"); });
      })
      .catch(() => {
        // demo-info call failed (server unreachable) - fall back to normal auth flow
        if (cancelled) return;
        if (!getToken()) {
          router.replace("/login");
          return;
        }
        api.me()
          .then(() => { if (!cancelled) setReady(true); })
          .catch(() => { if (!cancelled) router.replace("/login"); });
      });

    return () => { cancelled = true; };
  }, [router]);

  if (!ready) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-zinc-500 text-sm">
        Loading...
      </div>
    );
  }
  return <>{children}</>;
}
