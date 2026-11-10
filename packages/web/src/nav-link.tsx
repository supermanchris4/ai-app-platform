import type { ReactNode } from "react";
import { NavLink as RouterNavLink } from "react-router";

/** A sidebar link, highlighted while the current path is `to` or below it. */
export function NavLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <RouterNavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center rounded-md px-3 py-2 text-sm transition-colors ${
          isActive
            ? "bg-accent font-medium text-accent-foreground"
            : "hover:bg-accent hover:text-accent-foreground"
        }`
      }
    >
      {children}
    </RouterNavLink>
  );
}
