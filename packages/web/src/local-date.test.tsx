import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LocalDate } from "./local-date";

describe("LocalDate", () => {
  it("keeps the UTC timestamp in the time element and shows it in the browser's locale", () => {
    const iso = "2026-10-31T23:30:00Z";

    render(<LocalDate iso={iso} showTime={false} />);

    const time = screen.getByText(
      new Date(iso).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      }),
    );
    expect(time).toHaveAttribute("datetime", iso);
  });
});
