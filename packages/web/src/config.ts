/** Settings written at deployment into `config.json`; only the environment name (specs/40-ui.md). */
export interface AppConfig {
  environment: string;
}

/** Read `config.json`. An unreadable file gives "unknown", so the environment banner still shows. */
export async function loadConfig(): Promise<AppConfig> {
  try {
    const response = await fetch("/config.json", { cache: "no-store" });
    const config = (await response.json()) as Partial<AppConfig>;
    return { environment: typeof config.environment === "string" ? config.environment : "unknown" };
  } catch {
    return { environment: "unknown" };
  }
}
