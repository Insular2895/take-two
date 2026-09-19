import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const roots = ["src", "public"];
const forbidden = [
  /\bplaceOrder\b/,
  /\bsubmitOrder\b/,
  /\bcancelOrder\b/,
  /\bmodifyOrder\b/,
  /\bexerciseOptions\b/,
];
const violations = [];
let governedPaperTransmitLiterals = 0;

function scan(path) {
  for (const entry of readdirSync(path)) {
    const target = join(path, entry);
    if (statSync(target).isDirectory()) scan(target);
    else if (/\.(ts|js|html|txt)$/.test(entry)) {
      const contents = readFileSync(target, "utf8");
      for (const expression of forbidden) if (expression.test(contents)) violations.push(`${target}: ${expression}`);
      const transmitMatches = contents.match(/transmit\s*:\s*true/g) || [];
      if (transmitMatches.length) {
        const isolated = target === join("src", "paper-entry.ts") &&
          transmitMatches.length === 1 &&
          contents.includes("status: \"CONFIRMED\"") &&
          contents.includes("dispatch_authorized: false") &&
          contents.includes("paper_runtime_default: \"DISABLED\"");
        if (!isolated) violations.push(`${target}: ungoverned transmit:true literal`);
        else governedPaperTransmitLiterals += 1;
      }
    }
  }
}

for (const root of roots) scan(root);
if (violations.length) {
  process.stderr.write(`Forbidden broker capability detected:\n${violations.join("\n")}\n`);
  process.exit(1);
}
if (governedPaperTransmitLiterals !== 1) {
  process.stderr.write("Exactly one locked PAPER_ENTRY command builder is required.\n");
  process.exit(1);
}
process.stdout.write(
  "Worker scan passed: no broker SDK call; one locked PAPER_ENTRY command builder; runtime disabled.\n",
);
