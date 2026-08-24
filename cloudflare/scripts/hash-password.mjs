import { pbkdf2Sync, randomBytes } from "node:crypto";

function hiddenPrompt(label) {
  if (!process.stdin.isTTY) throw new Error("Run password:hash from an interactive terminal.");
  return new Promise((resolve, reject) => {
    const input = process.stdin;
    const characters = [];
    process.stdout.write(label);
    input.setRawMode(true);
    input.resume();
    input.setEncoding("utf8");
    const onData = (character) => {
      if (character === "\u0003") {
        input.setRawMode(false);
        reject(new Error("Cancelled."));
      } else if (character === "\r" || character === "\n") {
        input.setRawMode(false);
        input.pause();
        input.off("data", onData);
        process.stdout.write("\n");
        resolve(characters.join(""));
      } else if (character === "\u007f") {
        characters.pop();
      } else {
        characters.push(character);
      }
    };
    input.on("data", onData);
  });
}

const password = await hiddenPrompt("Admin password: ");
const confirmation = await hiddenPrompt("Confirm password: ");
if (password !== confirmation) throw new Error("Passwords do not match.");
if (password.length < 14) throw new Error("Use at least 14 characters.");
const iterations = 600_000;
const salt = randomBytes(16);
const derived = pbkdf2Sync(password, salt, iterations, 32, "sha256");
process.stdout.write(`v1$pbkdf2-sha256$${iterations}$${salt.toString("base64")}$${derived.toString("base64")}\n`);
