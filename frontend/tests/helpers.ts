import { vi } from "vitest";

/** Build a minimal fetch Response. */
export function jsonResponse(body: unknown, status = 200, headers: Record<string, string> = {}) {
  return new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

export function textResponse(text: string, status: number) {
  return new Response(text, { status });
}

/** Replace global fetch with a mock and return it. */
export function mockFetch(...responses: Response[]) {
  const fn = vi.fn<typeof fetch>();
  for (const r of responses) fn.mockResolvedValueOnce(r);
  vi.stubGlobal("fetch", fn);
  return fn;
}

export const TOKEN_KEY = "ksaw.token";
export const API = "http://localhost:8000";
