# CLAUDE.md

Project guidance for Claude Code. Shared agent rules live in `.github/` so Claude and GitHub Copilot read the
same source; they are imported here.

@.github/copilot-instructions.md
@.github/instructions/graphify.instructions.md

Setup and maintenance of the knowledge graphs is described in [GRAPHIFY.md](GRAPHIFY.md). The project-scoped
MCP server `graphify-skills` is declared in `.mcp.json`; it needs `graphify-mcp` on PATH
(`pipx install "graphifyy[mcp]"`).
