import type { AuthContext } from "./types";
import { audit } from "./db";
import { randomId } from "./domain";

const CSRF_COOKIE = "__Host-ttwo_csrf";
const CSRF_MAX_AGE_SECONDS = 24 * 60 * 60;
const REAUTH_WINDOW_MS = 5 * 60 * 1000;
const LOCAL_ACCESS_AUD = "local-take-two-control";
const CSRF_TOKEN_PATTERN = /^[A-Za-z0-9_-]{43}$/;
const ACTION_PASSWORD_HEADER = "X-Action-Password";
const ACTION_PASSWORD_WINDOW_MS = 15 * 60 * 1000;
const MAX_ACTION_PASSWORD_FAILURES = 5;
const ACTION_PASSWORD_MIN_LENGTH = 14;
const ACTION_PASSWORD_MAX_LENGTH = 128;

function bytesToBase64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}

function base64UrlToBytes(value: string): Uint8Array<ArrayBuffer> {
  if (!/^[A-Za-z0-9_-]+$/.test(value)) throw new Error("INVALID_BASE64URL");
  const padded = value.replaceAll("-", "+").replaceAll("_", "/").padEnd(Math.ceil(value.length / 4) * 4, "=");
  const binary = atob(padded);
  const bytes = new Uint8Array(new ArrayBuffer(binary.length));
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  return bytes;
}

async function sha256(value: string): Promise<string> {
  return bytesToBase64Url(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value))));
}

function constantTimeEqual(left: Uint8Array, right: Uint8Array): boolean {
  let difference = left.length ^ right.length;
  const maximum = Math.max(left.length, right.length);
  for (let index = 0; index < maximum; index += 1) {
    difference |= (left[index] ?? 0) ^ (right[index] ?? 0);
  }
  return difference === 0;
}

export async function verifyActionPassword(password: string, encodedVerifier: string): Promise<boolean> {
  if (password.length < ACTION_PASSWORD_MIN_LENGTH || password.length > ACTION_PASSWORD_MAX_LENGTH) return false;
  const [version, algorithm, keyText, expectedText, extra] = encodedVerifier.split("$");
  if (version !== "v1" || algorithm !== "hmac-sha256" || !keyText || !expectedText || extra !== undefined) return false;
  try {
    const keyBytes = base64UrlToBytes(keyText);
    const expected = base64UrlToBytes(expectedText);
    if (keyBytes.length !== 32 || expected.length !== 32) return false;
    const key = await crypto.subtle.importKey(
      "raw",
      keyBytes,
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign"],
    );
    const actual = new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(password)));
    return constantTimeEqual(actual, expected);
  } catch {
    return false;
  }
}

export async function requireActionPassword(
  request: Request,
  env: Env,
  auth: AuthContext,
  action: string,
): Promise<void> {
  const verifier = env.ACTION_PASSWORD_VERIFIER?.trim() ?? "";
  if (!verifier) throw new Error("ACTION_PASSWORD_NOT_CONFIGURED");

  const password = request.headers.get(ACTION_PASSWORD_HEADER) ?? "";
  if (!password) throw new Error("ACTION_PASSWORD_REQUIRED");

  const identityHash = await sha256(`action-password:${auth.email}`);
  const cutoff = new Date(Date.now() - ACTION_PASSWORD_WINDOW_MS).toISOString();
  await env.DB.prepare(
    "DELETE FROM action_password_attempts WHERE identity_hash=? AND attempted_at<=?",
  ).bind(identityHash, cutoff).run();
  const attemptId = randomId("action-auth");
  const attemptedAt = new Date().toISOString();
  const reservation = await env.DB.prepare(
    `INSERT INTO action_password_attempts(id,identity_hash,attempted_at,action)
     SELECT ?,?,?,?
     WHERE (SELECT count(*) FROM action_password_attempts WHERE identity_hash=? AND attempted_at>?) < ?
     RETURNING id`,
  ).bind(
    attemptId,
    identityHash,
    attemptedAt,
    action,
    identityHash,
    cutoff,
    MAX_ACTION_PASSWORD_FAILURES,
  ).first<{ id: string }>();
  if (!reservation) throw new Error("ACTION_PASSWORD_RATE_LIMITED");

  if (!(await verifyActionPassword(password, verifier))) {
    const failures = await env.DB.prepare(
      "SELECT count(*) AS total FROM action_password_attempts WHERE identity_hash=? AND attempted_at>?",
    ).bind(identityHash, cutoff).first<{ total: number }>();
    const rateLimited = (failures?.total ?? 0) >= MAX_ACTION_PASSWORD_FAILURES;
    await audit(env.DB, rateLimited ? "ACTION_PASSWORD_RATE_LIMITED" : "ACTION_PASSWORD_FAILURE", auth.actor, null, { action });
    if (rateLimited) throw new Error("ACTION_PASSWORD_RATE_LIMITED");
    throw new Error("ACTION_PASSWORD_INVALID");
  }

  await env.DB.prepare("DELETE FROM action_password_attempts WHERE identity_hash=?").bind(identityHash).run();
  await audit(env.DB, "ACTION_PASSWORD_ACCEPTED", auth.actor, null, { action });
}

function cookieValue(request: Request, name: string): string | null {
  const cookie = request.headers.get("Cookie") ?? "";
  for (const part of cookie.split(";")) {
    const [key, ...rest] = part.trim().split("=");
    if (key === name) return rest.join("=");
  }
  return null;
}

export async function authenticateAccess(
  request: Request,
  access: CloudflareAccessContext | undefined,
): Promise<AuthContext | null> {
  if (!access) return null;
  const identity = await access.getIdentity();
  const email = typeof identity?.email === "string" ? identity.email.trim().toLowerCase() : "";
  if (!email) return null;

  const suppliedCsrf = cookieValue(request, CSRF_COOKIE);
  const csrfToken = suppliedCsrf && CSRF_TOKEN_PATTERN.test(suppliedCsrf)
    ? suppliedCsrf
    : bytesToBase64Url(crypto.getRandomValues(new Uint8Array(32)));
  const issuedAtSeconds = typeof identity?.iat === "number" && Number.isFinite(identity.iat)
    ? identity.iat
    : access.aud === LOCAL_ACCESS_AUD ? Date.now() / 1000 : 0;

  return {
    actor: `access:${email}`,
    email,
    csrfToken,
    csrfCookieNeedsSet: csrfToken !== suppliedCsrf,
    accessIssuedAt: issuedAtSeconds * 1000,
  };
}

export function attachCsrfCookie(response: Response, auth: AuthContext): Response {
  if (!auth.csrfCookieNeedsSet) return response;
  const secured = new Response(response.body, response);
  secured.headers.append(
    "Set-Cookie",
    `${CSRF_COOKIE}=${auth.csrfToken}; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=${CSRF_MAX_AGE_SECONDS}`,
  );
  return secured;
}

export function requireCsrf(request: Request, auth: AuthContext): void {
  const supplied = request.headers.get("X-CSRF-Token") ?? "";
  if (!constantTimeEqual(new TextEncoder().encode(supplied), new TextEncoder().encode(auth.csrfToken))) {
    throw new Error("CSRF_INVALID");
  }
}

export function hasFreshSensitiveAuth(auth: AuthContext): boolean {
  const age = Date.now() - auth.accessIssuedAt;
  return age >= 0 && age <= REAUTH_WINDOW_MS;
}
