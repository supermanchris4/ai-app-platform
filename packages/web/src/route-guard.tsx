import type { ReactNode } from "react";

import { useSession } from "./session";

/**
 * Shows `children` when the signed-in person holds any of `anyOf`, and `otherwise` when not. This
 * decides only what is shown; the API refuses anything the roles do not allow.
 */
export function RequireRoles({
  anyOf,
  otherwise,
  children,
}: {
  anyOf: readonly string[];
  otherwise: ReactNode;
  children: ReactNode;
}) {
  const { roles } = useSession();
  return roles.some((role) => anyOf.includes(role)) ? children : otherwise;
}
