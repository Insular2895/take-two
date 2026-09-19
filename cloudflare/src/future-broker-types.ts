/**
 * Research-workbench descriptors only; these are not an executable API.
 * The separately isolated paper-control foundation does not make a planned research dossier
 * executable and is intentionally not represented by these types.
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
