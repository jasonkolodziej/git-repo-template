#!/usr/bin/env python3
"""Assemble a static GitHub Pages site from the graphify graphs in this repository.

GitHub Pages only serves static files, so it cannot run an MCP server. What it can do
is publish the graph artifacts so that people (graph.html), agents with web access
(GRAPH_REPORT.md, llms.txt) and locally run MCP servers (graph.json) can fetch them.

Usage: python3 .github/graphify/build_site.py [OUTPUT_DIR]   (default: _site)
"""

from __future__ import annotations

import html
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TARGETS_FILE = Path(".github/graphify/targets.txt")
# Files and folders copied from each <dir>/graphify-out/ when present.
PUBLISHED_FILES = ("graph.json", "GRAPH_REPORT.md", "graph.html", "GRAPH_TREE.html")
PUBLISHED_DIRS = ("wiki",)
# Written into every site this script builds; only marked directories are ever replaced.
SITE_MARKER = ".graphify-site"


def repo_root() -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
        ).stdout.strip()
        return Path(out)
    except (OSError, subprocess.CalledProcessError):
        return Path.cwd()


def read_targets() -> list[str]:
    if not TARGETS_FILE.is_file():
        return []
    targets = []
    for line in TARGETS_FILE.read_text(encoding="utf-8").splitlines():
        fields = line.split("#", 1)[0].split()
        if not fields:
            continue
        target = fields[0].rstrip("/").removeprefix("./") or "."
        targets.append(target)
    return targets


def slug_for(target: str) -> str:
    return "_root" if target == "." else target


def copy_graph(target: str, site: Path) -> dict | None:
    source = Path(target) / "graphify-out"
    if not (source / "graph.json").is_file():
        print(f"skip {target}: no {source}/graph.json yet (run .github/graphify/update.sh {target})")
        return None

    dest = site / "graphs" / slug_for(target)
    dest.mkdir(parents=True, exist_ok=True)
    entry: dict = {"directory": target}
    for name in PUBLISHED_FILES:
        if (source / name).is_file():
            shutil.copy2(source / name, dest / name)
            entry[name] = f"graphs/{slug_for(target)}/{name}"
    for name in PUBLISHED_DIRS:
        if (source / name).is_dir():
            shutil.copytree(source / name, dest / name, dirs_exist_ok=True)
            entry[name] = f"graphs/{slug_for(target)}/{name}/index.md"
    print(f"published {target} -> {dest}")
    return entry


def write_index(site: Path, graphs: list[dict], meta: dict) -> None:
    rows = []
    for g in graphs:
        links = [
            f'<a href="{html.escape(g[key])}">{label}</a>'
            for key, label in (
                ("graph.html", "interactive graph"),
                ("GRAPH_REPORT.md", "report"),
                ("graph.json", "graph.json"),
                ("wiki", "wiki"),
            )
            if key in g
        ]
        rows.append(f"<li><code>{html.escape(g['directory'])}/</code> · {' · '.join(links)}</li>")
    body = "\n".join(rows) or "<li>No graphs have been built yet.</li>"
    title = html.escape(f"{meta['repository']} knowledge graphs")
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ color-scheme: light dark; --fg: #1f2328; --bg: #ffffff; --muted: #59636e; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --fg: #e6edf3; --bg: #0d1117; --muted: #9198a1; }} }}
  body {{ font: 16px/1.6 system-ui, sans-serif; color: var(--fg); background: var(--bg);
         max-width: 48rem; margin: 2rem auto; padding: 0 1rem; }}
  small, .muted {{ color: var(--muted); }}
  li {{ margin: .4rem 0; }}
</style>
</head>
<body>
<h1>{title}</h1>
<p class="muted">Built by <a href="https://github.com/Graphify-Labs/graphify">graphify</a>
from commit <code>{html.escape(meta['commit'][:12])}</code> on {html.escape(meta['generated_at'])}.</p>
<ul>
{body}
</ul>
<p><small>Machine-readable index: <a href="graphs.json">graphs.json</a> ·
agent summary: <a href="llms.txt">llms.txt</a>. This site is static: to query a graph over MCP,
download its <code>graph.json</code> and run <code>graphify-mcp</code> locally.</small></p>
</body>
</html>
"""
    (site / "index.html").write_text(page, encoding="utf-8")


def write_llms_txt(site: Path, graphs: list[dict], meta: dict) -> None:
    lines = [
        f"# {meta['repository']} knowledge graphs",
        "",
        "> graphify knowledge graphs for selected directories of this repository. Read a",
        "> GRAPH_REPORT.md for an architecture overview; load graph.json into `graphify-mcp`",
        "> or `graphify query --graph <file>` for scoped questions.",
        "",
        "## Graphs",
        "",
    ]
    for g in graphs:
        if "GRAPH_REPORT.md" in g:
            lines.append(f"- [{g['directory']}/ report]({g['GRAPH_REPORT.md']}): architecture summary")
        lines.append(f"- [{g['directory']}/ graph.json]({g['graph.json']}): full graph")
    (site / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare_output(site: Path) -> None:
    """Create an empty output dir, refusing anything this script did not generate.

    Guards against `build_site.py skills` or `build_site.py .` wiping source files.
    """
    resolved = site.resolve()
    root = Path.cwd().resolve()
    if resolved == root or resolved in root.parents:
        raise SystemExit(f"error: refusing to use {site} as output: it is the repository root or one of its parents")
    if site.is_symlink() or (resolved.exists() and not resolved.is_dir()):
        raise SystemExit(f"error: refusing to use {site} as output: it is not a plain directory")
    if resolved.exists() and any(resolved.iterdir()):
        if not (resolved / SITE_MARKER).is_file():
            raise SystemExit(
                f"error: refusing to overwrite {site}: it is not empty and was not generated by this script "
                f"(no {SITE_MARKER} marker). Pass a new or empty directory such as _site."
            )
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)
    (resolved / SITE_MARKER).write_text("generated by .github/graphify/build_site.py\n", encoding="utf-8")


def main() -> int:
    os.chdir(repo_root())
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
    prepare_output(site)

    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    meta = {
        "repository": os.environ.get("GITHUB_REPOSITORY") or Path.cwd().name,
        "commit": commit or "unknown",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }

    graphs = [g for t in read_targets() if (g := copy_graph(t, site))]
    (site / "graphs.json").write_text(json.dumps({**meta, "graphs": graphs}, indent=2) + "\n", encoding="utf-8")
    write_index(site, graphs, meta)
    write_llms_txt(site, graphs, meta)
    (site / ".nojekyll").touch()
    print(f"site written to {site}/ ({len(graphs)} graph(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
