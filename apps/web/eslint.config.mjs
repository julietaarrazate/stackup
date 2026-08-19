import next from "eslint-config-next";

/**
 * Next 16 ships a native flat-config array from `eslint-config-next`
 * (bundling next core-web-vitals + next/typescript). We append our own
 * ignore patterns.
 */
const eslintConfig = [
  ...next,
  {
    ignores: [".next/**", "node_modules/**", "next-env.d.ts"],
  },
];

export default eslintConfig;
