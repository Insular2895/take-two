interface WorkerEnv {
  DB: D1Database;
  MONITOR: DurableObjectNamespace;
  ACTION_PASSWORD_VERIFIER: string;
  ANALYSIS_CALLBACK_SECRET: string;
  GITHUB_ACTIONS_TOKEN: string;
  GITHUB_REPOSITORY: string;
  GITHUB_WORKFLOW: string;
  GITHUB_GOVERNED_REF: string;
  BROKER_BRIDGE_SHARED_SECRET?: string;
  BROKER_BRIDGE_ID?: string;
  BROKER_TELEMETRY_SHARED_SECRET?: string;
  BROKER_TELEMETRY_ID?: string;
  MARKET_DATA_API_KEY?: string;
  MARKET_DATA_BASE_URL?: string;
  FREE_TIER_MODE: string;
  MARKET_INTERVAL_SECONDS: string;
  OFF_HOURS_INTERVAL_SECONDS: string;
  SNAPSHOT_INTERVAL_SECONDS: string;
}

interface Env extends WorkerEnv {}

declare namespace Cloudflare {
  interface Env extends WorkerEnv {
    TEST_MIGRATIONS: D1Migration[];
  }
}
