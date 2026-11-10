import { createContext, useContext } from "react";

import { apiRequest, setCsrfToken } from "./api-client";
import { navigation } from "./navigation";

/** The signed-in person, from `GET /api/auth/session`. */
export interface Session {
  displayName: string | null;
  actorType: string;
  roles: string[];
}

export const SessionContext = createContext<Session | null>(null);

/** The signed-in person. Only for components inside `SessionProvider`. */
export function useSession(): Session {
  const session = useContext(SessionContext);
  if (session === null) {
    throw new Error("useSession is used outside SessionProvider");
  }
  return session;
}

/** End the session through the API, then follow the identity provider's sign-out address. */
export async function signOut(): Promise<void> {
  const response = await apiRequest<{ logout_url: string | null }>("/api/auth/logout", {
    method: "POST",
  });
  setCsrfToken(null);
  navigation.assign(response.logout_url ?? "/");
}
