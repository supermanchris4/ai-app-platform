import { beforeEach, describe, expect, it } from "vitest";

import { captureNavigation, fakeFetch, jsonResponse } from "./test/fake-api";

import { ApiError, apiRequest, setCsrfToken } from "./api-client";

describe("apiRequest", () => {
  beforeEach(() => {
    setCsrfToken("csrf-token");
  });

  it("sends a correlation ID on every request and the session cookie", async () => {
    const requests = fakeFetch(() => jsonResponse({ ok: true }));

    await apiRequest("/api/v1/records");
    await apiRequest("/api/v1/records");

    const [first, second] = requests;
    expect(first?.headers.get("X-Correlation-ID")).toMatch(/^[0-9a-f-]{36}$/);
    expect(second?.headers.get("X-Correlation-ID")).not.toBe(
      first?.headers.get("X-Correlation-ID"),
    );
    expect(first?.credentials).toBe("same-origin");
  });

  it("asks the browser to revalidate rather than reuse a cached response", async () => {
    const requests = fakeFetch(() => jsonResponse({ ok: true }));

    await apiRequest("/api/v1/items");

    expect(requests[0]?.cache).toBe("no-cache");
  });

  it("sends the CSRF token only on state-changing requests", async () => {
    const requests = fakeFetch(() => jsonResponse({}));

    await apiRequest("/api/v1/records");
    await apiRequest("/api/v1/items", { method: "POST", body: "{}" });
    await apiRequest("/api/v1/items/1", { method: "DELETE" });

    expect(requests.map((request) => request.headers.get("X-CSRF-Token"))).toEqual([
      null,
      "csrf-token",
      "csrf-token",
    ]);
  });

  it("returns the parsed body, and nothing for 204", async () => {
    fakeFetch((request) =>
      request.method === "DELETE" ? new Response(null, { status: 204 }) : jsonResponse({ id: 1 }),
    );

    await expect(apiRequest("/api/v1/thing")).resolves.toEqual({ id: 1 });
    await expect(apiRequest("/api/v1/thing", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it("raises ApiError with the status, code, message and correlation ID", async () => {
    fakeFetch(() =>
      jsonResponse(
        { error: { code: "CONFLICT", message: "Code already used", correlation_id: "corr-1" } },
        409,
      ),
    );

    const error = await apiRequest("/api/v1/items", { method: "POST" }).catch(
      (caught: unknown) => caught,
    );

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 409,
      code: "CONFLICT",
      message: "Code already used",
      correlationId: "corr-1",
    });
  });

  it("falls back to the response's correlation ID when the body has none", async () => {
    fakeFetch(
      () => new Response("Bad gateway", { status: 502, headers: { "X-Correlation-ID": "corr-2" } }),
    );

    const error = await apiRequest("/api/v1/records").catch((caught: unknown) => caught);

    expect(error).toMatchObject({ status: 502, correlationId: "corr-2", code: null });
    expect((error as ApiError).message).toBe("The request failed with status 502");
  });

  it("sends the person to sign in again on a 401, returning to the current page", async () => {
    window.history.pushState({}, "", "/records?status=active");
    const addresses = captureNavigation();
    fakeFetch(() => jsonResponse({ error: { code: "UNAUTHORIZED", message: "Sign in" } }, 401));

    await expect(apiRequest("/api/v1/records")).rejects.toMatchObject({ status: 401 });

    expect(addresses).toEqual([
      "/api/auth/login?provider=internal&return_to=%2Frecords%3Fstatus%3Dactive",
    ]);
  });
});
