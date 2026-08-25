const MAX_CALLBACK_BODY_BYTES = 512 * 1024;
const CALLBACK_WINDOW_SECONDS = 5 * 60;
const HEX_64 = /^[a-f0-9]{64}$/;
const NONCE = /^[A-Za-z0-9_-]{16,128}$/;
const ANALYSIS_ID = /^analysis-[a-f0-9]{24}$/;

function bytesToHex(bytes: ArrayBuffer): string {
  return [...new Uint8Array(bytes)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function constantTimeTextEqual(left: string, right: string): boolean {
  const leftBytes = new TextEncoder().encode(left);
  const rightBytes = new TextEncoder().encode(right);
  let difference = leftBytes.length ^ rightBytes.length;
  const maximum = Math.max(leftBytes.length, rightBytes.length);
  for (let index = 0; index < maximum; index += 1) {
    difference |= (leftBytes[index] ?? 0) ^ (rightBytes[index] ?? 0);
  }
  return difference === 0;
}

export async function sha256Hex(value: string | ArrayBuffer): Promise<string> {
  const bytes = typeof value === "string" ? new TextEncoder().encode(value) : value;
  return bytesToHex(await crypto.subtle.digest("SHA-256", bytes));
}

export async function hmacHex(secret: string, value: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  return bytesToHex(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(value)));
}

export interface VerifiedInternalRequest {
  analysisId: string;
  body: ArrayBuffer;
}

export async function verifyInternalRequest(
  request: Request,
  env: Env,
  expectedAnalysisId: string,
): Promise<VerifiedInternalRequest> {
  const secret = env.ANALYSIS_CALLBACK_SECRET?.trim() ?? "";
  if (!secret) throw new Error("ANALYSIS_CALLBACK_SECRET_NOT_CONFIGURED");
  if (!ANALYSIS_ID.test(expectedAnalysisId)) throw new Error("INVALID_ANALYSIS_REQUEST_ID");
  const timestamp = request.headers.get("X-TTWO-Timestamp") ?? "";
  const nonce = request.headers.get("X-TTWO-Nonce") ?? "";
  const contentHash = request.headers.get("X-TTWO-Content-SHA256") ?? "";
  const analysisId = request.headers.get("X-TTWO-Analysis-Id") ?? "";
  const signature = request.headers.get("X-TTWO-Signature") ?? "";
  if (
    analysisId !== expectedAnalysisId || !/^\d{10}$/.test(timestamp) || !NONCE.test(nonce) ||
    !HEX_64.test(contentHash) || !HEX_64.test(signature)
  ) throw new Error("INVALID_CALLBACK_AUTHENTICATION");
  const age = Math.abs(Math.floor(Date.now() / 1000) - Number(timestamp));
  if (age > CALLBACK_WINDOW_SECONDS) throw new Error("CALLBACK_TIMESTAMP_OUTSIDE_WINDOW");
  const declaredSize = Number(request.headers.get("Content-Length") ?? "0");
  if (Number.isFinite(declaredSize) && declaredSize > MAX_CALLBACK_BODY_BYTES) {
    throw new Error("CALLBACK_BODY_TOO_LARGE");
  }
  const body = await request.arrayBuffer();
  if (body.byteLength > MAX_CALLBACK_BODY_BYTES) throw new Error("CALLBACK_BODY_TOO_LARGE");
  const actualContentHash = await sha256Hex(body);
  if (!constantTimeTextEqual(actualContentHash, contentHash)) {
    throw new Error("CALLBACK_BODY_HASH_MISMATCH");
  }
  const pathname = new URL(request.url).pathname;
  const signedPayload = [
    timestamp,
    nonce,
    analysisId,
    request.method.toUpperCase(),
    pathname,
    contentHash,
  ].join("\n");
  const expectedSignature = await hmacHex(secret, signedPayload);
  if (!constantTimeTextEqual(expectedSignature, signature)) {
    throw new Error("INVALID_CALLBACK_SIGNATURE");
  }
  const receivedAt = new Date().toISOString();
  const pruneBefore = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  await env.DB.prepare("DELETE FROM analysis_callback_nonces WHERE received_at<?")
    .bind(pruneBefore).run();
  try {
    await env.DB.prepare(
      "INSERT INTO analysis_callback_nonces(nonce,analysis_request_id,received_at) VALUES(?,?,?)",
    ).bind(nonce, analysisId, receivedAt).run();
  } catch {
    throw new Error("CALLBACK_REPLAY_DETECTED");
  }
  return { analysisId, body };
}

export function decodeInternalJson(body: ArrayBuffer): unknown {
  if (!body.byteLength) return {};
  try {
    return JSON.parse(new TextDecoder().decode(body)) as unknown;
  } catch {
    throw new Error("INVALID_CALLBACK_JSON");
  }
}
