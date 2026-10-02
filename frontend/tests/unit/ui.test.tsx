import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Star } from "lucide-react";
import { scoreColor, StatusPill, SuitabilityRing, ActionButton, MetaChip, STATUS_STYLES } from "@/components/ui";

describe("scoreColor", () => {
  it.each([
    [100, "text-emerald-400"],
    [85, "text-emerald-400"],
    [84, "text-amber-400"],
    [70, "text-amber-400"],
    [69, "text-zinc-400"],
    [0, "text-zinc-400"],
  ])("%i -> %s", (score, cls) => {
    expect(scoreColor(score).text).toBe(cls);
  });
});

describe("StatusPill", () => {
  it.each(Object.keys(STATUS_STYLES))("renders %s with its colour", (status) => {
    render(<StatusPill status={status} />);
    expect(screen.getByText(status)).toHaveClass(STATUS_STYLES[status].text);
  });

  it("falls back to New styling for unknown statuses", () => {
    render(<StatusPill status="Ghosted" />);
    expect(screen.getByText("Ghosted")).toHaveClass(STATUS_STYLES.New.text);
  });
});

describe("SuitabilityRing", () => {
  it("shows the score with matching colour", () => {
    render(<SuitabilityRing score={90} />);
    expect(screen.getByText("90")).toHaveClass("text-emerald-400");
  });

  it("dash offset is proportional to the score", () => {
    const { container } = render(<SuitabilityRing score={25} size={46} />);
    const ring = container.querySelectorAll("circle")[1];
    const circ = 2 * Math.PI * 20;
    expect(Number(ring.getAttribute("stroke-dashoffset"))).toBeCloseTo(circ * 0.75);
  });
});

describe("MetaChip", () => {
  it("renders its label", () => {
    render(<MetaChip icon={Star} label="London" />);
    expect(screen.getByText("London")).toBeInTheDocument();
  });
});

describe("ActionButton", () => {
  it("calls onClick", async () => {
    const onClick = vi.fn();
    render(<ActionButton icon={Star} label="Analyze" onClick={onClick} />);
    await userEvent.click(screen.getByRole("button", { name: "Analyze" }));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it.each([{ loading: true }, { disabled: true }])("is disabled when %j", async (props) => {
    const onClick = vi.fn();
    render(<ActionButton icon={Star} label="Go" onClick={onClick} {...props} />);
    const btn = screen.getByRole("button", { name: "Go" });
    expect(btn).toBeDisabled();
    await userEvent.click(btn);
    expect(onClick).not.toHaveBeenCalled();
  });

  it("renders nothing when hidden", () => {
    const { container } = render(<ActionButton icon={Star} label="Go" hidden />);
    expect(container).toBeEmptyDOMElement();
  });

  it("applies primary/danger styles", () => {
    render(<><ActionButton icon={Star} label="P" primary /><ActionButton icon={Star} label="D" danger /></>);
    expect(screen.getByRole("button", { name: "P" })).toHaveClass("bg-blue-500");
    expect(screen.getByRole("button", { name: "D" })).toHaveClass("text-red-300");
  });
});
