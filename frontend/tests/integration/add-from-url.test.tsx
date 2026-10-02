import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AddFromUrlModal } from "@/components/AddFromUrlModal";
import { jsonResponse, textResponse, mockFetch, TOKEN_KEY, API } from "../helpers";

function setup() {
  const props = { onClose: vi.fn(), onCreated: vi.fn(), onSwitchToManual: vi.fn() };
  render(<AddFromUrlModal {...props} />);
  return { ...props, input: screen.getByPlaceholderText(/greenhouse/i), submit: screen.getByRole("button", { name: /scrape & add/i }) };
}

describe("AddFromUrlModal + API client", () => {
  beforeEach(() => window.localStorage.setItem(TOKEN_KEY, "tok"));

  it("submits the URL and hands the created job back", async () => {
    const job = { id: 9, company: "Acme", role: "Engineer" };
    const fetch = mockFetch(jsonResponse(job, 201));
    const { input, submit, onCreated } = setup();
    expect(submit).toBeDisabled();

    await userEvent.type(input, "https://jobs.lever.co/acme/1");
    await userEvent.click(submit);

    expect(fetch).toHaveBeenCalledWith(`${API}/jobs/from-url`, expect.objectContaining({ method: "POST" }));
    expect(JSON.parse(fetch.mock.calls[0][1]!.body as string)).toEqual({ url: "https://jobs.lever.co/acme/1" });
    expect(onCreated).toHaveBeenCalledWith(job);
  });

  it("submits on Enter", async () => {
    const fetch = mockFetch(jsonResponse({ id: 1 }, 201));
    const { input, onCreated } = setup();
    await userEvent.type(input, "https://x.com/job{Enter}");
    expect(fetch).toHaveBeenCalledOnce();
    expect(onCreated).toHaveBeenCalled();
  });

  it("shows the backend error and does not call onCreated", async () => {
    mockFetch(textResponse('{"detail":"fetch failed: 403 Forbidden"}', 400));
    const { input, submit, onCreated } = setup();
    await userEvent.type(input, "https://linkedin.com/jobs/1");
    await userEvent.click(submit);
    expect(await screen.findByText(/fetch failed: 403 Forbidden/)).toBeInTheDocument();
    expect(onCreated).not.toHaveBeenCalled();
    expect(submit).toBeEnabled();
  });

  it("shows a busy state while scraping", async () => {
    let resolve!: (r: Response) => void;
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((r) => (resolve = r))));
    const { input, submit } = setup();
    await userEvent.type(input, "https://x.com");
    await userEvent.click(submit);
    expect(screen.getByRole("button", { name: /scraping/i })).toBeDisabled();
    resolve(jsonResponse({ id: 1 }, 201));
    expect(await screen.findByRole("button", { name: /scrape & add/i })).toBeInTheDocument();
  });

  it("wires up the close and manual-entry buttons", async () => {
    const { onClose, onSwitchToManual } = setup();
    await userEvent.click(screen.getByRole("button", { name: /enter manually/i }));
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onSwitchToManual).toHaveBeenCalledOnce();
    expect(onClose).toHaveBeenCalledOnce();
  });
});
