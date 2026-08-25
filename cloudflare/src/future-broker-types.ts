/**
 * Future-only broker boundary. These are descriptors, not an executable API.
 * No credentials, sessions, order methods, or provider implementation exist.
 */
export type FutureBrokerKind = "IBKR" | "CUSTOMER_CONFIGURED";

export interface BrokerExecutionProviderDescriptor {
  provider: FutureBrokerKind;
  enabled: false;
  authorizationScope: "NOT_CONFIGURED";
  marketDataCapability: "NOT_CONFIGURED";
  executionCapability: "NOT_CONFIGURED";
  multiTenantCapability: "NOT_IMPLEMENTED";
  orderCapability: "forbidden";
}

export interface PlannedExecutionIntentDescriptor {
  dossierId: string;
  candidateId: string;
  state: "PLANNED";
  provider: null;
  actualEntryCashFlow: null;
  actualOpenedAt: null;
  transmitted: false;
}
