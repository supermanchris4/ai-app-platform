import { signIn } from "./navigation";

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

let csrfToken: string | null = null;

/** The session's cross-site request forgery token, sent on every state-changing request. */
export function setCsrfToken(token: string | null): void {
  csrfToken = token;
}

/** A failed API call, with the status and the API's shared error body (specs/21-api.md §1.8). */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly body: unknown;
  readonly correlationId: string | null;

  constructor(status: number, body: unknown, correlationId: string | null) {
    const error = errorObject(body);
    super(stringField(error, "message") ?? `The request failed with status ${String(status)}`);
    this.name = "ApiError";
    this.status = status;
    this.code = stringField(error, "code");
    this.body = body;
    this.correlationId = stringField(error, "correlation_id") ?? correlationId;
  }
}

/**
 * `fetch` for API calls. Adds the correlation ID to every request and the CSRF token to
 * state-changing ones, sends the browser's session cookie, and on a 401 sends the person to sign in
 * again. Returns the response, including error responses; `apiRequest` turns those into `ApiError`.
 *
 * The API lets callers cache some lists for minutes (specs/21-api.md#17-caching), but a page
 * reloads its data after a change to show the change, so the browser revalidates every response.
 */
export async function platformFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  // A path is resolved against the page, as browsers do; Node's Request, under test, needs it absolute.
  const target = typeof input === "string" ? new URL(input, window.location.href) : input;
  const request = new Request(target, { credentials: "same-origin", cache: "no-cache", ...init });
  if (!request.headers.has("X-Correlation-ID")) {
    request.headers.set("X-Correlation-ID", crypto.randomUUID());
  }
  if (!SAFE_METHODS.has(request.method) && csrfToken !== null) {
    request.headers.set("X-CSRF-Token", csrfToken);
  }
  const response = await fetch(request);
  if (response.status === 401) {
    signIn();
  }
  return response;
}

/** Call the API and return the parsed JSON body, or throw `ApiError`. */
export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await platformFetch(path, init);
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    throw new ApiError(response.status, body, response.headers.get("X-Correlation-ID"));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function errorObject(body: unknown): Record<string, unknown> | null {
  if (typeof body === "object" && body !== null && "error" in body) {
    const error = body.error;
    if (typeof error === "object" && error !== null) {
      return error as Record<string, unknown>;
    }
  }
  return null;
}

function stringField(object: Record<string, unknown> | null, name: string): string | null {
  const value = object?.[name];
  return typeof value === "string" ? value : null;
}
