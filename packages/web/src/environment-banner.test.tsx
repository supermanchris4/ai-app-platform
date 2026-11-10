import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EnvironmentBanner } from "./environment-banner";

describe("EnvironmentBanner", () => {
  it("names the environment", () => {
    render(<EnvironmentBanner environment="test" />);
    expect(screen.getByText("Environment: test")).toBeInTheDocument();
  });

  it("shows nothing in production", () => {
    const { container } = render(<EnvironmentBanner environment="prod" />);
    expect(container).toBeEmptyDOMElement();
  });
});
