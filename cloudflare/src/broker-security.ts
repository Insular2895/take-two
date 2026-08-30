const MAX_BODY_BYTES = 64 * 1024;
const MAX_CLOCK_SKEW_SECONDS = 60;

export interface VerifiedBridgeRequest {
  bridgeId: string;
  bodyText: string;
  receivedAt: string;
}

export interface VerifiedTelemetryRequest {
  telemetryId: string;
  bodyText: string;
  receivedAt: string;
  payloadSha256: string;
}

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
}

function hexToBytes(value: string): Uint8Array | null {
  if (!/^[0-9a-f]{64}$/i.test(value)) return null;
  const result = new Uint8Array(value.length / 2);
  for (let index = 0; index < value.length; index += 2) {
    result[index / 2] = Number.parseInt(value.slice(index, index + 2), 16);
  }
  return result;
}

export async function sha256Hex(value: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return bytesToHex(new Uint8Array(digest));
}

async function verifyHmac(secret: string, canonical: string, signatureHex: string): Promise<boolean> {
  const signature = hexToBytes(signatureHex);
  if (!signature) return false;
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"],
  );
  return crypto.subtle.verify(
    "HMAC",
    key,
    Uint8Array.from(signature).buffer,
    new TextEncoder().encode(canonical),
  );
}

interface MachineSignatureConfig {
  secret: string | undefined;
  configuredId: string | undefined;
  idHeader: string;
  timestampHeader: string;
  nonceHeader: string;
  signatureHeader: string;
  errorPrefix: "BROKER_BRIDGE" | "BROKER_TELEMETRY";
}

async function verifyMachineRequest(
  request: Request,
  env: Env,
  config: MachineSignatureConfig,
): Promise<{ machineId: string; bodyText: string; receivedAt: string; payloadSha256: string }> {
  const secret = config.secret?.trim();
  if (!secret || secret.length < 32) throw new Error(`${config.errorPrefix}_SECRET_NOT_CONFIGURED`);

  const machineId = request.headers.get(config.idHeader) ?? "";
  const timestampText = request.headers.get(config.timestampHeader) ?? "";
  const nonce = request.headers.get(config.nonceHeader) ?? "";
  const suppliedSignature = request.headers.get(config.signatureHeader) ?? "";
  if (!/^[a-zA-Z0-9._-]{3,80}$/.test(machineId)) throw new Error(`INVALID_${config.errorPrefix}_ID`);
  if (config.configuredId?.trim() && machineId !== config.configuredId.trim()) {
    throw new Error(`INVALID_${config.errorPrefix}_ID`);
  }
  if (!/^[a-zA-Z0-9_-]{16,128}$/.test(nonce)) throw new Error(`INVALID_${config.errorPrefix}_NONCE`);

  const timestamp = Number(timestampText);
  const nowSeconds = Math.floor(Date.now() / 1000);
  if (!Number.isInteger(timestamp) || Math.abs(nowSeconds - timestamp) > MAX_CLOCK_SKEW_SECONDS) {
    throw new Error(`${config.errorPrefix}_TIMESTAMP_OUTSIDE_WINDOW`);
  }

  const bodyText = await request.text();
  if (new TextEncoder().encode(bodyText).byteLength > MAX_BODY_BYTES) {
    throw new Error(`${config.errorPrefix}_BODY_TOO_LARGE`);
  }
  const path = new URL(request.url).pathname;
  const payloadSha256 = await sha256Hex(bodyText);
  const canonical = [timestampText, nonce, request.method.toUpperCase(), path, payloadSha256].join("\n");
  if (!await verifyHmac(secret, canonical, suppliedSignature)) {
    throw new Error(`INVALID_${config.errorPrefix}_SIGNATURE`);
  }

  const receivedAt = new Date().toISOString();
  await env.DB.prepare("DELETE FROM broker_bridge_nonces WHERE received_at < ?")
    .bind(new Date(Date.now() - 10 * 60_000).toISOString()).run();
  const inserted = await env.DB.prepare(
    "INSERT OR IGNORE INTO broker_bridge_nonces(nonce,bridge_id,received_at) VALUES(?,?,?)",
  ).bind(nonce, machineId, receivedAt).run();
  if (!inserted.meta.changes) throw new Error(`${config.errorPrefix}_REPLAY_DETECTED`);
  return { machineId, bodyText, receivedAt, payloadSha256 };
}

export async function verifyBridgeRequest(request: Request, env: Env): Promise<VerifiedBridgeRequest> {
  const verified = await verifyMachineRequest(request, env, {
    secret: env.BROKER_BRIDGE_SHARED_SECRET,
    configuredId: env.BROKER_BRIDGE_ID,
    idHeader: "X-TTWO-Bridge-Id",
    timestampHeader: "X-TTWO-Bridge-Timestamp",
    nonceHeader: "X-TTWO-Bridge-Nonce",
    signatureHeader: "X-TTWO-Bridge-Signature",
    errorPrefix: "BROKER_BRIDGE",
  });
  return { bridgeId: verified.machineId, bodyText: verified.bodyText, receivedAt: verified.receivedAt };
}

export async function verifyTelemetryRequest(request: Request, env: Env): Promise<VerifiedTelemetryRequest> {
  const verified = await verifyMachineRequest(request, env, {
    secret: env.BROKER_TELEMETRY_SHARED_SECRET,
    configuredId: env.BROKER_TELEMETRY_ID,
    idHeader: "X-TTWO-Telemetry-Id",
    timestampHeader: "X-TTWO-Telemetry-Timestamp",
    nonceHeader: "X-TTWO-Telemetry-Nonce",
    signatureHeader: "X-TTWO-Telemetry-Signature",
    errorPrefix: "BROKER_TELEMETRY",
  });
  return {
    telemetryId: verified.machineId,
    bodyText: verified.bodyText,
    receivedAt: verified.receivedAt,
    payloadSha256: verified.payloadSha256,
  };
}
