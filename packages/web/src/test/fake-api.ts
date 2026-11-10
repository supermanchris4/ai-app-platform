import { vi } from "vitest";

import { navigation } from "../navigation";

export type Handler = (request: Request) => Response | Promise<Response>;

export function jsonResponse(body: unknown, status = 200, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

/** Replaces `fetch` with `handler` and returns the requests it received. */
export function fakeFetch(handler: Handler): Request[] {
  const requests: Request[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      // Paths resolve against the page, as browsers do; Node's Request needs them absolute.
      const target = typeof input === "string" ? new URL(input, window.location.href) : input;
      const request = new Request(target, init);
      requests.push(request);
      return handler(request);
    }),
  );
  return requests;
}

/** Records full-page navigations instead of making them, which jsdom cannot. */
export function captureNavigation(): string[] {
  const addresses: string[] = [];
  vi.spyOn(navigation, "assign").mockImplementation((url) => {
    addresses.push(url);
  });
  return addresses;
}
