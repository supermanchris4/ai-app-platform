import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { apiRequest } from "./api-client";
import { useSession } from "./session";
import { SessionProvider } from "./session-provider";
import { captureNavigation, fakeFetch, jsonResponse } from "./test/fake-api";

const SESSION = {
  display_name: "Sam Example",
  actor_type: "internal",
  roles: ["editor.write"],
  csrf_token: "session-csrf",
};

function WhoIsSignedIn() {
  const session = useSession();
  return (
    <p>
      {session.displayName} holds {session.roles.join(", ")}
    </p>
  );
}

function renderProvider() {
  render(
    <SessionProvider>
      <WhoIsSignedIn />
    </SessionProvider>,
  );
}

describe("SessionProvider", () => {
  it("shows loading, then the app with the signed-in person", async () => {
    fakeFetch(() => jsonResponse(SESSION));

    renderProvider();

    expect(screen.getByRole("status")).toHaveTextContent("Loading");
    expect(await screen.findByText("Sam Example holds editor.write")).toBeInTheDocument();
  });

  it("sends the session's CSRF token on later state-changing requests", async () => {
    const requests = fakeFetch((request) =>
      request.url.endsWith("/api/auth/session") ? jsonResponse(SESSION) : jsonResponse({}),
    );
    renderProvider();
    await screen.findByText(/Sam Example/);

    await apiRequest("/api/v1/records", { method: "POST" });

    expect(requests.at(-1)?.headers.get("X-CSRF-Token")).toBe("session-csrf");
  });

  it("keeps loading while a person who is not signed in is sent to sign in", async () => {
    const addresses = captureNavigation();
    fakeFetch(() => jsonResponse({ error: { code: "UNAUTHORIZED", message: "Sign in" } }, 401));

    renderProvider();

    await waitFor(() => {
      expect(addresses).toHaveLength(1);
    });
    expect(screen.getByRole("status")).toHaveTextContent("Loading");
  });

  it("shows the error when the session cannot be read, and tries again on request", async () => {
    let calls = 0;
    fakeFetch(() => {
      calls += 1;
      return calls === 1
        ? jsonResponse({ error: { message: "Service unavailable", correlation_id: "c-1" } }, 503)
        : jsonResponse(SESSION);
    });
    renderProvider();

    expect(await screen.findByRole("alert")).toHaveTextContent("Service unavailable");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByText(/Sam Example/)).toBeInTheDocument();
  });
});
