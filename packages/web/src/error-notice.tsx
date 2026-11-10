import { ApiError } from "./api-client";

/** An error with the API's message and the correlation ID for support (specs/40-ui.md). */
export function ErrorNotice({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : "Something went wrong.";
  const correlationId = error instanceof ApiError ? error.correlationId : null;
  return (
    <div
      role="alert"
      className="rounded-md border border-destructive/50 bg-destructive/5 p-4 text-sm"
    >
      <p className="font-medium">{message}</p>
      {correlationId !== null && (
        <p className="mt-1 text-muted-foreground">
          Correlation ID for support: <span className="font-mono">{correlationId}</span>
        </p>
      )}
      {onRetry !== undefined && (
        <button type="button" onClick={onRetry} className="mt-2 underline">
          Try again
        </button>
      )}
    </div>
  );
}
