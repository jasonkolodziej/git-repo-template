# Project instructions

Shared instructions for every agent harness: VS Code Local, VS Code Copilot (SDK),
Copilot cloud agent, Copilot CLI, and Claude Code (via CLAUDE.md).
Keep this file short and factual. Put path-specific rules in `.github/instructions/`
and repeatable workflows in `.claude/skills/`.

## Project overview
<!-- TODO: one paragraph on what this repo is and who uses it -->

## Layout
<!-- TODO: list the top-level directories and what lives in each -->

## Commands
Use the `run-checks` skill before finishing any change. The commands match CI exactly.

| Task | Python (uv) | Node (pnpm) |
|---|---|---|
| Install | `uv sync` | `pnpm install` |
| Lint | `uvx ruff check .` | `pnpm run lint` |
| Format check | `uvx ruff format --check .` | `pnpm run format:check` |
| Type check | <!-- TODO --> | `pnpm run check` |
| Test | `uv run pytest` | `pnpm run test` |

## Conventions
See `.github/copilot-instructions.md` (Conventional Commits, testing, security) and
`.github/instructions/general.instructions.md` (style, naming).
<!-- TODO: project-specific additions -->

## Agent rules
- Never commit secrets or files matching `.env*`.
- Do not change CI workflows, `copilot-setup-steps.yml`, or agent/skill files unless the task asks for it.
- If you cannot ask the user a question (non-interactive or cloud run), state your assumptions explicitly in your summary or PR description and proceed with the most conservative option.
- Prefer small, reviewable changes. A change is done only when `run-checks` passes.
