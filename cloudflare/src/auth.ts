import type { AuthContext, Session } from "./types";
import { audit } from "./db";
import { randomId } from "./domain";

const SESSION_COOKIE = "ttwo_session";
const REAUTH_WINDOW_MS = 5 * 60 * 1000;
const LOGIN_WINDOW_MS = 10 * 60 * 1000;
const MAX_LOGIN_FAILURES = 5;

function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

function base64ToBytes(value: string): Uint8Array<ArrayBuffer> {
  const binary = atob(value);
  const bytes = new Uint8Array(new ArrayBuffer(binary.length));
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  return bytes;
}

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function sha256(value: string): Promise<string> {
  return bytesToHex(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value))));
}

function constantTimeEqual(left: Uint8Array, right: Uint8Array): boolean {
  let difference = left.length ^ right.length;
  const maximum = Math.max(left.length, right.length);
  for (let index = 0; index < maximum; index += 1) {
    difference |= (left[index] ?? 0) ^ (right[index] ?? 0);
  }
  return difference === 0;
}

export async function verifyPassword(password: string, encodedHash: string): Promise<boolean> {
  const [version, algorithm, iterationsText, saltText, expectedText] = encodedHash.split("$");
  const iterations = Number(iterationsText);
  if (version !== "v1" || algorithm !== "pbkdf2-sha256" || !Number.isInteger(iterations) || iterations < 600_000 || !saltText || !expectedText) {
    return false;
  }
  try {
    const salt = base64ToBytes(saltText);
    const expected = base64ToBytes(expectedText);
    if (salt.length < 16 || expected.length < 32) return false;
    const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveBits"]);
    const derived = new Uint8Array(await crypto.subtle.deriveBits(
      { name: "PBKDF2", hash: "SHA-256", salt, iterations },
      key,
      expected.length * 8,
    ));
    return constantTimeEqual(derived, expected);
  } catch {
    return false;
  }
}

function cookieValue(request: Request, name: string): string | null {
  const cookie = request.headers.get("Cookie") ?? "";
  for (const part of cookie.split(";")) {
    const [key, ...rest] = part.trim().split("=");
    if (key === name) return rest.join("=");
  }
  return null;
}

export async function authenticate(request: Request, env: Env): Promise<AuthContext | null> {
  const token = cookieValue(request, SESSION_COOKIE);
  if (!token) return null;
  const tokenHash = await sha256(token);
  const row = await env.DB.prepare(
    `SELECT id,csrf_token AS csrfToken,expires_at AS expiresAt,sensitive_authenticated_at AS sensitiveAuthenticatedAt
     FROM sessions WHERE token_hash=? AND revoked_at IS NULL AND expires_at>?`,
  ).bind(tokenHash, new Date().toISOString()).first<Session>();
  return row ? { session: row, cookieToken: token } : null;
}

export function requireCsrf(request: Request, auth: AuthContext): void {
  const supplied = request.headers.get("X-CSRF-Token") ?? "";
  if (!constantTimeEqual(new TextEncoder().encode(supplied), new TextEncoder().encode(auth.session.csrfToken))) {
    throw new Error("CSRF_INVALID");
  }
}

export function hasFreshSensitiveAuth(auth: AuthContext): boolean {
  return Date.now() - Date.parse(auth.session.sensitiveAuthenticatedAt) <= REAUTH_WINDOW_MS;
}

async function identityHash(request: Request, username: string): Promise<string> {
  return sha256(`${request.headers.get("CF-Connecting-IP") ?? "local"}:${username.toLowerCase()}`);
}

export async function login(request: Request, env: Env): Promise<Response> {
  const body = await request.json<{ username?: string; password?: string }>();
  const username = body.username ?? "";
  const identity = await identityHash(request, username);
  const cutoff = new Date(Date.now() - LOGIN_WINDOW_MS).toISOString();
  const failures = await env.DB.prepare(
    "SELECT count(*) AS total FROM login_attempts WHERE identity_hash=? AND success=0 AND attempted_at>?",
  ).bind(identity, cutoff).first<{ total: number }>();
  if ((failures?.total ?? 0) >= MAX_LOGIN_FAILURES) {
    await audit(env.DB, "LOGIN_FAILURE", "anonymous", null, { reason: "RATE_LIMITED" });
    return Response.json({ error: "LOGIN_RATE_LIMITED" }, { status: 429 });
  }
  const validUsername = constantTimeEqual(new TextEncoder().encode(username), new TextEncoder().encode(env.ADMIN_USERNAME));
  const validPassword = await verifyPassword(body.password ?? "", env.ADMIN_PASSWORD_HASH);
  const success = validUsername && validPassword;
  await env.DB.prepare("INSERT INTO login_attempts(id,identity_hash,attempted_at,success) VALUES(?,?,?,?)")
    .bind(randomId("login"), identity, new Date().toISOString(), success ? 1 : 0).run();
  if (!success) {
    await audit(env.DB, "LOGIN_FAILURE", "anonymous", null, { reason: "INVALID_CREDENTIALS" });
    return Response.json({ error: "INVALID_CREDENTIALS" }, { status: 401 });
  }
  const rawToken = bytesToBase64(crypto.getRandomValues(new Uint8Array(32)));
  const tokenHash = await sha256(rawToken);
  const csrfToken = bytesToBase64(crypto.getRandomValues(new Uint8Array(32)));
  const now = new Date();
  const maxAge = Number(env.SESSION_MAX_AGE_SECONDS || "43200");
  const sessionId = randomId("session");
  await env.DB.prepare(
    "INSERT INTO sessions(id,token_hash,csrf_token,created_at,expires_at,sensitive_authenticated_at) VALUES(?,?,?,?,?,?)",
  ).bind(sessionId, tokenHash, csrfToken, now.toISOString(), new Date(now.getTime() + maxAge * 1000).toISOString(), now.toISOString()).run();
  await audit(env.DB, "LOGIN_SUCCESS", "admin", null, { session_id: sessionId });
  return Response.json(
    { authenticated: true, csrf_token: csrfToken },
    { headers: { "Set-Cookie": `${SESSION_COOKIE}=${rawToken}; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=${maxAge}` } },
  );
}

export async function logout(auth: AuthContext, env: Env): Promise<Response> {
  await env.DB.prepare("UPDATE sessions SET revoked_at=? WHERE id=?").bind(new Date().toISOString(), auth.session.id).run();
  await audit(env.DB, "LOGOUT", "admin", null, { session_id: auth.session.id });
  return Response.json(
    { authenticated: false },
    { headers: { "Set-Cookie": `${SESSION_COOKIE}=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0` } },
  );
}

export async function reauthenticate(request: Request, auth: AuthContext, env: Env): Promise<Response> {
  const body = await request.json<{ password?: string }>();
  if (!(await verifyPassword(body.password ?? "", env.ADMIN_PASSWORD_HASH))) {
    await audit(env.DB, "LOGIN_FAILURE", "admin", null, { reason: "SENSITIVE_REAUTH_FAILED" });
    return Response.json({ error: "INVALID_CREDENTIALS" }, { status: 401 });
  }
  const timestamp = new Date().toISOString();
  await env.DB.prepare("UPDATE sessions SET sensitive_authenticated_at=? WHERE id=?").bind(timestamp, auth.session.id).run();
  return Response.json({ sensitive_authenticated_at: timestamp });
}
