const MAX_BODY_BYTES = 64 * 1024;
const MAX_CLOCK_SKEW_SECONDS = 60;

export interface VerifiedBridgeRequest {
  bridgeId: string;
  bodyText: string;
  receivedAt: string;
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

async function sha256Hex(value: string): Promise<string> {
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

export async function verifyBridgeRequest(request: Request, env: Env): Promise<VerifiedBridgeRequest> {
  const secret = env.BROKER_BRIDGE_SHARED_SECRET?.trim();
  if (!secret || secret.length < 32) throw new Error("BROKER_BRIDGE_SECRET_NOT_CONFIGURED");

  const bridgeId = request.headers.get("X-TTWO-Bridge-Id") ?? "";
  const timestampText = request.headers.get("X-TTWO-Bridge-Timestamp") ?? "";
  const nonce = request.headers.get("X-TTWO-Bridge-Nonce") ?? "";
  const suppliedSignature = request.headers.get("X-TTWO-Bridge-Signature") ?? "";
  if (!/^[a-zA-Z0-9._-]{3,80}$/.test(bridgeId)) throw new Error("INVALID_BROKER_BRIDGE_ID");
  if (env.BROKER_BRIDGE_ID?.trim() && bridgeId !== env.BROKER_BRIDGE_ID.trim()) {
    throw new Error("INVALID_BROKER_BRIDGE_ID");
  }
  if (!/^[a-zA-Z0-9_-]{16,128}$/.test(nonce)) throw new Error("INVALID_BROKER_BRIDGE_NONCE");

  const timestamp = Number(timestampText);
  const nowSeconds = Math.floor(Date.now() / 1000);
  if (!Number.isInteger(timestamp) || Math.abs(nowSeconds - timestamp) > MAX_CLOCK_SKEW_SECONDS) {
    throw new Error("BROKER_BRIDGE_TIMESTAMP_OUTSIDE_WINDOW");
  }

  const bodyText = await request.text();
  if (new TextEncoder().encode(bodyText).byteLength > MAX_BODY_BYTES) {
    throw new Error("BROKER_BRIDGE_BODY_TOO_LARGE");
  }
  const path = new URL(request.url).pathname;
  const canonical = [timestampText, nonce, request.method.toUpperCase(), path, await sha256Hex(bodyText)].join("\n");
  if (!await verifyHmac(secret, canonical, suppliedSignature)) {
    throw new Error("INVALID_BROKER_BRIDGE_SIGNATURE");
  }

  const receivedAt = new Date().toISOString();
  await env.DB.prepare("DELETE FROM broker_bridge_nonces WHERE received_at < ?")
    .bind(new Date(Date.now() - 10 * 60_000).toISOString()).run();
  const inserted = await env.DB.prepare(
    "INSERT OR IGNORE INTO broker_bridge_nonces(nonce,bridge_id,received_at) VALUES(?,?,?)",
  ).bind(nonce, bridgeId, receivedAt).run();
  if (!inserted.meta.changes) throw new Error("BROKER_BRIDGE_REPLAY_DETECTED");
  return { bridgeId, bodyText, receivedAt };
}
