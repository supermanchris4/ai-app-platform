/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Built as a library: one ES module, with React and React Router left for the application to provide
// (peer dependencies), so the application and the package share one copy of each. The type
// declarations are written by `tsc -p tsconfig.build.json`.
const external = [/^react($|\/)/, /^react-dom($|\/)/, /^react-router($|\/)/];

export default defineConfig({
  plugins: [react()],
  build: {
    lib: { entry: "src/index.ts", formats: ["es"], fileName: "index" },
    rolldownOptions: { external },
    sourcemap: true,
    emptyOutDir: true,
  },
  test: {
    include: ["src/**/*.test.{ts,tsx}"],
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
    restoreMocks: true,
    unstubGlobals: true,
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/**/*.test.{ts,tsx}", "src/test/**", "src/test-setup.ts", "src/index.ts"],
      thresholds: { lines: 80, functions: 80, branches: 80, statements: 80 },
    },
  },
});
