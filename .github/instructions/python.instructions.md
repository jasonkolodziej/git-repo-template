---
applyTo: "**/*.py"
---
- Target the Python version pinned in `pyproject.toml`; manage dependencies only with `uv add` / `uv remove`.
- Use type hints on all public functions.
- Lint and format with ruff; do not add other formatters.
<!-- TODO: project-specific Python conventions -->
