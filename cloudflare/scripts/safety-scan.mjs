import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const roots = ["src", "public"];
const forbidden = [
  /\bplaceOrder\b/,
  /\bsubmitOrder\b/,
  /\bcancelOrder\b/,
  /\bmodifyOrder\b/,
  /\bexerciseOptions\b/,
  /transmit\s*:\s*true/,
];
const violations = [];

function scan(path) {
  for (const entry of readdirSync(path)) {
    const target = join(path, entry);
    if (statSync(target).isDirectory()) scan(target);
    else if (/\.(ts|js|html)$/.test(entry)) {
      const contents = readFileSync(target, "utf8");
      for (const expression of forbidden) if (expression.test(contents)) violations.push(`${target}: ${expression}`);
    }
  }
}

for (const root of roots) scan(root);
if (violations.length) {
  process.stderr.write(`Forbidden broker capability detected:\n${violations.join("\n")}\n`);
  process.exit(1);
}
process.stdout.write("Safety boundary scan passed: preview-only, transmit=false.\n");
