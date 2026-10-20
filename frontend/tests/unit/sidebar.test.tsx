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
    sortBy: "created_at_desc" as const,
    onSortByChange: vi.fn(),
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

describe("Sidebar sort-by control", () => {
  it("defaults to Date added", () => {
    setup();
    expect(screen.getByLabelText("Sort by")).toHaveValue("created_at_desc");
  });

  it("shows the given sort value selected", () => {
    setup({ sortBy: "updated_at_desc" });
    expect(screen.getByLabelText("Sort by")).toHaveValue("updated_at_desc");
  });

  it("calls onSortByChange when a different option is picked", async () => {
    const { onSortByChange } = setup();
    await userEvent.selectOptions(screen.getByLabelText("Sort by"), "updated_at_desc");
    expect(onSortByChange).toHaveBeenCalledWith("updated_at_desc");
  });
});
