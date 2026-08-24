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

const password = await hiddenPrompt("Admin password: ");
const confirmation = await hiddenPrompt("Confirm password: ");
if (password !== confirmation) throw new Error("Passwords do not match.");
if (password.length < 14) throw new Error("Use at least 14 characters.");
const iterations = 600_000;
const salt = randomBytes(16);
const derived = pbkdf2Sync(password, salt, iterations, 32, "sha256");
process.stdout.write(`v1$pbkdf2-sha256$${iterations}$${salt.toString("base64")}$${derived.toString("base64")}\n`);
