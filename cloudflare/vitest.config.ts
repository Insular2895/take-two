import { cloudflareTest, readD1Migrations } from "@cloudflare/vitest-plugin";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    cloudflareTest(async () => ({
      wrangler: { configPath: "./wrangler.jsonc" },
      miniflare: {
        bindings: {
          TEST_MIGRATIONS: await readD1Migrations("./migrations"),
          ACTION_PASSWORD_VERIFIER: "v1$hmac-sha256$BwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwc$yXxGMhJsIjUD7xzr7aV5eTPfQ7gtwCXYw7O0nKMJtMw",
        },
      },
    })),
  ],
  test: {
    setupFiles: ["./test/apply-migrations.ts"],
  },
});
