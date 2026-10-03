---
name: run-checks
description: Run the same lint, format, type-check, and test commands that CI runs. Use before declaring any code change finished, after fixing a failing check, or when asked to verify the project builds.
---
# Run checks

These commands mirror `.github/workflows/ci.yml`. If a command here and CI disagree, CI is correct — update this file.

## Always (the `Lint & Validate` job)
1. Every `*.yml` / `*.yaml` file parses: `python3 -c "import yaml, pathlib, sys; [yaml.safe_load(pathlib.Path(f).read_text()) for f in sys.argv[1:]]" $(git ls-files '*.yml' '*.yaml')`
2. No secret-looking values in YAML/JSON (see the `Check for secret patterns` step in `ci.yml`).

## Detect the stack
- `pyproject.toml` at the repo root → run the **Python** section.
- `package.json` at the repo root → run the **Node** section.
- Both present → run both.

## Python (uv)
1. `uv sync`
2. `uvx ruff check .`
3. `uvx ruff format --check .`
4. If a `tests/` directory exists: `uv run pytest -q`

## Node (pnpm)
1. `pnpm install --frozen-lockfile`
2. `pnpm run --if-present lint`
3. `pnpm run --if-present format:check`
4. `pnpm run --if-present check`
5. `pnpm run --if-present test`

## On failure
- Fix the cause, then re-run only the failing command, then the full list once more.
- Never weaken a check (disabling rules, skipping tests, loosening types) to make it pass unless the task explicitly asks for it.
- Report which commands ran and their results in your final summary.
