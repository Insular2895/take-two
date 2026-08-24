import type { CloudPositionDossier, OptionQuote, ProviderSnapshot } from "./types";

export interface MarketDataProvider {
  getUnderlyingQuote(dossier: CloudPositionDossier): Promise<{ spot: number; timestamp: string; source: string; quality: string }>;
  getOptionQuotes(dossier: CloudPositionDossier): Promise<OptionQuote[]>;
  getFxQuote(dossier: CloudPositionDossier): Promise<{ rate: number | null; timestamp: string | null; source: string | null }>;
  getProviderStatus(): Promise<{ status: "READY" | "NOT_CONFIGURED" | "ERROR"; provider: string }>;
  getComboQuote?(dossier: CloudPositionDossier): Promise<{
    price: number;
    cash_flow_type: "CREDIT" | "DEBIT";
    timestamp: string | null;
  } | null>;
}

class HttpMarketDataProvider implements MarketDataProvider {
  constructor(private readonly baseUrl: string, private readonly apiKey: string) {}

  private async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: { Authorization: `Bearer ${this.apiKey}`, Accept: "application/json" },
    });
    if (!response.ok) throw new Error(`DATA_PROVIDER_ERROR:${response.status}`);
    return response.json<T>();
  }

  getUnderlyingQuote(dossier: CloudPositionDossier) {
    return this.get<{ spot: number; timestamp: string; source: string; quality: string }>(`/underlying/${encodeURIComponent(dossier.ticker)}`);
  }

  getOptionQuotes(dossier: CloudPositionDossier) {
    const identities = dossier.legs.map((leg) => leg.contract_identity).join(",");
    return this.get<OptionQuote[]>(`/options?identities=${encodeURIComponent(identities)}`);
  }

  getFxQuote(dossier: CloudPositionDossier) {
    return this.get<{ rate: number | null; timestamp: string | null; source: string | null }>(
      `/fx/${encodeURIComponent(dossier.entry_native_currency)}/${encodeURIComponent(dossier.policy_currency)}`,
    );
  }

  async getProviderStatus() {
    const status = await this.get<{ status: "READY" | "ERROR"; provider: string }>("/status");
    return status;
  }

  getComboQuote(dossier: CloudPositionDossier) {
    return this.get<{
      price: number;
      cash_flow_type: "CREDIT" | "DEBIT";
      timestamp: string | null;
    } | null>(`/combo/${encodeURIComponent(dossier.position_id)}`);
  }
}

class NotConfiguredMarketDataProvider implements MarketDataProvider {
  async getUnderlyingQuote(): Promise<never> { throw new Error("MARKET_DATA_NOT_CONFIGURED"); }
  async getOptionQuotes(): Promise<never> { throw new Error("MARKET_DATA_NOT_CONFIGURED"); }
  async getFxQuote(): Promise<never> { throw new Error("MARKET_DATA_NOT_CONFIGURED"); }
  async getProviderStatus() { return { status: "NOT_CONFIGURED" as const, provider: "NONE" }; }
}

export function marketDataProvider(env: Env): MarketDataProvider {
  if (env.MARKET_DATA_BASE_URL && env.MARKET_DATA_API_KEY) {
    return new HttpMarketDataProvider(env.MARKET_DATA_BASE_URL.replace(/\/$/, ""), env.MARKET_DATA_API_KEY);
  }
  return new NotConfiguredMarketDataProvider();
}

export async function fetchProviderSnapshot(
  provider: MarketDataProvider,
  dossier: CloudPositionDossier,
): Promise<ProviderSnapshot | null> {
  const status = await provider.getProviderStatus();
  if (status.status !== "READY") return null;
  const sameCurrency = dossier.entry_native_currency === dossier.policy_currency;
  const [underlying, options, fx, combo] = await Promise.all([
    provider.getUnderlyingQuote(dossier),
    provider.getOptionQuotes(dossier),
    sameCurrency
      ? Promise.resolve({ rate: null, timestamp: null, source: null })
      : provider.getFxQuote(dossier),
    provider.getComboQuote ? provider.getComboQuote(dossier) : Promise.resolve(null),
  ]);
  const ivValues = options.flatMap((quote) => quote.iv === undefined ? [] : [quote.iv]);
  const currentGreeks: Record<string, number> = {};
  for (const option of options) {
    const leg = dossier.legs.find((candidate) => candidate.contract_identity === option.contract_identity);
    if (!leg || !option.greeks) continue;
    const sign = leg.side === "LONG" ? 1 : -1;
    for (const [name, value] of Object.entries(option.greeks)) {
      currentGreeks[name] = (currentGreeks[name] ?? 0) + sign * value * leg.quantity * leg.multiplier;
    }
  }
  const imported = dossier.last_imported_snapshot;
  const snapshot: ProviderSnapshot = {
    timestamp: underlying.timestamp,
    underlying_timestamp: underlying.timestamp,
    provider: status.provider,
    source: underlying.source,
    quality: underlying.quality,
    synthetic: false,
    spot: underlying.spot,
    option_quotes: options,
    fx_rate_to_policy_currency: fx.rate,
    fx_source: fx.source,
    fx_timestamp: fx.timestamp,
    estimated_exit_commission: imported?.estimated_exit_commission ?? null,
    estimated_exit_slippage: imported?.estimated_exit_slippage ?? null,
    estimated_exit_fx: imported?.estimated_exit_fx ?? null,
    estimated_exit_fx_status: imported?.estimated_exit_fx_status ?? "UNKNOWN",
    current_iv: ivValues.length ? ivValues.reduce((sum, value) => sum + value, 0) / ivValues.length : null,
    current_greeks: currentGreeks,
    thesis_invalidated: false,
    data_sufficient: true,
  };
  if (combo) snapshot.combo_quote = combo;
  return snapshot;
}
