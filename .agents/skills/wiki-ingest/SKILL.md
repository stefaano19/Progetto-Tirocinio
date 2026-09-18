---
name: wiki-ingest
description: Ingest a raw source document into the knowledge base wiki. Use when the user drops a file in knowledge-base/raw/ and wants it processed.
license: MIT
compatibility: Requires knowledge-base/ wiki structure per AGENTS.md.
metadata:
  author: llm-wiki
  version: "1.0"
---

Ingest a raw source document into the knowledge base.

**Input**: A filename in `knowledge-base/raw/` OR a path the user specifies.
If the user provides no file, list files in `knowledge-base/raw/` (excluding `processed/`) and ask which one to process.

---

## Steps

### 1. Identify the source

If no file is specified:
```bash
ls knowledge-base/raw/ | grep -v "^processed$" | grep -v "^assets$" | grep -v "^\.gitkeep$"
```
Ask the user which file to ingest.

### 2. Read the source

Read the source document fully. For markdown files, use the view tool. For images, view them directly. For large files, read in sections.

### 3. Discuss with the user (interactive mode)

Briefly summarize what you found:
- Main topic and scope
- Key points (3–5 bullets)
- What domain concepts and entities appear
- Whether it looks spec-worthy (should it become an OpenSpec change?)

Ask if the user wants to adjust emphasis before you write.

### 4. Read the index

```bash
cat knowledge-base/index.md
```

Identify which existing pages this source is relevant to.

### 5. Check for supersession of an existing source

Compare the new source's title/topic against the Sources section of
`index.md`. Look for a match on the same topic (a newer edition, an updated
report, a revised transcript, etc.), or the user explicitly saying this
source replaces/updates an earlier one.

**If a match is found**, confirm with the user before proceeding. On confirmation:

- Open the **old** source page and set `status: superseded`, pointing
  `superseded_by` at the new source page using this project's page-reference
  convention (plain relative path — see `knowledge-base/AGENTS.md` → "Page
  Frontmatter"). Add a one-line notice near
  the top referencing the new source, in the same convention: `⚠️ Superseded
  by <link to new source> on YYYY-MM-DD.`
- The **new** source page (created in step 6) will get `status: current` and
  a `supersedes` field pointing back at the old source page, same convention.
- Note which concept/entity pages cite the old source — their claims will be
  reviewed and updated in steps 7–8 below, not just the source pages themselves.

See `knowledge-base/AGENTS.md` → "Superseding a Source" for the full convention.

**If no match is found:** skip this step entirely — this is a brand-new source.

### 6. Query the knowledge graph (if available)

Check whether a graphify knowledge graph has been built for this project:

```bash
ls graphify-out/graph.json 2>/dev/null && echo "AVAILABLE" || echo "NOT_FOUND"
```

**If `graphify-out/graph.json` exists:**

Run targeted queries for the key concepts and entities found in the source:

```bash
graphify query "<key concept from the source>"
graphify explain "<significant entity or component>"
graphify path "<concept-A>" "<concept-B>"   # when two concepts seem related
```

Read `graphify-out/GRAPH_REPORT.md` for a broad architecture overview (god nodes, surprising connections, design rationale nodes).

Use graph findings to enrich wiki pages:
- Add code-level connections to the source summary's "Connections to Existing Pages" section
- Create or update entity pages for significant codebase entities discovered
- Note graph relationships in concept pages under "Where It Appears in This Project"
- If the graph reveals a surprising connection the source doesn't mention, flag it as an open question

**If the graph is not available:** skip this step entirely.

### 7. Create the source summary page

File: `knowledge-base/pages/sources/<slug>.md`

Use the source summary template from `knowledge-base/AGENTS.md`. The slug is a kebab-case version of the source title.

If step 5 found this source supersedes an earlier one, set `status: current`
and a `supersedes` field pointing at the old source page (see
`knowledge-base/AGENTS.md` → "Page Frontmatter" for the exact reference form
this project uses).

### 8. Update or create concept pages

For each significant concept mentioned in the source:
- If a concept page exists: open it, add new information, update `updated` date, add the source to the `sources` frontmatter list
- If no concept page exists: create `knowledge-base/pages/concepts/<concept-name>.md` using the concept template
- If this source supersedes an old one (step 5) and the concept page cited the old source: replace or update the claim with what changed, keep the old source listed only if it still adds historical context, and append a `## Corrections` entry noting the update per `knowledge-base/AGENTS.md`

### 9. Update or create entity pages

For each significant entity (tool, system, person, company) mentioned:
- Same pattern as concept pages: update if exists, create if not, propagate supersession updates from step 5 the same way

### 10. Update or create decision pages

If the source records or implies an architectural or design decision:
- Create `knowledge-base/pages/decisions/<NNN>-<slug>.md` using the decision template
- Number sequentially (check the highest existing number)

### 11. Create question pages for open unknowns

If the source raises unresolved questions relevant to the project:
- Create `knowledge-base/pages/questions/<slug>.md` using the question template

### 12. Update index.md

Add entries for every new page created. Update the Statistics table.
Keep each section sorted as documented in `knowledge-base/AGENTS.md`.
If step 5 applied, reflect the old source's `(status: superseded)` in its index entry.

### 13. Append to log.md

```markdown
## [YYYY-MM-DD] ingest | <Source Title>

Source: `knowledge-base/raw/<filename>`
Pages created: <list new pages>
Pages updated: <list updated pages>
Key topics: <brief description>
Spec-worthy: yes / no / maybe — <reason>
Supersedes: <reference to the old source page, in this project's convention> — omit this line when the source doesn't supersede anything
```

### 14. Move the source

```bash
mv "knowledge-base/raw/<filename>" "knowledge-base/raw/processed/<filename>"
```

### 15. Relocate any referenced assets

`knowledge-base/raw/assets/` holds Confluence attachments (images,
spreadsheets, csv exports, etc.) downloaded alongside pages — never
markdown pages themselves. Scan the source's body for links pointing at
`assets/<filename>`. For every asset the page actually references, move
it from `knowledge-base/raw/assets/` to `knowledge-base/raw/processed/assets/`
so it stays alongside the now-processed page instead of being left
behind in the loose `raw/assets/` pool:

```bash
mv "knowledge-base/raw/assets/<referenced-filename>" "knowledge-base/raw/processed/assets/<referenced-filename>"
```

Leave any asset in `raw/assets/` that the source does not reference —
it may belong to a different page not yet ingested.

---

## Output

After completing ingestion, summarize:
- Source title and file
- Pages created (with links)
- Pages updated (with links)
- Whether this source supersedes an earlier one, and what changed
- Whether this source raises any OpenSpec-worthy topics
- Next suggested action (e.g., "Use `wiki-lint` to check for new orphans" or "This looks spec-worthy — use `openspec-propose` to draft a change")

---

## Guardrails

- **Never modify** files in `knowledge-base/raw/` (only read + move to processed)
- **Never invent claims** — only write what the source actually says
- **Always link** — every new page must link to related pages; no orphans
- **Always update** the `updated` frontmatter field on modified pages
- **Flag conflicts** — if the source contradicts an existing page or accepted spec, document the conflict clearly and do not silently resolve it
- **Flag spec-worthy content** — if the source contains implementation requirements, architecture decisions, or behavioral constraints, say so explicitly
- **Assets are media, not sources** — never treat a file in `knowledge-base/raw/assets/` as something to ingest on its own; only move it once its referencing page has been processed
- **Confirm supersession, don't assume it** — always ask the user before marking an existing source `superseded`; a similar topic doesn't automatically mean it replaces the old one
- **Corrections leave a trail** — when propagating a supersession into concept/entity pages, append a `## Corrections` entry rather than silently rewriting the claim
