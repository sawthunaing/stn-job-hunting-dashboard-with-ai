"use client";
/**
 * Google Analytics 4 integration with GDPR-compliant consent flow.
 *
 * Behaviour:
 * - Reads NEXT_PUBLIC_GA_ID at build time. If unset, no analytics is loaded.
 *   (Private stack leaves this unset in compose, so no analytics there.)
 * - Shows a consent banner on first visit. Stores choice in a cookie
 *   (yes, ironically the consent storage is the only cookie we set without
 *   consent - this is standard practice and considered necessary for the
 *   consent mechanism itself).
 * - Only loads GA4 scripts AFTER consent is granted.
 * - Provides a `trackEvent` helper for custom events from anywhere.
 *
 * To enable on demo stack, set NEXT_PUBLIC_GA_ID at build time to your
 * GA4 measurement ID (format: "G-XXXXXXXXXX").
 */
import { useEffect, useState } from "react";
import Script from "next/script";

const CONSENT_COOKIE = "ksaw.analytics.consent";
const CONSENT_TTL_DAYS = 180;

const GA_ID = process.env.NEXT_PUBLIC_GA_ID;

type ConsentState = "granted" | "denied" | "unset";

function readConsent(): ConsentState {
  if (typeof document === "undefined") return "unset";
  const match = document.cookie.match(new RegExp(`(?:^|; )${CONSENT_COOKIE}=([^;]+)`));
  if (!match) return "unset";
  if (match[1] === "granted") return "granted";
  if (match[1] === "denied") return "denied";
  return "unset";
}

function writeConsent(state: "granted" | "denied") {
  const expires = new Date();
  expires.setDate(expires.getDate() + CONSENT_TTL_DAYS);
  document.cookie =
    `${CONSENT_COOKIE}=${state}; expires=${expires.toUTCString()}; path=/; samesite=lax`;
}

/** Custom event tracking. Safe to call even if GA isn't loaded. */
export function trackEvent(name: string, params: Record<string, unknown> = {}) {
  if (typeof window === "undefined") return;
  const w = window as unknown as { gtag?: (...args: unknown[]) => void };
  if (w.gtag) w.gtag("event", name, params);
}

export function Analytics() {
  const [consent, setConsent] = useState<ConsentState>("unset");

  useEffect(() => {
    setConsent(readConsent());
  }, []);

  // No GA configured at build time → render nothing
  if (!GA_ID) return null;

  return (
    <>
      {/* Only load GA4 after consent is granted */}
      {consent === "granted" && (
        <>
          <Script
            src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
            strategy="afterInteractive"
          />
          <Script id="ga-init" strategy="afterInteractive">{`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            window.gtag = gtag;
            gtag('js', new Date());
            gtag('config', '${GA_ID}', {
              anonymize_ip: true,
              cookie_flags: 'samesite=lax;secure'
            });
          `}</Script>
        </>
      )}

      {/* Consent banner shown only when state is unset */}
      {consent === "unset" && (
        <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:max-w-md z-50">
          <div className="rounded-lg border border-zinc-700 bg-zinc-900 shadow-2xl p-4 text-sm">
            <div className="text-zinc-200 font-medium mb-1">A note on cookies</div>
            <div className="text-zinc-400 text-xs leading-relaxed mb-3">
              This demo uses Google Analytics to understand how visitors use the
              app. No personal data is shared, IPs are anonymised. You can decline
              and the demo still works fully.
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => { writeConsent("granted"); setConsent("granted"); }}
                className="px-3 py-1.5 rounded-md bg-blue-500 hover:bg-blue-400 text-white text-xs font-medium"
              >
                Allow analytics
              </button>
              <button
                onClick={() => { writeConsent("denied"); setConsent("denied"); }}
                className="px-3 py-1.5 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium border border-zinc-700"
              >
                Decline
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
