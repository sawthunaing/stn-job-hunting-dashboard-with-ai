import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { router } from "./router";
import { AuthGuard } from "@/components/AuthGuard";
import { jsonResponse, textResponse, mockFetch, TOKEN_KEY, API } from "../helpers";

function renderGuard() {
  return render(<AuthGuard><div>Secret dashboard</div></AuthGuard>);
}

describe("AuthGuard + API client", () => {
  beforeEach(() => router.replace.mockReset());

  it("shows a loading state, then children when the token is valid", async () => {
    window.localStorage.setItem(TOKEN_KEY, "good");
    const fetch = mockFetch(jsonResponse({ demo_mode: false }), jsonResponse({ username: "tester" }));
    renderGuard();
    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(screen.queryByText("Secret dashboard")).not.toBeInTheDocument();

    expect(await screen.findByText("Secret dashboard")).toBeInTheDocument();
    expect(fetch.mock.calls.map((c) => c[0])).toEqual([`${API}/demo-info`, `${API}/auth/me`]);
    expect(router.replace).not.toHaveBeenCalled();
  });

  it("redirects to /login when there is no token", async () => {
    const fetch = mockFetch(jsonResponse({ demo_mode: false }));
    renderGuard();
    await waitFor(() => expect(router.replace).toHaveBeenCalledWith("/login"));
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(screen.queryByText("Secret dashboard")).not.toBeInTheDocument();
  });

  it("redirects to /login and drops the token when the server rejects it", async () => {
    window.localStorage.setItem(TOKEN_KEY, "expired");
    mockFetch(jsonResponse({ demo_mode: false }), textResponse("invalid or expired token", 401));
    renderGuard();
    await waitFor(() => expect(router.replace).toHaveBeenCalledWith("/login"));
    expect(window.localStorage.getItem(TOKEN_KEY)).toBeNull();
  });

  it("lets anonymous visitors in when the backend is in demo mode", async () => {
    const fetch = mockFetch(jsonResponse({ demo_mode: true }));
    renderGuard();
    expect(await screen.findByText("Secret dashboard")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(router.replace).not.toHaveBeenCalled();
  });

  it("falls back to normal auth if /demo-info is unreachable", async () => {
    window.localStorage.setItem(TOKEN_KEY, "good");
    const fetch = mockFetch();
    fetch.mockRejectedValueOnce(new TypeError("Failed to fetch")).mockResolvedValueOnce(jsonResponse({ username: "tester" }));
    renderGuard();
    expect(await screen.findByText("Secret dashboard")).toBeInTheDocument();
  });
});
