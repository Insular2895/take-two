import { createHmac, randomBytes } from "node:crypto";
import { chmodSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const SECRET_NAME = "ACTION_PASSWORD_VERIFIER";
const MINIMUM_PASSWORD_LENGTH = 14;
const MAXIMUM_PASSWORD_LENGTH = 128;

function hiddenPrompt(label) {
  if (!process.stdin.isTTY) throw new Error("Run action-password:set from an interactive terminal.");
  return new Promise((resolve, reject) => {
    const input = process.stdin;
    const characters = [];
    process.stdout.write(label);
    input.setRawMode(true);
    input.resume();
    input.setEncoding("utf8");
    const finish = () => {
      input.setRawMode(false);
      input.pause();
      input.off("data", onData);
    };
    const onData = (data) => {
      for (const character of data) {
        if (character === "\u0003") {
          finish();
          process.stdout.write("\n");
          reject(new Error("Cancelled."));
          return;
        }
        if (character === "\r" || character === "\n") {
          finish();
          process.stdout.write("\n");
          resolve(characters.join(""));
          return;
        }
        if (character === "\u007f" || character === "\b") {
          if (characters.length > 0) {
            characters.pop();
            process.stdout.write("\b \b");
          }
        } else {
          characters.push(character);
          process.stdout.write("*");
        }
      }
    };
    input.on("data", onData);
  });
}

function createVerifier(password) {
  const key = randomBytes(32);
  const digest = createHmac("sha256", key).update(password, "utf8").digest();
  return `v1$hmac-sha256$${key.toString("base64url")}$${digest.toString("base64url")}`;
}

function writeLocalVerifier(verifier) {
  const path = join(process.cwd(), ".dev.vars");
  const current = existsSync(path) ? readFileSync(path, "utf8") : "";
  const retained = current
    .split(/\r?\n/)
    .filter((line) => line && !line.startsWith(`${SECRET_NAME}=`));
  retained.push(`${SECRET_NAME}=${JSON.stringify(verifier)}`);
  writeFileSync(path, `${retained.join("\n")}\n`, { encoding: "utf8", mode: 0o600 });
  chmodSync(path, 0o600);
}

function putRemoteVerifier(verifier) {
  const executable = join(
    process.cwd(),
    "node_modules",
    ".bin",
    process.platform === "win32" ? "wrangler.cmd" : "wrangler",
  );
  if (!existsSync(executable)) throw new Error("Run npm install before action-password:set.");
  const result = spawnSync(executable, ["secret", "put", SECRET_NAME], {
    cwd: process.cwd(),
    input: `${verifier}\n`,
    stdio: ["pipe", "inherit", "inherit"],
  });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error("Cloudflare secret update failed.");
}

const localOnly = process.argv.includes("--local-only");
const password = await hiddenPrompt("Action password: ");
const confirmation = await hiddenPrompt("Confirm action password: ");
if (password !== confirmation) throw new Error("Passwords do not match.");
if (password.length < MINIMUM_PASSWORD_LENGTH) {
  throw new Error(`Use at least ${MINIMUM_PASSWORD_LENGTH} characters.`);
}
if (password.length > MAXIMUM_PASSWORD_LENGTH) {
  throw new Error(`Use at most ${MAXIMUM_PASSWORD_LENGTH} characters.`);
}

const verifier = createVerifier(password);
if (!localOnly) putRemoteVerifier(verifier);
writeLocalVerifier(verifier);
process.stdout.write(
  localOnly
    ? "Local action-password verifier saved to ignored .dev.vars.\n"
    : "Action-password verifier stored in Cloudflare and ignored local .dev.vars. The password was not stored.\n",
);
