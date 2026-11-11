---
applyTo: "**/*.{ts,svelte}"
---
- TypeScript strict mode; no `any` without a comment explaining why.
- Svelte 5 runes syntax (`$state`, `$derived`, `$effect`, `$props`); no legacy `export let`.
- Manage dependencies only with `pnpm add` / `pnpm remove`.
<!-- TODO: project-specific TS/Svelte conventions -->
