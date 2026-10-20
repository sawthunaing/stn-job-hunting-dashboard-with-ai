import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Sidebar } from "@/components/Sidebar";

function setup(overrides: Partial<Parameters<typeof Sidebar>[0]> = {}) {
  const props = {
    jobs: [],
    selectedId: null,
    onSelect: vi.fn(),
    search: "",
    onSearch: vi.fn(),
    statusFilter: "All",
    onStatusChange: vi.fn(),
    onAddClick: vi.fn(),
    loading: false,
    minScore: 0,
    onMinScoreChange: vi.fn(),
    includeUnscored: true,
    onIncludeUnscoredChange: vi.fn(),
    appliedFrom: "",
    onAppliedFromChange: vi.fn(),
    appliedTo: "",
    onAppliedToChange: vi.fn(),
    ...overrides,
  };
  render(<Sidebar {...props} />);
  return props;
}

describe("Sidebar applied-date filter", () => {
  it("renders the from/to date inputs with the given values", () => {
    setup({ appliedFrom: "2026-10-01", appliedTo: "2026-10-15" });
    expect(screen.getByLabelText("Applied from")).toHaveValue("2026-10-01");
    expect(screen.getByLabelText("Applied to")).toHaveValue("2026-10-15");
  });

  it("calls onAppliedFromChange / onAppliedToChange when the inputs change", async () => {
    const { onAppliedFromChange, onAppliedToChange } = setup();
    await userEvent.type(screen.getByLabelText("Applied from"), "2026-10-01");
    expect(onAppliedFromChange).toHaveBeenCalledWith("2026-10-01");
    await userEvent.type(screen.getByLabelText("Applied to"), "2026-10-15");
    expect(onAppliedToChange).toHaveBeenCalledWith("2026-10-15");
  });

  it("hides the clear button when neither date is set", () => {
    setup();
    expect(screen.queryByLabelText("Clear applied-date filter")).not.toBeInTheDocument();
  });

  it("clear button resets both dates", async () => {
    const { onAppliedFromChange, onAppliedToChange } = setup({ appliedFrom: "2026-10-01" });
    await userEvent.click(screen.getByLabelText("Clear applied-date filter"));
    expect(onAppliedFromChange).toHaveBeenCalledWith("");
    expect(onAppliedToChange).toHaveBeenCalledWith("");
  });
});

describe("Sidebar status chip row", () => {
  it("renders every status chip, including Rejected, without a scroll container", () => {
    setup();
    for (const s of ["All", "New", "Applied", "Interviewing", "Offer", "Rejected"]) {
      expect(screen.getByRole("button", { name: s })).toBeInTheDocument();
    }
    const row = screen.getByRole("button", { name: "Rejected" }).parentElement!;
    expect(row.className).toContain("flex-wrap");
    expect(row.className).not.toContain("overflow-x-auto");
    expect(row.className).not.toContain("scrollbar-hide");
  });

  it("clicking the Rejected chip calls onStatusChange", async () => {
    const { onStatusChange } = setup();
    await userEvent.click(screen.getByRole("button", { name: "Rejected" }));
    expect(onStatusChange).toHaveBeenCalledWith("Rejected");
  });
});
