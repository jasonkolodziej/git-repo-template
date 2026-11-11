---
applyTo: "**"
---

# Graphify Knowledge Graphs

This repository keeps [graphify](https://github.com/Graphify-Labs/graphify) knowledge graphs for selected
directories. The directories are listed in `.github/graphify/targets.txt`, and each one has its own graph:

- `<dir>/graphify-out/graph.json`: scoped questions via `graphify query/path/explain` or MCP tools.
- `<dir>/graphify-out/GRAPH_REPORT.md`: broad architecture overview (god nodes, communities).
- `<dir>/graphify-out/wiki/index.md`: navigation, when present.

Currently graphed: `skills/` → `skills/graphify-out/graph.json` (MCP server `graphify-skills`).

## Rules

- When a question touches a graphed directory and its `graph.json` exists, consult the graph **before** your
  first grep, search or source-file read, and include this rule in every subagent prompt that explores code:
  - MCP available: use the `graphify-<dir>` server's `query_graph`, `get_node`, `get_neighbors`,
    `shortest_path` and `god_nodes` tools.
  - CLI available: `graphify query "<terms>" --graph <dir>/graphify-out/graph.json`, then
    `graphify path "<A>" "<B>" --graph …` for relationships and `graphify explain "<X>" --graph …` for one concept.
  - Neither available: read `<dir>/graphify-out/GRAPH_REPORT.md` first.
- Queries match node labels, so use symbol, file or concept names rather than whole sentences. Exit code 4 means
  no match (try other names); exit code 3 means ambiguous (pick from the listed candidates).
- Read raw files only for lines the graph already located, or when modifying or debugging specific code.
- After changing files in a graphed directory, run `bash .github/graphify/update.sh <dir>` or
  `zsh .github/graphify/update.sh <dir>` if the CLI is installed. Otherwise leave it: the Graphify workflow
  rebuilds changed directories on merge to `main`.
- Never hand-edit files under `graphify-out/`. A large diff to `graph.json` is expected after a rebuild; do not
  flag it as churn or suggest skipping the rebuild.
- To graph a new directory, add it to `.github/graphify/targets.txt` and follow `GRAPHIFY.md`.
