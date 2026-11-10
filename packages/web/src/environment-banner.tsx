const PRODUCTION = "prod";

/** Names the environment on every page, except in production (specs/40-ui.md). */
export function EnvironmentBanner({ environment }: { environment: string }) {
  if (environment === PRODUCTION) {
    return null;
  }
  return (
    <div className="bg-amber-100 px-4 py-1 text-center text-xs font-medium text-amber-900">
      Environment: {environment}
    </div>
  );
}
