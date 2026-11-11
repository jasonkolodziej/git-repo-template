# Graphify

This template uses [graphify](https://github.com/Graphify-Labs/graphify) to give every coding agent a shared
knowledge graph of selected directories. The agents covered are Claude Code (local and on the web), GitHub
Copilot Chat in VS Code, and the Copilot cloud agent on github.com. Agents query a scoped subgraph instead of
grepping and reading many files, which saves tokens and surfaces how files relate.

Each directory in [`.github/graphify/targets.txt`](.github/graphify/targets.txt) gets its own graph:

```text
<dir>/graphify-out/
├── graph.json        # the graph: read by `graphify query` and the MCP server (committed)
├── GRAPH_REPORT.md   # plain-language architecture summary (committed)
├── graph.html        # interactive visualization (committed)
└── cache/            # extraction cache (git-ignored)
```

In this template repository the test target is `skills/`.

## What the template ships

| File | Purpose |
| --- | --- |
| `.github/graphify/targets.txt` | Directories to graph, with an optional per-directory mode (`code-only` / `full`) |
| `.github/graphify/update.sh` | Rebuilds all, selected, or only changed targets. Used by VS Code and CI |
| `.github/graphify/build_site.py` | Builds a static GitHub Pages site from the graphs |
| `.github/workflows/graphify.yml` | Rebuilds graphs on push to `main` (changed dirs only) and on PRs; manual runs; optional Pages publish |
| `.github/workflows/copilot-setup-steps.yml` | Installs graphify for the Copilot cloud agent |
| `.github/instructions/graphify.instructions.md` | Agent rules: query the graph first. Read by Copilot (VS Code and cloud) and imported by `CLAUDE.md` |
| `CLAUDE.md` | Imports the shared Copilot instructions and graphify rules for Claude Code |
| `.mcp.json` | Claude Code project MCP server (`graphify-skills`) |
| `.vscode/mcp.json` | VS Code / Copilot Chat MCP server (`graphify-skills`) |
| `.vscode/mcp-config.json` | MCP JSON to paste into the Copilot cloud agent settings |
| `.vscode/tasks.json` | `graphify: …` tasks for manual updates, queries, watch mode and a local MCP HTTP server |
| `.graphifyignore` | Paths graphify skips (e.g. the vendored graphify skill source in `.agents/`) |

## After creating a repository from this template

Work through this checklist once. The one-time `setup.yml` workflow renames the repo but does not touch
graphify.

### 1. Choose the directories to graph

Edit `.github/graphify/targets.txt`. Use one line per directory, with the mode as an optional second column:

```text
src
services/api   code-only
docs           full
skills         full
```

- **`code-only`** (default) uses local tree-sitter AST extraction. It needs no API key, sends nothing off the
  runner, and takes seconds. Markdown, PDFs and images are **skipped**.
- **`full`** also sends documents, papers and images to an LLM for semantic extraction, and names communities
  with the LLM. Use it for prose-heavy directories such as `docs/` or `skills/`. Without an API key it falls
  back to `code-only` with a warning.
- **`.`** graphs the whole repository. Check `.graphifyignore` first.

Keep `skills` if you kept the bundled skills, or remove the line if you deleted them. To stop tracking a
directory, remove its line and delete `<dir>/graphify-out/`.

### 2. Configure the GitHub Action

Go to **Settings → Secrets and variables → Actions**:

| Name | Kind | Needed for |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY` | secret | `full` mode (any one) |
| `GRAPHIFY_MODE` | variable | default mode when a target has no column (`code-only`) |
| `GRAPHIFY_BACKEND` | variable | force a backend (`claude`, `openai`, `gemini`, …) when several keys are set |
| `GRAPHIFY_VERSION` | variable | pin the `graphifyy` version (recommended once you are happy with output) |
| `GRAPHIFY_PAGES` | variable | `true` to publish to GitHub Pages after every `main` build (step 6) |

The workflow commits graph updates back to `main` as `github-actions[bot]`. If `main` is protected, allow
GitHub Actions to bypass the rule. If you can't, change the commit step to open a pull request instead (for
example with `peter-evans/create-pull-request`).

### 3. Build the first graphs

Either run **Actions → Graphify → Run workflow** (leave *targets* blank to build every directory), or build
locally and commit the result:

```bash
pipx install "graphifyy[mcp,anthropic,openai,gemini]"
```

```bash
bash .github/graphify/update.sh
```

```bash
git add -- '*graphify-out/*' && git commit -m "chore(graphify): initial knowledge graphs"
```

### 4. Register one MCP server per graphed directory

`graphify-mcp` serves a single `graph.json`, so add one entry per target. Name them `graphify-<dir>`, and
copy the `graphify-skills` entry in each of these files:

- **VS Code / Copilot Chat:** `.vscode/mcp.json`, using `${workspaceFolder}/<dir>/graphify-out/graph.json`.
- **Claude Code:** `.mcp.json`, using a path relative to the repo root. Alternatively, run
  `claude mcp add --transport stdio graphify-<dir> -- graphify-mcp "$PWD/<dir>/graphify-out/graph.json"`.
- **Copilot cloud agent:** paste the `mcpServers` object from `.vscode/mcp-config.json` into
  **Settings → Copilot → Coding agent → MCP configuration**. `copilot-setup-steps.yml` already installs
  `graphify-mcp` on the agent's runner.

If you have many directories, you can instead merge them into one graph with
`graphify merge-graphs a/graphify-out/graph.json b/graphify-out/graph.json --out graphify-out/merged-graph.json`
and serve that file.

### 5. Point the agent rules at your directories

Update the "Currently graphed" line in `.github/instructions/graphify.instructions.md`. `CLAUDE.md` imports
this file, so Claude Code and Copilot read the same rules.

### 6. Optional: publish graphs to GitHub Pages

1. **Settings → Pages → Build and deployment → Source:** select **GitHub Actions**.
2. Set the `GRAPHIFY_PAGES` variable to `true`, or tick *publish-pages* on a manual run.

The site contains `index.html` (links to each `graph.html`), `graphs.json` (a machine-readable index),
`llms.txt`, and a copy of every `graph.json` and `GRAPH_REPORT.md`. See
[Hosting an MCP server via GitHub Pages](#hosting-an-mcp-server-via-github-pages) for what Pages can and
cannot do.

> [!WARNING]
> Pages sites are public on most GitHub plans, even for private repositories. A graph exposes your code's
> structure and symbol names. Only enable Pages for public repositories, or on GitHub Enterprise Cloud with
> private Pages.

## Keeping graphs up to date

### Manually in VS Code

Open **Terminal → Run Task…** and pick:

| Task | What it does |
| --- | --- |
| `graphify: install CLI` | installs `graphify` + `graphify-mcp` (with watch mode and the Anthropic/OpenAI/Gemini clients) via uv, pipx or pip |
| `graphify: update all targets` | rebuilds every directory in `targets.txt` |
| `graphify: update targets changed vs origin/main` | rebuilds only directories with changes on your branch |
| `graphify: update one directory…` | prompts for a directory and mode |
| `graphify: query…` | runs `graphify query` against one directory's graph |
| `graphify: watch directory (auto-rebuild code)` | `graphify watch <dir>` (needs the `watch` extra) |
| `graphify: serve MCP over HTTP (localhost:8099)` | Streamable HTTP MCP endpoint at `http://127.0.0.1:8099/mcp` |
| `graphify: build Pages site locally (_site/)` | previews what the Pages job would publish |

The same script works from any shell:

```bash
bash .github/graphify/update.sh --help
```

### Automatically with GitHub Actions

`.github/workflows/graphify.yml` runs on these events:

- **Push to `main`:** diffs the push and rebuilds only the targets with changed files. A change to
  `targets.txt` rebuilds every target. It then commits changed `graphify-out/` files with `[skip ci]`.
  Commits that only touch `graphify-out/` don't trigger it.
- **Pull request:** rebuilds changed targets and uploads them as the `graphify-out` artifact for review.
  Nothing is committed. Runs from forks get no secrets, so they always use `code-only`.
- **Manual run:** builds the directories you list (or all of them) with an optional mode override, and can
  publish to Pages.

### Locally on every commit (optional)

`graphify hook install` only rebuilds a graph at the **repository root** (`./graphify-out/`). For
per-directory graphs, use a small post-commit hook instead:

```bash
printf '#!/bin/sh\nbash .github/graphify/update.sh --code-only --changed HEAD~1 >/dev/null 2>&1 &\n' > .git/hooks/post-commit && chmod +x .git/hooks/post-commit
```

If your only target is `.`, the built-in hooks work. Run `graphify hook install` and check the result with
`graphify hook status`.

## Using the graph from each agent

### Claude Code (CLI, desktop, VS Code extension)

- `CLAUDE.md` imports the graphify rules, and `.mcp.json` declares `graphify-skills`. Approve the server the
  first time Claude Code asks.
- **Optional:** run `graphify claude install` for PreToolUse hooks that nudge Claude to query the graph before
  it greps or reads files. Use `graphify install --project --strict` to block the first raw read until a query
  has run. These hooks write **absolute paths** into `.claude/settings.json`, so keep them in
  `.claude/settings.local.json` rather than committing them.
- **Optional:** run `graphify install` to add the `/graphify` skill to `~/.claude/skills/`.

### Claude Code on the web (cloud sessions)

The container doesn't include graphify. Add this to the environment's setup script:

```bash
pip install "graphifyy[mcp]"
```

The committed graphs are then available as soon as the session starts. Without the CLI, Claude follows the
fallback rule and reads `GRAPH_REPORT.md`.

### GitHub Copilot Chat in VS Code

- `chat.instructionsFilesLocations` in `.vscode/settings.json` loads `.github/instructions/`, so the graphify
  rules apply automatically.
- `.vscode/mcp.json` starts `graphify-skills`. With `chat.mcp.autostart`, it starts once `graphify-mcp` is
  installed. Run the **graphify: install CLI** task first.
- **Optional:** run `graphify vscode install` to add the `/graphify` chat skill to your user profile.

### GitHub Copilot cloud agent (github.com)

- `copilot-setup-steps.yml` installs `graphifyy[mcp]` before the agent starts.
- The agent reads `.github/copilot-instructions.md` and `.github/instructions/*.instructions.md`.
- Add the MCP JSON from `.vscode/mcp-config.json` in the repository's Copilot settings (step 4).

### Other agents

`graphify <platform> install` writes the always-on rules for other tools. Platforms include `codex`,
`cursor`, `gemini`, `opencode`, `kiro`, `aider` and `copilot` (Copilot CLI). Run `graphify --help` for the
full list. Most of them write `AGENTS.md`.

## Hosting an MCP server via GitHub Pages

**Short answer: GitHub Pages cannot host an MCP server. It can host the graph files that an MCP server reads.**

### Why not

- Pages serves pre-built static files from a CDN, and it runs no server code. Jekyll is a build step, not a
  runtime.
- MCP needs either a local process (stdio) or an HTTP endpoint that accepts **`POST`** JSON-RPC requests and
  answers with JSON or an SSE stream (Streamable HTTP). Pages only answers `GET`/`HEAD`, can't read request
  bodies, and can't check an `Authorization` header.
- So `graphify-mcp --transport http` has nowhere to run on Pages, and you can't keep a private Pages endpoint
  behind an API key.

### What works

| Option | How | Trade-offs |
| --- | --- | --- |
| **A. Static graphs on Pages + local stdio server** (shipped) | The workflow publishes `graphs/<dir>/graph.json`. Download it and run `graphify-mcp` locally (example below). | Free, no infra. Every agent still runs its own process. The graph is public. |
| **B. Pages as a read-only "API" for agents with web access** (shipped) | Agents fetch `llms.txt`, `graphs.json` and `GRAPH_REPORT.md` over HTTPS. | No MCP tools (no `query_graph`), just documents. Good enough for an overview. |
| **C. Self-hosted Streamable HTTP server** | Run `graphify-mcp <graph.json> --transport http --host 0.0.0.0 --api-key "$GRAPHIFY_API_KEY"` on any container host (Docker, Cloud Run, Fly.io, Cloudflare Containers). Pull the graph from Pages or the repo on a schedule; the server reloads `graph.json` when it changes. | Real shared MCP endpoint with an API key. You run the server and should put TLS in front of it. |
| **D. Edge function reading the Pages graph** | A Cloudflare Worker (see the `cloudflare` / `agents-sdk` skills) that implements MCP and fetches `graph.json` from Pages. | Serverless and cheap, but you reimplement graphify's query tools. |
| **E. Hosted graphify** | Graphify's own hosted MCP service. | No infra. Your code is indexed by a third party, on a paid plan beyond the free tier. |

Option A, connecting a local agent to a published graph:

```bash
mkdir -p ~/.cache/graphify-remote && curl -fsSL "https://<owner>.github.io/<repo>/graphs/skills/graph.json" -o ~/.cache/graphify-remote/skills.json
```

```bash
claude mcp add --transport stdio graphify-skills-remote -- graphify-mcp "$HOME/.cache/graphify-remote/skills.json"
```

Option C, smoke-testing an HTTP server locally (the same command runs in a container):

```bash
GRAPHIFY_API_KEY="$(openssl rand -hex 32)" graphify-mcp skills/graphify-out/graph.json --transport http --port 8099
```

MCP clients then connect to `http://<host>:8099/mcp` and send `Authorization: Bearer <key>`.

## Testing in this template repository

`skills/` is the test target, with mode `full`. It is almost entirely Markdown, so:

- **Without** an LLM key, the build runs in code-only mode and only graphs the handful of `.ts`, `.sh`,
  `.json`, `.yml` and `.toml` files. That shows the pipeline works but gives a sparse graph.
- **With** `ANTHROPIC_API_KEY` (or another key) set as a repository secret, every `SKILL.md` and reference doc
  is extracted semantically and the communities are named. Expect a one-off LLM cost on the first build;
  later builds re-extract only changed files.

To try it:

1. Merge to `main`, or run **Actions → Graphify → Run workflow** with *targets* = `skills`.
2. Check that `skills/graphify-out/graph.json` and `GRAPH_REPORT.md` were committed.
3. Run `graphify query "cloudflare workers" --graph skills/graphify-out/graph.json` locally, or ask Copilot or
   Claude a question about the skills and confirm it uses the `graphify-skills` tools.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `graphify CLI not found` | Run the **graphify: install CLI** task, or `pipx install "graphifyy[mcp]"`. The PyPI package name has two y's. |
| `graphify-mcp: command not found` | Reinstall with the MCP extra: `uv tool install --reinstall "graphifyy[mcp]"`. |
| MCP server fails to start | The graph doesn't exist yet. Build it first (step 3). |
| `query` exits 4 (`No matching nodes found`) | Use symbol, file or concept names, not whole sentences. |
| `query` exits 3 | The name is ambiguous. Use one of the listed candidates. |
| Workflow can't push | `main` is protected. See step 2. |
| `full` target built as code-only | No API key secret is visible to the run. Fork PRs never get one, and run with `GRAPHIFY_BACKEND=none`. |
| `GRAPHIFY_BACKEND='…' is not a built-in backend or a configured custom provider` | Fix the name, or define the provider with `graphify provider add`. In CI there is no `~/.graphify/providers.json`: commit `.graphify/providers.json`, set `GRAPHIFY_ALLOW_LOCAL_PROVIDERS=1` in the workflow `env`, and pass the provider's `env_key` secret. |
| `the 'anthropic' package is required for this backend` | Install the matching extra: `pipx install --force "graphifyy[mcp,anthropic,openai,gemini]"`. |
| Graph shrank after deleting files and the update was refused | Rebuild with `GRAPHIFY_FORCE=1`, e.g. `GRAPHIFY_FORCE=1 bash .github/graphify/update.sh <dir>`. |

## References

- Vibe coding setup: <https://docs.graphify.com/open-source/vibe-coding>
- MCP server: <https://docs.graphify.com/open-source/mcp-server>
- Source and issues: <https://github.com/Graphify-Labs/graphify>
