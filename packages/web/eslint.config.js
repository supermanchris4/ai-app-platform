import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "coverage"] },
  {
    files: ["**/*.{ts,tsx}"],
    extends: [js.configs.recommended, ...tseslint.configs.strictTypeChecked],
    languageOptions: {
      globals: globals.browser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: { "react-hooks": reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "no-restricted-globals": [
        "error",
        { name: "localStorage", message: "Personal information is never stored in the browser." },
        { name: "sessionStorage", message: "Personal information is never stored in the browser." },
      ],
    },
  },
  {
    // The package holds no application's code, so it imports only itself and its packages.
    files: ["src/**"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/*", "../../*"],
              message: "The package imports only its own modules and its declared packages.",
            },
          ],
        },
      ],
    },
  },
);
