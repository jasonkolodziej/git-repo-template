# git-repo-template

GitHub repo template setup for all git-repos

## Included CI Checks

The default GitHub Actions workflow in `.github/workflows/ci.yml` runs:

- YAML validation for `.yml` and `.yaml` files (via PyYAML)
- Basic secret-pattern scanning across YAML/JSON sources while excluding common generated/vendor paths
- **Python (uv)** — `ruff check`, `ruff format --check`, `pytest` — only when `pyproject.toml` exists at the root
- **Node (pnpm)** — `lint`, `format:check`, `check`, `test` scripts — only when `package.json` exists at the root

The `run-checks` skill (`.claude/skills/run-checks/SKILL.md`) mirrors these commands so every agent runs what CI runs.

## Agent workspace

Scaffolding that works across the VS Code **Local** harness, the VS Code **Copilot** (SDK) harness, the
**Copilot cloud agent**, Copilot CLI, and Claude Code.

| Path | Purpose | Read by |
|---|---|---|
| `AGENTS.md` | Canonical project instructions | Local, Copilot, Cloud, CLI |
| `CLAUDE.md` | Imports `AGENTS.md` | Claude Code |
| `.github/copilot-instructions.md` | Repo-wide Copilot instructions | Local, Copilot, Cloud, CLI |
| `.github/instructions/*.instructions.md` | Path-scoped rules (`applyTo` globs) | Local, Copilot, Cloud |
| `.github/agents/ask-portable.agent.md` | Read-only Q&A agent | Local, Copilot, Cloud |
| `.github/agents/plan-portable.agent.md` | Read-only planning agent | Local, Copilot, Cloud |
| `.claude/skills/run-checks/SKILL.md` | Runs the same checks as CI | Local, Copilot, Cloud, CLI, Claude Code |
| `.vscode/mcp.json` | MCP servers for VS Code (`servers` key) | Local, Copilot |
| `.mcp.json` | MCP servers for Claude Code (`mcpServers` key, no-auth servers only) | Claude Code |
| `.github/copilot/cloud-mcp.json` | Source of truth for the cloud agent's MCP config | Pasted into GitHub repo settings |
| `.github/workflows/ci.yml` | YAML/secret checks plus per-stack lint, format, type-check, test | Gate for every harness's output |
| `.github/workflows/copilot-setup-steps.yml` | Toolchain install for the cloud agent | Cloud |
| `.vscode/settings.json` | Editor/extension settings plus worktree settings for Copilot-harness sessions | VS Code |
| `.worktreeinclude` | Ignored files copied into Claude Code worktrees | Claude Code |

`.venv` is deliberately not symlinked into worktrees: an editable install inside it points back at the
original checkout, so a worktree session would test the wrong code. Only `node_modules` is symlinked.

### Portability rules

Agent files (`.github/agents/*.agent.md`):

- Frontmatter: `name`, `description`, `tools` only. **No `target`** (unset = available everywhere).
  No `handoffs`, `argument-hint`, `model`, `infer`, or `disable-model-invocation`.
- `tools`: aliases only (`read`, `search`, `edit`, `execute`, `agent`, `web`) plus `github/*`,
  written as a YAML block list. VS Code-only tool IDs do nothing in other harnesses.
- Body: no `#tool:` references; include a fallback for non-interactive (cloud) runs.
- `---` must be the very first line, or VS Code's Markdown validator reports "No link definition found".

Everything else:

- Put new repeatable workflows in skills, not `.prompt.md` files (prompt files are IDE-only).
- Put guardrails you need everywhere in CI, not hooks (hook schemas differ per harness).
- Claude Code reads skills only from `.claude/skills/`; the vendored skills in `.agents/skills/` are not visible to it.

### Setup checklist (repos created from this template)

1. Fill in the `TODO` sections of `AGENTS.md` and both language `.instructions.md` files.
2. Edit `ci.yml` and the `run-checks` skill together so their commands match.
3. Node projects: set `packageManager` in `package.json` (`pnpm/action-setup` reads the version from it)
   and commit `pnpm-lock.yaml` (`--frozen-lockfile` and the `pnpm` cache need it).
4. Add MCP servers to `.vscode/mcp.json`, `.mcp.json`, **and** `.github/copilot/cloud-mcp.json`, then paste the
   latter into **GitHub repo → Settings → Copilot → Cloud agent → MCP configuration**
   (the cloud agent does not read `.mcp.json`). Store server secrets as `COPILOT_MCP_*` secrets in the
   repo's `copilot` environment.
5. Run `copilot-setup-steps.yml` once from the Actions tab to confirm it succeeds.
6. Protect `main` and require the CI jobs to pass.
7. In your **user** (not workspace) VS Code settings, choose your default harness:
   `"chat.editor.preferCopilotHarness": false` keeps Local as the default.

### Verify per harness

- **Local**: new chat → target Local → agent picker lists `ask-portable` and `plan-portable`.
- **Copilot**: new chat → target Copilot → same two agents appear; type `/` to see SDK commands.
- **Cloud**: assign an issue to Copilot, or use `/delegate` from a Copilot session → the PR description
  should show `run-checks` results and CI should run on the PR.

### Known unverified points

- `git.worktreeIncludeFiles` / `git.worktreeSymlinkFolders`: neither setting name nor value shape
  (arrays of globs here) could be confirmed from public docs. If the Settings UI greys them out, remove them.
- The `web` tool alias may not be available on the cloud agent. If a validator flags it, remove it from both agent files.
- Cloud MCP secret references: `.github/copilot/cloud-mcp.json` passes `COPILOT_MCP_SHADCN_SVELTE` as a bare
  name. Check the current GitHub docs for whether `$COPILOT_MCP_…` syntax is required.

## What are Agent Skills?

Agent Skills are a lightweight, open format for extending AI agent capabilities with specialized knowledge and workflows.

At its core, a skill is a folder containing a `SKILL.md` file. This file includes metadata (`name` and `description`, at minimum) and instructions that tell an agent how to perform a specific task. Skills can also bundle scripts, reference materials, templates, and other resources.

```text
my-skill/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── ...               # Any additional files or directories
```

## Why Agent Skills?

Agents are increasingly capable, but often don't have the context they need to do real work reliably. Skills solve this by packaging procedural knowledge and company-, team-, and user-specific context into portable, version-controlled folders that agents load on demand. This gives agents:

* **Domain expertise**: Capture specialized knowledge — from legal review processes to data analysis pipelines to presentation formatting — as reusable instructions and resources.
* **Repeatable workflows**: Turn multi-step tasks into consistent, auditable procedures.
* **Cross-product reuse**: Build a skill once and use it across any skills-compatible agent.

## How do Agent Skills work?

Agents load skills through **progressive disclosure**, in three stages:

1. **Discovery**: At startup, agents load only the name and description of each available skill, just enough to know when it might be relevant.

2. **Activation**: When a task matches a skill's description, the agent reads the full `SKILL.md` instructions into context.

3. **Execution**: The agent follows the instructions, optionally executing bundled code or loading referenced files as needed.

Full instructions load only when a task calls for them, so agents can keep many skills on hand with only a small context footprint.

## Modifying Template Repo

The standard approach for template repos is a GitHub Actions setup workflow that triggers on the first push to the default branch, skips if running in the template repo itself, performs the substitutions, commits the result, then deletes itself.

The flow:

1. New repo created from template → GitHub creates an initial commit
2. The bundled [setup.yml](.github/workflows/setup.yml) workflow fires on that push
3. It detects it's not the template repo (via github.repository check)
   1. Trigger: `push` to `main` — GitHub fires this automatically when the new repo receives its first commit after being created from the template.
   2. Guard (`if: github.repository != 'jasonkolodziej/git-repo-template'`): prevents the workflow from running inside the template repo itself on every push.
4. Replaces the `# git-repo-template` header (and any other placeholders) with the actual repo name
5. Commits back and self-deletes so it never runs again.
   1. **Self-deletion:** after committing the substitutions, the workflow git rms itself and pushes — so it never runs again in the child repo. The child repo's CI (ci.yml) takes over from that point.
   2. **Extending it:** add more `sed` / `find` lines in the Replace template placeholders step for any other tokens you want to swap out (e.g., owner name, year, license holder).
