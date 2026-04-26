"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getToken } from "@/lib/api";

/**
 * Wrap protected pages with this. It checks for a token on mount and
 * redirects to /login if missing or invalid.
 *
 * Renders nothing while verifying so we never flash protected content.
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    // Quick verify the token is still valid server-side
    api.me()
      .then(() => setReady(true))
      .catch(() => router.replace("/login"));
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
