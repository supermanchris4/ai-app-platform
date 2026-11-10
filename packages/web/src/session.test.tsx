import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { apiRequest, setCsrfToken } from "./api-client";
import { signOut, useSession } from "./session";
import { captureNavigation, fakeFetch, jsonResponse } from "./test/fake-api";

describe("useSession", () => {
  it("is refused outside SessionProvider", () => {
    expect(() => renderHook(() => useSession())).toThrow(/outside SessionProvider/);
  });
});

describe("signOut", () => {
  beforeEach(() => {
    setCsrfToken("csrf-token");
  });

  it("ends the session with the CSRF token, then follows the provider's sign-out address", async () => {
    const addresses = captureNavigation();
    const requests = fakeFetch(() => jsonResponse({ logout_url: "https://issuer.example/logout" }));

    await signOut();

    expect(requests[0]?.method).toBe("POST");
    expect(new URL(requests[0]?.url ?? "").pathname).toBe("/api/auth/logout");
    expect(requests[0]?.headers.get("X-CSRF-Token")).toBe("csrf-token");
    expect(addresses).toEqual(["https://issuer.example/logout"]);
  });

  it("forgets the CSRF token and goes home when the provider has no sign-out address", async () => {
    const addresses = captureNavigation();
    const requests = fakeFetch(() => jsonResponse({ logout_url: null }));

    await signOut();
    await apiRequest("/api/v1/records", { method: "POST" });

    expect(addresses).toEqual(["/"]);
    expect(requests[1]?.headers.get("X-CSRF-Token")).toBeNull();
  });
});
