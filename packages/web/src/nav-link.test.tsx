import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";

import { NavLink } from "./nav-link";

describe("NavLink", () => {
  it("marks the link for the current path, and paths below it, as the current page", () => {
    render(
      <MemoryRouter initialEntries={["/records/7"]}>
        <NavLink to="/records">Records</NavLink>
        <NavLink to="/items">Items</NavLink>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Records" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Records" })).toHaveClass("font-medium");
    expect(screen.getByRole("link", { name: "Items" })).not.toHaveAttribute("aria-current");
  });
});
