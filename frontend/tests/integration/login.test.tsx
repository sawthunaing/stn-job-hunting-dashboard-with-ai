import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { router } from "./router";
import LoginPage from "@/app/login/page";
import { jsonResponse, textResponse, mockFetch, TOKEN_KEY, API } from "../helpers";

// The form's <label>s aren't tied to their inputs, so locate fields by autocomplete hint.
const usernameInput = () => document.querySelector<HTMLInputElement>('input[autocomplete="username"]')!;
const passwordInput = () => document.querySelector<HTMLInputElement>('input[autocomplete="current-password"]')!;

async function fillAndSubmit(user = "tester", pass = "pw") {
  await userEvent.type(usernameInput(), user);
  await userEvent.type(passwordInput(), pass);
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
}

describe("Login page + API client", () => {
  beforeEach(() => router.push.mockReset());

  it("disables submit until both fields are filled", async () => {
    render(<LoginPage />);
    const btn = screen.getByRole("button", { name: /sign in/i });
    expect(btn).toBeDisabled();
    await userEvent.type(usernameInput(), "tester");
    expect(btn).toBeDisabled();
    await userEvent.type(passwordInput(), "pw");
    expect(btn).toBeEnabled();
  });

  it("logs in, stores the token and navigates home", async () => {
    const fetch = mockFetch(jsonResponse({ token: "jwt-123", username: "tester", expires_in_hours: 1 }));
    render(<LoginPage />);
    await fillAndSubmit("tester", "s3cret");

    expect(fetch).toHaveBeenCalledWith(`${API}/auth/login`, expect.objectContaining({ method: "POST" }));
    expect(JSON.parse(fetch.mock.calls[0][1]!.body as string)).toEqual({ username: "tester", password: "s3cret" });
    expect(window.localStorage.getItem(TOKEN_KEY)).toBe("jwt-123");
    expect(router.push).toHaveBeenCalledWith("/");
  });

  it("shows a friendly message on 401 and stays on the page", async () => {
    mockFetch(textResponse('{"detail":"invalid credentials"}', 401));
    render(<LoginPage />);
    await fillAndSubmit();

    expect(await screen.findByText("Invalid username or password")).toBeInTheDocument();
    expect(window.localStorage.getItem(TOKEN_KEY)).toBeNull();
    expect(router.push).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeEnabled();
  });

  it("shows the raw error for other failures", async () => {
    mockFetch(textResponse("upstream down", 502));
    render(<LoginPage />);
    await fillAndSubmit();
    expect(await screen.findByText("502: upstream down")).toBeInTheDocument();
  });
});
