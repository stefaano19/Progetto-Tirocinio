---
applyTo: "**"
---

# Spec-Driven Development

## Trigger

Apply this instruction when the request explores, proposes, changes, validates,
syncs, or archives an OpenSpec change. Do not apply it to unrelated coding or
repository-maintenance tasks.

## Required context

Before exploring or proposing a change:

1. Read `AGENTS.md` and, when present, `knowledge-base/AGENTS.md`.
2. Inspect `knowledge-base/index.md` and relevant wiki pages; use the
   `wiki-query` skill when it is available.
3. Check accepted specifications and active changes for overlap or conflicts.
4. Use Graphify context when `graphify-out/graph.json` is present.
5. Record material evidence, assumptions, gaps, and conflicts in the OpenSpec
   artifacts rather than silently resolving them.

## Workflow

Use the OpenSpec skills installed under `.agents/skills/`:

- `openspec-explore` to investigate a change;
- `openspec-propose` to create its proposal and related artifacts;
- `openspec-apply-change`, `openspec-sync-specs`, and
  `openspec-archive-change` for later lifecycle stages.

`AGENTS.md` remains authoritative. If an existing repository instruction
conflicts with it, surface the conflict and ask for direction before proceeding.
