import { describe, it, expect, beforeEach, vi } from "vitest";
import { api, getToken, setToken, clearToken, AuthError } from "@/lib/api";
import { jsonResponse, textResponse, mockFetch, TOKEN_KEY, API } from "../helpers";

describe("token storage", () => {
  it("round-trips through localStorage", () => {
    expect(getToken()).toBeNull();
    setToken("abc");
    expect(window.localStorage.getItem(TOKEN_KEY)).toBe("abc");
    expect(getToken()).toBe("abc");
    clearToken();
    expect(getToken()).toBeNull();
  });
});

describe("request helper", () => {
  beforeEach(() => setToken("tok"));

  it("sends bearer token and JSON content type", async () => {
    const fetch = mockFetch(jsonResponse({ username: "tester" }));
    await expect(api.me()).resolves.toEqual({ username: "tester" });
    const [url, init] = fetch.mock.calls[0];
    expect(url).toBe(`${API}/auth/me`);
    expect(init?.headers).toMatchObject({
      Authorization: "Bearer tok",
      "Content-Type": "application/json",
    });
    expect(init?.cache).toBe("no-store");
  });

  it("throws AuthError without calling fetch when no token", async () => {
    clearToken();
    const fetch = mockFetch();
    await expect(api.list()).rejects.toBeInstanceOf(AuthError);
    expect(fetch).not.toHaveBeenCalled();
  });

  it("clears the token and throws AuthError on 401", async () => {
    mockFetch(textResponse("invalid or expired token", 401));
    await expect(api.list()).rejects.toBeInstanceOf(AuthError);
    expect(getToken()).toBeNull();
  });

  it("throws status + body on other errors and keeps the token", async () => {
    mockFetch(textResponse('{"detail":"not found"}', 404));
    await expect(api.get(1)).rejects.toThrow('404: {"detail":"not found"}');
    expect(getToken()).toBe("tok");
  });

  it("returns undefined for 204", async () => {
    mockFetch(new Response(null, { status: 204 }));
    await expect(api.delete(3)).resolves.toBeUndefined();
  });
});

describe("api endpoints", () => {
  beforeEach(() => setToken("tok"));

  it("login stores the token and skips auth header", async () => {
    clearToken();
    const fetch = mockFetch(jsonResponse({ token: "new-token", username: "tester" }));
    await api.login("tester", "pw");
    const [url, init] = fetch.mock.calls[0];
    expect(url).toBe(`${API}/auth/login`);
    expect(init?.method).toBe("POST");
    expect(JSON.parse(init?.body as string)).toEqual({ username: "tester", password: "pw" });
    expect((init?.headers as Record<string, string>).Authorization).toBeUndefined();
    expect(getToken()).toBe("new-token");
  });

  it("login does not store anything on 401", async () => {
    clearToken();
    mockFetch(textResponse("invalid credentials", 401));
    await expect(api.login("tester", "bad")).rejects.toThrow("401");
    expect(getToken()).toBeNull();
  });

  it("logout clears the token", () => {
    api.logout();
    expect(getToken()).toBeNull();
  });

  it("demoInfo works without a token", async () => {
    clearToken();
    mockFetch(jsonResponse({ demo_mode: true }));
    await expect(api.demoInfo()).resolves.toEqual({ demo_mode: true });
  });

  it.each([
    [undefined, "/jobs"],
    [{ status: "All" }, "/jobs"],
    [{ status: "Applied" }, "/jobs?status_filter=Applied"],
    [{ q: "acme corp" }, "/jobs?q=acme+corp"],
    [{ status: "Offer", q: "x" }, "/jobs?status_filter=Offer&q=x"],
  ])("list(%j) -> %s", async (params, path) => {
    const fetch = mockFetch(jsonResponse([]));
    await api.list(params);
    expect(fetch.mock.calls[0][0]).toBe(`${API}${path}`);
  });

  it.each([
    ["create", () => api.create({ company: "A", role: "B" }), "/jobs", "POST", { company: "A", role: "B" }],
    ["createFromUrl", () => api.createFromUrl("https://x"), "/jobs/from-url", "POST", { url: "https://x" }],
    ["update", () => api.update(5, { status: "Applied" }), "/jobs/5", "PATCH", { status: "Applied" }],
    ["saveProfile", () => api.saveProfile({ full_name: "J" }), "/profile", "PUT", { full_name: "J" }],
    ["tailor", () => api.tailor(5, "cover_letter"), "/jobs/5/tailor", "POST", { doc_type: "cover_letter" }],
  ] as const)("%s sends the right method and body", async (_n, call, path, method, body) => {
    const fetch = mockFetch(jsonResponse({}));
    await call();
    const [url, init] = fetch.mock.calls[0];
    expect(url).toBe(`${API}${path}`);
    expect(init?.method).toBe(method);
    expect(JSON.parse(init?.body as string)).toEqual(body);
  });

  it.each(["analyze", "prep", "research"] as const)("%s POSTs to /jobs/:id/%s", async (name) => {
    const fetch = mockFetch(jsonResponse({}));
    await api[name](7);
    expect(fetch.mock.calls[0][0]).toBe(`${API}/jobs/7/${name}`);
    expect(fetch.mock.calls[0][1]?.method).toBe("POST");
  });
});

describe("downloadCV", () => {
  beforeEach(() => {
    setToken("tok");
    URL.createObjectURL = vi.fn(() => "blob:fake");
    URL.revokeObjectURL = vi.fn();
  });

  it("uses filename from Content-Disposition and triggers a download", async () => {
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    const fetch = mockFetch(
      new Response("PDFDATA", { status: 200, headers: { "Content-Disposition": 'attachment; filename="Jane_CV.pdf"' } }),
    );
    await expect(api.downloadCV(3, "pdf")).resolves.toBe("Jane_CV.pdf");
    expect(fetch.mock.calls[0][0]).toBe(`${API}/jobs/3/cv?format=pdf`);
    expect(fetch.mock.calls[0][1]?.headers).toEqual({ Authorization: "Bearer tok" });
    expect(click).toHaveBeenCalledOnce();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:fake");
  });

  it("falls back to cv.<format> when no header", async () => {
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    mockFetch(new Response("x", { status: 200 }));
    await expect(api.downloadCV(3, "docx")).resolves.toBe("cv.docx");
  });

  it("surfaces error text on failure", async () => {
    mockFetch(textResponse("No tailored CV yet", 400));
    await expect(api.downloadCV(3, "pdf")).rejects.toThrow("No tailored CV yet");
  });
});
