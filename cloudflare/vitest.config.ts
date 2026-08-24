import { cloudflareTest, readD1Migrations } from "@cloudflare/vitest-plugin";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    cloudflareTest(async () => ({
      wrangler: { configPath: "./wrangler.jsonc" },
      miniflare: {
        bindings: {
          ADMIN_USERNAME: "admin",
          ADMIN_PASSWORD_HASH:
            "v1$pbkdf2-sha256$600000$AAECAwQFBgcICQoLDA0ODw==$yunIATdFlvF95Iuk7XBhaStdCrQzkyp9PN9pjf2Ls+g=",
          TEST_MIGRATIONS: await readD1Migrations("./migrations"),
        },
      },
    })),
  ],
  test: {
    setupFiles: ["./test/apply-migrations.ts"],
  },
});
