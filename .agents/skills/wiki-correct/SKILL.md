---
name: wiki-correct
description: Correct a wrong wiki page or retract an inaccurate source in the knowledge base. Use when the user says a page is wrong, a claim is outdated/incorrect, or a source document itself turns out to be inaccurate.
license: MIT
compatibility: Requires knowledge-base/ wiki structure per AGENTS.md.
metadata:
  author: llm-wiki
  version: "1.0"
---

Fix inaccurate wiki content without silently rewriting history.

**Input**: A page, claim, or source the user says is wrong. If the user gives
no specifics, ask what's wrong and where they saw it.

---

## Steps

### 1. Identify what's wrong

Ask (if not already clear):
- Which page(s) or source is affected?
- Is the **wiki's interpretation** wrong (the source is fine, the page
  mis-stated or misapplied it), or is the **source itself** wrong/outdated
  (the document it was built from is inaccurate)?

This distinction determines the rest of the workflow — see
`knowledge-base/AGENTS.md` → "Corrections and Retractions".

### 2. Read the affected page(s)

Read the full page content, its frontmatter, and its `sources:` list.
If a source is implicated, read `knowledge-base/pages/sources/<slug>.md` too.

### 3. Check blast radius

```bash
grep -rl "<page-slug>" knowledge-base/pages/ --include="*.md"
```

Find every other page that links to or cites the affected page/source, so the
correction can be propagated everywhere it matters, not just on one page.

### 4a. Case: wiki mis-stated something (source is fine)

- Fix the content directly on the affected page(s).
- Update the `updated` frontmatter field.
- Append (or create) a `## Corrections` section with a dated entry:
  `- YYYY-MM-DD: <what changed and why>`.
- Do not touch the source page or the file in `knowledge-base/raw/processed/`.

### 4b. Case: the source itself is wrong

- **Never edit or delete** the immutable file under `knowledge-base/raw/processed/`.
- Set the source summary page's frontmatter `status: retracted`.
- Add a `## ⚠️ Retraction Notice` section near the top of the source summary
  page: what's wrong, when flagged, and (if known) what replaces it.
- For every concept/entity/decision page citing this source (from step 3):
  - If the claim is now unsupported, remove it or replace it with corrected
    information (ask the user for the correct fact if it's not otherwise known).
  - Append a `## Corrections` entry describing what was removed/changed and why.
  - Remove the retracted source from `sources:` unless the page still needs it
    for historical context (in which case keep it, but don't rely on it alone).
- If no corrected information exists yet for a removed claim, create a
  `knowledge-base/pages/questions/<slug>.md` page capturing the gap using the
  question template, and link it from the affected page(s).
- Check whether the retracted source underpins an **accepted** OpenSpec spec
  (`openspec/specs/`) or Spec-Kit spec. If so, **do not modify the spec** —
  flag the conflict explicitly to the user per root `AGENTS.md` §8.

### 5. Update index.md

Reflect any status changes (e.g. a source's entry may need a `(status: retracted)`
suffix) and any new question pages created.

### 6. Append to log.md

```markdown
## [YYYY-MM-DD] correct | <Title>

Target: <page(s) or source corrected>
Reason: <what was wrong>
Pages updated: <list updated pages, including any new question pages>
Source retracted: yes / no — <source slug, if yes>
```

---

## Output

Summarize:
- What was wrong and why
- Every page touched, with a link
- Any new question page filed for an unresolved gap
- Any flagged conflict with an accepted spec (not auto-resolved)

---

## Guardrails

- **Never edit or delete files in `knowledge-base/raw/`** — sources are immutable; retract via frontmatter/notice, not by rewriting the source file
- **Never silently rewrite** — every correction leaves a `## Corrections` trail with date and reason
- **Full blast radius** — fix every page that cites the wrong claim, not just the one the user pointed at
- **Don't invent the correct fact** — if the true information isn't known, file an open question instead of guessing
- **Don't touch accepted specs** — flag conflicts with `openspec/specs/` or accepted Spec-Kit specs instead of modifying them
- **Update the index and log** — every correction must be discoverable via `index.md` and traceable via `log.md`