import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RequireRoles } from "./route-guard";
import { SessionContext } from "./session";

function renderWithRoles(roles: string[]) {
  render(
    <SessionContext.Provider value={{ displayName: "Test Person", actorType: "internal", roles }}>
      <RequireRoles anyOf={["admin.write", "editor.write"]} otherwise={<p>Not permitted</p>}>
        <p>Allowed</p>
      </RequireRoles>
    </SessionContext.Provider>,
  );
}

describe("RequireRoles", () => {
  it("shows the content to a person holding any of the roles", () => {
    renderWithRoles(["editor.write"]);
    expect(screen.getByText("Allowed")).toBeInTheDocument();
  });

  it("shows the alternative to anyone else", () => {
    renderWithRoles(["reader"]);
    expect(screen.getByText("Not permitted")).toBeInTheDocument();
    expect(screen.queryByText("Allowed")).not.toBeInTheDocument();
  });
});
