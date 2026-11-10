import { useCallback, useEffect, useState, type ReactNode } from "react";

import { ApiError, apiRequest, setCsrfToken } from "./api-client";
import { ErrorNotice } from "./error-notice";
import { SessionContext, type Session } from "./session";

interface SessionResponse {
  display_name: string | null;
  actor_type: string;
  roles: string[];
  csrf_token: string;
}

type SessionState =
  | { status: "loading" }
  | { status: "signed-in"; session: Session }
  | { status: "failed"; error: unknown };

/**
 * Reads who is signed in when the app starts and renders `children` only once they are. A person
 * who is not signed in is sent to the API's sign-in endpoint by the API module's 401 handling.
 */
export function SessionProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SessionState>({ status: "loading" });

  const fetchSession = useCallback(() => {
    apiRequest<SessionResponse>("/api/auth/session").then(
      (response) => {
        setCsrfToken(response.csrf_token);
        setState({
          status: "signed-in",
          session: {
            displayName: response.display_name,
            actorType: response.actor_type,
            roles: response.roles,
          },
        });
      },
      (error: unknown) => {
        // A 401 has already sent the person to sign in, so the loading state stays while it does.
        if (!(error instanceof ApiError && error.status === 401)) {
          setState({ status: "failed", error });
        }
      },
    );
  }, []);

  useEffect(fetchSession, [fetchSession]);

  if (state.status === "loading") {
    return (
      <p role="status" className="p-6 text-sm text-muted-foreground">
        Loading…
      </p>
    );
  }
  if (state.status === "failed") {
    return (
      <div className="p-6">
        <ErrorNotice
          error={state.error}
          onRetry={() => {
            setState({ status: "loading" });
            fetchSession();
          }}
        />
      </div>
    );
  }
  return <SessionContext.Provider value={state.session}>{children}</SessionContext.Provider>;
}
