import { describe, expect, it } from "vitest";

import { loadConfig } from "./config";
import { fakeFetch, jsonResponse } from "./test/fake-api";

describe("loadConfig", () => {
  it("reads the environment from config.json, never from a cached copy", async () => {
    const requests = fakeFetch(() => jsonResponse({ environment: "dev" }));

    await expect(loadConfig()).resolves.toEqual({ environment: "dev" });
    expect(new URL(requests[0]?.url ?? "").pathname).toBe("/config.json");
    expect(requests[0]?.cache).toBe("no-store");
  });

  it("gives unknown when the file has no environment", async () => {
    fakeFetch(() => jsonResponse({ environment: 3 }));
    await expect(loadConfig()).resolves.toEqual({ environment: "unknown" });
  });

  it("gives unknown when the file cannot be read", async () => {
    fakeFetch(() => new Response("not json"));
    await expect(loadConfig()).resolves.toEqual({ environment: "unknown" });
  });
});
