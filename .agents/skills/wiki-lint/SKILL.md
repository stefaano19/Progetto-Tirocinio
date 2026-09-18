---
name: wiki-lint
description: Health-check the knowledge base wiki. Find contradictions, orphan pages, stale claims, missing cross-references, and data gaps. Use periodically to keep the wiki accurate and well-connected.
license: MIT
compatibility: Requires knowledge-base/ wiki structure per AGENTS.md.
metadata:
  author: llm-wiki
  version: "1.0"
---

Perform a health check on the knowledge base wiki.

**Input**: None required. Optionally the user may request a focused lint (e.g., "lint only concepts" or "check for OpenSpec conflicts").

---

## Steps

### 1. Load the full inventory

Read `knowledge-base/index.md` to get the complete list of pages.
Also scan the actual filesystem to catch any pages not yet listed in the index:

```bash
find knowledge-base/pages -name "*.md" | sort
```

### 2. Read recent log entries

```bash
grep "^## \[" knowledge-base/log.md | tail -20
```

Note what was recently ingested or changed, to focus attention.

### 3. Check for orphan pages

For each page, check whether any other page links to it using a standard
relative Markdown link (`[Title](path/to/page.md)`).
Pages with no inbound links are orphans — flag them.

```bash
# Example: check if decisions/001-use-postgres is referenced anywhere
grep -r "001-use-postgres" knowledge-base/pages/ --include="*.md" -l
```

### 4. Check for missing index entries

Compare pages found on disk vs pages listed in `index.md`.
Flag any page that exists on disk but has no index entry.

### 5. Check for stale claims

Scan concept and entity pages for:
- Claims tied to a source that was ingested long ago
- Claims that might be superseded by more recently ingested sources (check log dates)
- Frontmatter `updated` dates significantly older than the most recent relevant source ingest

Flag pages that may need a review.

### 6. Check for contradictions

Look for pages that make opposing claims about the same topic:
- Scan concept pages for conflicting definitions or descriptions
- Check decision pages: are any two decisions in conflict?
- Check if any open question has been implicitly answered by a decision (question should be marked resolved)

### 7. Check for missing concept pages

Scan all pages for Markdown links pointing at `pages/concepts/<concept-name>.md`
where no corresponding file exists (a dangling link).
These are concepts referenced but not yet given their own page.

Also look for recurring terms (mentioned 3+ times across pages) that lack a dedicated concept page.

### 8. Check for undocumented code entities (if graphify is available)

Check whether a knowledge graph exists:

```bash
ls graphify-out/graph.json 2>/dev/null && echo "AVAILABLE" || echo "NOT_FOUND"
```

**If `graphify-out/graph.json` exists:**

Read `graphify-out/GRAPH_REPORT.md` to identify god nodes (the most-connected concepts — everything flows through these) and other major codebase entities.

For each significant code entity, check whether an entity page exists in `knowledge-base/pages/entities/`:

```bash
ls knowledge-base/pages/entities/ | grep -i "<entity-name>"
```

Flag as a suggestion any god node or key component that lacks a wiki entity page. This is suggestions-only — not a blocking issue.

**If the graph is not available:** skip this step entirely.

### 9. Check for missing cross-references

For each page, scan its body for mentions of other existing pages' titles/slugs
that are not wrapped in a Markdown link (`[Title](path/to/page.md)`). Also check whether related
pages (e.g., a concept and the decisions/sources that reference it) fail to
link back to each other. Flag pages that should cross-reference each other but
currently don't.

### 10. Check for unresolved questions blocking specification work

Scan `knowledge-base/pages/questions/` for pages with `status: open`. For each,
check whether it's referenced by (or clearly relevant to) an active change
under `openspec/changes/` or an accepted spec under `openspec/specs/`. Flag any
open question that blocks drafting, syncing, or implementing a change.

### 11. Check for OpenSpec conflicts

Compare accepted specs in `openspec/specs/` against wiki pages:
- Does any wiki page contradict an accepted spec?
- Does any wiki decision record conflict with spec behavior?
- Are there open questions that block an accepted spec?

Flag any conflicts found.

### 12. Suggest new sources and investigations

Based on gaps found, suggest:
- Topics with thin coverage that would benefit from a new source
- Questions that could be resolved with a web search
- Concepts mentioned but not sourced

---

## Output Format

Structure the lint report as follows:

```markdown
# Wiki Lint Report — YYYY-MM-DD

## 🔴 Conflicts and Contradictions
[Pages or claims that directly conflict. These need attention now.]

## 🟡 Orphan Pages
[Pages with no inbound links. Consider linking them or merging/deleting.]

## 🟡 Missing Index Entries
[Pages on disk not in index.md.]

## 🟡 Stale Pages
[Pages whose content may be outdated relative to newer sources.]

## 🟡 Blocking Open Questions
[Open questions that block an active change or accepted spec.]

## 🔵 Missing Concept Pages
[Concepts referenced but lacking their own page.]

## 🔵 Missing Cross-References
[Pages that should link to each other but currently don't.]

## 🔵 Undocumented Code Entities
[God nodes or key codebase components (from graphify) without wiki entity pages. Suggestions only — only shown when graphify-out/graph.json exists.]

## 🔵 OpenSpec Conflicts
[Wiki content that contradicts accepted specs.]

## 💡 Suggestions
[New sources to seek, questions to investigate, improvements to consider.]

## ✅ Summary
- Total pages checked: N
- Issues found: N (X critical, Y warnings, Z suggestions)
- Recommended actions: [list]
```

### 13. Update log

Append to `knowledge-base/log.md`:

```markdown
## [YYYY-MM-DD] lint | Wiki health check

Pages checked: N
Issues found: X conflicts, Y orphans, Z stale pages, W missing concept pages
Action required: [summary of what needs fixing]
```

---

## Guardrails

- **Report, don't auto-fix** — surface issues clearly; let the user decide what to fix (except trivial missing index entries, which you may fix)
- **Be specific** — name the pages and cite the conflicting claims; don't be vague
- **Prioritize** — conflicts are critical; missing index entries, orphans, stale pages, and blocking open questions are warnings; missing concepts and missing cross-references are suggestions
- **Don't over-flag** — a page that was updated recently and has no issues is not worth mentioning
- **Check OpenSpec** — always include an OpenSpec conflict check unless the user explicitly scopes the lint to wiki-only