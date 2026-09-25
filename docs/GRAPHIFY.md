# Repo knowledge graph (graphify)

A prebuilt knowledge graph of this repo, produced by `graphify`. Its purpose is
to let an agent orient itself from a small, verified map instead of re-reading
the whole tree every session. The output is plain JSON/Markdown/HTML — no
vendor-specific format — so any coding agent (Claude Code, Codex, Gemini CLI,
opencode, …) can use the same graph.

It is a **map, not the territory**: use it to find structure and connections,
but still open the real files before editing.

## Where it lives

| Path | What |
|---|---|
| `graphify-out/GRAPH_REPORT.md` | The map: god nodes, communities, surprising connections, gaps |
| `graphify-out/graph.json` | Raw graph (nodes / links / hyperedges + `built_at_commit`) |
| `graphify-out/graph.html` | Self-contained interactive view — open in any browser |
| `graphify-out/manifest.json` | What was scanned; drives incremental `graphify update` |
| `graphify-out/cache/` | Per-file extraction cache — what makes rebuilds cheap |

Built at commit `9c03b20` on branch `pron-lora-ar-only` (committed there and
rides into `main` on merge). The graph reflects the commit it was built at —
refresh it after meaningful changes (see below).

## Use it

- Structure / "how does X connect to Y" / "what are the load-bearing pieces":
  read `graphify-out/GRAPH_REPORT.md`, or run a scoped query (roughly ~5k tokens
  vs reading the tree):
  ```bash
  graphify query "<question>"
  ```
- Shortest path between two concepts: `graphify path "<A>" "<B>"`.
- Plain-language explanation of one node and its neighbours: `graphify explain "<X>"`.

## Refresh it

```bash
graphify update .     # re-extracts only changed files; reuses manifest.json + cache/
```

Run this before merging the branch, and at the end of a session that changed a
lot, so the graph never drifts far from the code.

## Enable it in another agent / environment

The artifact is agent-neutral, but the *integration* is per tool. One-time per
environment:

```bash
graphify install --platform claude|codex|gemini|opencode|aider|cursor|...
```

Or expose the graph live over MCP (all of the tools above speak MCP):

```bash
python -m graphify.serve graphify-out/graph.json   # stdio MCP server
```

where `python` is the interpreter that has `graphify` installed (see caveat 1).

## Caveats

1. `graphify-out/.graphify_python` is a **VM-specific** interpreter path and is
   git-ignored. On a fresh VM, delete it and let the skill re-resolve, or install
   `graphify` there.
2. The extraction cache is keyed by graphify version *and* extraction prompt — a
   version bump can miss cache and re-extract.
3. The graph is **branch-specific**. The 2026-09-25 build has a known gap: 135
   dangling-endpoint edges + 1 self-loop; a targeted re-extract would clean them.
4. Building / semantic extraction costs LLM tokens (~26k in / 9k out on the first
   build); `graphify update` is far cheaper because of the cache.
