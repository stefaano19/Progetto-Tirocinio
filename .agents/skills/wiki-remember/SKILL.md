---
name: wiki-remember
description: Capture a fact, preference, or statement the user states directly in conversation into the knowledge base wiki, with no source document involved. Use when the user says "remember that...", "note that...", or asks to add/state something directly rather than ingesting a file.
license: MIT
compatibility: Requires knowledge-base/ wiki structure per AGENTS.md.
metadata:
  author: llm-wiki
  version: "1.0"
---

File a user-asserted statement into the wiki without a backing source document.

**Input**: A fact, preference, decision, or statement the user states directly
in the conversation. If the statement is vague, ask for enough specifics to
file it usefully (what it's about, why it matters).

---

## Steps

### 1. Capture the statement

Restate what you understood back to the user, verbatim where possible, to
confirm before filing it.

### 2. Read the index

```bash
cat knowledge-base/index.md
```

Identify which existing pages this statement is relevant to, and whether it
should update an existing page or create a new one.

### 3. Check for conflicts

If the statement contradicts an existing sourced claim, **do not silently
overwrite it**. Surface the conflict to the user and ask how to reconcile it
(e.g. "the wiki currently says X per [source], you're stating Y — should I
replace, add as an alternative view, or flag both?").

### 4. File a lightweight note source page

Even without a document, keep the "every claim traceable to a source"
principle from `knowledge-base/AGENTS.md`. Create
`knowledge-base/pages/sources/<slug>.md` using the source summary template,
with:

```markdown
**Type**: note
**Author(s)**: <user>, via conversation with the coding agent
**Date**: YYYY-MM-DD
**URL / Location**: conversation — no backing file
```

There is no file in `knowledge-base/raw/` and no move-to-processed step —
this step differs from `wiki-ingest` in that the "source" is the conversation
itself, not a document.

### 5. Update or create the relevant pages

Same pattern as `wiki-ingest` steps 7–10:
- Concept pages: update if exists, create if not
- Entity pages: update if exists, create if not
- Decision pages: create an ADR if this statement records a decision
- Question pages: create if the statement raises an open question

On every page touched or created from this statement, add `user-asserted` to
the `tags:` frontmatter list so it's distinguishable from externally sourced
claims during `wiki-lint` and `wiki-query`.

### 6. Update index.md

Add entries for every new page. Update the Statistics table.

### 7. Append to log.md

```markdown
## [YYYY-MM-DD] remember | <Title>

Statement: <the fact/preference captured, briefly>
Filed as: `pages/sources/<note-slug>.md`
Pages updated: <list new/updated concept/entity/decision/question pages>
```

---

## Output

Summarize:
- The statement as filed
- The note source page created
- Pages created/updated (with links)
- Whether this was flagged as a conflict with existing sourced content, and how it was resolved

---

## Guardrails

- **No source file required** — this skill exists precisely because not every
  fact comes from a document in `knowledge-base/raw/`
- **Still traceable** — always file a lightweight note source page so the
  statement's provenance (user, conversation, date) is recorded, not left implicit
- **Tag as user-asserted** — mark affected pages so readers can weigh a
  conversational assertion differently from an externally sourced claim
- **Never silently overwrite sourced claims** — surface contradictions and ask
  the user how to reconcile them
- **Update the index and log** — every remembered statement must be
  discoverable via `index.md` and traceable via `log.md`
