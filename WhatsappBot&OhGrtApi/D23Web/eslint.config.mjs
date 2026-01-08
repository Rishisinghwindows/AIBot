import js from "@eslint/js"
import globals from "globals"
import tsParser from "@typescript-eslint/parser"
import reactHooks from "eslint-plugin-react-hooks"
import nextPlugin from "@next/eslint-plugin-next"

const nextRules = nextPlugin.configs["core-web-vitals"].rules

export default [
  {
    ignores: ["node_modules/**", ".next/**", "public/**", "components/ui/**"],
  },
  js.configs.recommended,
  {
    files: ["**/*.{ts,tsx,js,jsx}", "**/app/**", "**/components/**"],
    languageOptions: {
      parser: tsParser,
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        ...globals.browser,
        React: "writable",
      },
      parserOptions: {
        project: false,
      },
    },
    plugins: {
      "react-hooks": reactHooks,
      "@next/next": nextPlugin,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      ...nextRules,
      "@next/next/no-img-element": "off",
      "no-unused-vars": ["warn", { "args": "none", "varsIgnorePattern": "^_" }],
    },
  },
]
