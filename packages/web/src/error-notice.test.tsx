import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "./api-client";
import { ErrorNotice } from "./error-notice";

describe("ErrorNotice", () => {
  it("shows the API's message and the correlation ID for support", () => {
    const error = new ApiError(409, { error: { message: "Name already used" } }, "corr-9");

    render(<ErrorNotice error={error} />);

    expect(screen.getByRole("alert")).toHaveTextContent("Name already used");
    expect(screen.getByText("corr-9")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("shows a general message for anything that is not an error, with no correlation ID", () => {
    render(<ErrorNotice error="unexpected" />);

    expect(screen.getByRole("alert")).toHaveTextContent("Something went wrong.");
    expect(screen.queryByText(/Correlation ID/)).not.toBeInTheDocument();
  });

  it("offers to try again", async () => {
    const onRetry = vi.fn();
    render(<ErrorNotice error={new Error("Offline")} onRetry={onRetry} />);

    await userEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(onRetry).toHaveBeenCalledOnce();
  });
});
