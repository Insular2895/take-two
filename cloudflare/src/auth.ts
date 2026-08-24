import type { AuthContext } from "./types";

const CSRF_COOKIE = "__Host-ttwo_csrf";
const CSRF_MAX_AGE_SECONDS = 24 * 60 * 60;
const REAUTH_WINDOW_MS = 5 * 60 * 1000;
const LOCAL_ACCESS_AUD = "local-take-two-control";
const CSRF_TOKEN_PATTERN = /^[A-Za-z0-9_-]{43}$/;

function bytesToBase64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}

function constantTimeEqual(left: Uint8Array, right: Uint8Array): boolean {
  let difference = left.length ^ right.length;
  const maximum = Math.max(left.length, right.length);
  for (let index = 0; index < maximum; index += 1) {
    difference |= (left[index] ?? 0) ^ (right[index] ?? 0);
  }
  return difference === 0;
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
