interface WorkerEnv {
  DB: D1Database;
  MONITOR: DurableObjectNamespace;
  ACTION_PASSWORD_VERIFIER: string;
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
