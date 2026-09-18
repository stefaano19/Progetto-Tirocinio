---
name: wiki-query
description: Query the knowledge base wiki and synthesize an answer. Optionally file valuable answers back as new wiki pages. Use when the user wants to ask questions against the accumulated knowledge base.
license: MIT
compatibility: Requires knowledge-base/ wiki structure per AGENTS.md.
metadata:
  author: llm-wiki
  version: "1.0"
---

Query the knowledge base and synthesize a grounded answer.

**Input**: A question from the user. May be open-ended or specific.
If no question is provided, ask what they want to know.

---

## Steps

### 1. Read the index

```bash
cat knowledge-base/index.md
```

Scan all sections — concepts, entities, sources, decisions, questions, synthesis — and identify which pages are relevant to the question.

### 2. Read relevant pages

Read all pages identified as relevant. For broad questions, prefer synthesis and concept pages. For specific topics, drill into entity or source pages.

If an important page links to another page that might also be relevant, follow the link.

### 3. Query the knowledge graph (if available)

Check whether a graphify knowledge graph exists:

```bash
ls graphify-out/graph.json 2>/dev/null && echo "AVAILABLE" || echo "NOT_FOUND"
```

**If `graphify-out/graph.json` exists:**

Run graph queries to supplement wiki knowledge with code-level connections:

```bash
graphify query "<the user's question, or a derived sub-question>"
graphify explain "<entity mentioned in the question>"
graphify path "<concept-A>" "<concept-B>"   # for relationship questions
```

Read `graphify-out/GRAPH_REPORT.md` for broad architecture context (god nodes, surprising connections).

Merge graph findings with wiki findings in the synthesized answer. Cite the graph where it adds information the wiki doesn't yet contain. If the graph reveals a meaningful gap in the wiki, offer to file a new entity or concept page after answering.

**If the graph is not available:** skip this step entirely.

### 4. Check for related open questions

Scan `knowledge-base/pages/questions/` for any open questions that relate to what the user is asking. Surface them in the answer if relevant.

### 5. Synthesize the answer

Write a clear, grounded answer:
- Cite wiki pages using standard relative Markdown links (`[Title](path/to/page.md)`)
- Surface contradictions or unresolved tensions if they exist
- Distinguish between what the wiki confirms and what is uncertain
- Note any gaps: "The wiki does not have a page on X yet"

### 6. Choose the output format

Match the format to the question:

| Question type | Preferred format |
|---|---|
| Explanation or overview | Prose with headings |
| Comparison of options | Markdown table |
| Trade-off analysis | Table + prose |
| Timeline or sequence | Ordered list or ASCII diagram |
| Presentation-ready output | Marp slide deck |
| Visualization | ASCII diagram |

For Marp output, use:
```markdown
---
marp: true
theme: default
---
```

### 7. Offer to file the answer

If the answer is a valuable synthesis (comparison, analysis, discovered connection, cross-cutting overview), offer to save it:

> "This comparison looks useful to keep. Should I file it as `knowledge-base/pages/synthesis/<slug>.md`?"

If the user agrees:
- Create the synthesis page using the frontmatter conventions from `knowledge-base/AGENTS.md`
- Update `knowledge-base/index.md`
- Append to `knowledge-base/log.md`:
  ```
  ## [YYYY-MM-DD] query | <Question or Synthesis Title>
  Filed answer as [Synthesis Title](pages/synthesis/slug.md).
  ```

---

## Output

The synthesized answer, clearly structured, with:
- Citations to wiki pages
- Any caveats or gaps noted
- An offer to file if the answer is synthesis-worthy

---

## Guardrails

- **Ground answers in the wiki** — do not generate claims not supported by wiki pages or source summaries
- **Surface gaps honestly** — if the wiki doesn't cover something, say so and suggest whether a new source should be ingested
- **Do not hallucinate sources** — only cite pages that actually exist in `knowledge-base/pages/`
- **Preserve ambiguity** — if the wiki records an open question or contradiction, reflect that in the answer
- **Offer to file, don't auto-file** — let the user decide whether to save the answer as a page