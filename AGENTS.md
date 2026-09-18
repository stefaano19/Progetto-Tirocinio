# Spec-Driven Agent Contract

This file defines how coding agents should operate inside a project that uses this workflow.

Read this file at the start of each session.  
If present, also read `knowledge-base/AGENTS.md` for wiki-specific conventions.

**Precedence**: `AGENTS.md` is the single authoritative contract for session behavior
and governance. Tool-specific instructions are implementation aids, not competing
contracts. If another instruction appears to conflict with this file, the rules in
`AGENTS.md` win.

---

## 1) Mission

Operate as a spec-driven assistant that:

1. Uses project wiki knowledge as the primary context source
2. Drafts and evolves specification artifacts through OpenSpec
3. Uses Graphify context when available to improve impact analysis
4. Preserves traceability, explicit uncertainty, and approval guardrails

---

## 2) Engine Model

This workflow supports one OpenSpec path through agent skills:

- **OpenSpec path**: `openspec-*` skills under `.agents/skills/` and
  `openspec/` artifacts

All feature/change work uses OpenSpec. There is no engine selection step and
no ambiguity to resolve — proceed directly to context discovery and preflight
using the OpenSpec conventions below.

Before exploring or proposing a change, use `wiki-query` to gather relevant
repository knowledge, then use `openspec-explore` or `openspec-propose` as
appropriate. Record material evidence, gaps, and assumptions in the resulting
OpenSpec artifacts.

---

## 3) Context Discovery and Authority Order

### Discovery order (where to look)

1. **Wiki index and pages**
   - `knowledge-base/index.md`
   - relevant pages under `knowledge-base/pages/`
2. **Active feature artifacts**
   - OpenSpec: `openspec/changes/<change>/` (proposal, design, specs, tasks)
3. **Specification state**
   - accepted specs (for overlap/conflict checks)
   - other active/in-flight changes (for conflicts)
4. **Graph context (optional)**
   - `graphify-out/graph.json`
   - `graphify-out/GRAPH_REPORT.md`
   - `graphify query|explain|path`

If graph data is missing, continue with wiki/spec context only and state any impact-analysis limitations explicitly.

### Authority order (what wins on conflict)

When sources disagree, resolve using this precedence, highest first:

1. **Current feature artifacts and destination-repo code/config/tests** — the
   actual state of the feature being worked on and the real repository always
   outrank derived or historical context.
2. **Accepted specs** (`openspec/specs/`)
3. **Wiki pages** (`knowledge-base/pages/`)
4. **Graph context** (optional, lowest — it is a navigational aid, not a source of truth)

Never silently pick a side of a conflict between these levels — surface it per
Section 8 (Governance and Approval Boundaries).

---

## 4) Preflight / Fail-Closed Behavior

Before doing any OpenSpec work (drafting, editing, or syncing artifacts),
run this preflight and fail closed rather than improvising:

1. **Verify required files/dirs for OpenSpec.**
   - `openspec/specs/`, `openspec/changes/`, `openspec/config.yaml` exist
   - If required paths are missing or malformed (e.g. empty `openspec/config.yaml`,
     a `changes/` directory that isn't a directory), **stop and report the exact
     gap** — name the missing/malformed path — instead of inventing structure or
     silently working around it.
2. **Check for conflicting destination-repo instructions.**
   - If the destination project already has its own `AGENTS.md`/instructions with
     rules that conflict with this contract (e.g. a different wiki location,
     different governance rules), do not silently merge or override them.
     Surface the conflict explicitly to the user and ask how to reconcile it
     before proceeding.
3. **Only proceed once preflight passes** (or the user has explicitly told you how
   to handle a reported gap/conflict).

---

## 5) Wiki Operations

### Ingest

Trigger: user asks to process sources in `knowledge-base/raw/`.

Required outcomes:
- source summary created/updated
- related concept/entity/decision/question pages updated
- if the source supersedes an earlier one (confirmed with the user, never assumed), the old source is marked `status: superseded`/`superseded_by` and the new one `status: current`/`supersedes`, with citing pages updated accordingly
- `knowledge-base/index.md` updated
- entry appended to `knowledge-base/log.md`
- source moved to `knowledge-base/raw/processed/`

### Correct

Trigger: user reports a wiki page is wrong, a claim is outdated/incorrect, or a
source document itself turns out to be inaccurate.

Required outcomes:
- distinguish a wiki mis-statement (fix the page directly) from a bad source
  (retract via frontmatter `status: retracted` + notice — never edit/delete
  the immutable file under `knowledge-base/raw/`)
- every page touched gets a dated `## Corrections` entry — no silent rewrites
- every citing page is checked and updated, not just the page the user pointed at
- conflicts with an accepted spec are flagged, never silently resolved by editing the spec
- `knowledge-base/index.md` and `knowledge-base/log.md` updated

### Remember

Trigger: user states a fact, preference, or decision directly in conversation
with no backing document to ingest.

Required outcomes:
- statement filed as a lightweight note source page (provenance: user + conversation date), preserving the "every claim traceable to a source" principle
- relevant concept/entity/decision/question pages created/updated, tagged `user-asserted`
- contradictions with existing sourced claims are surfaced and confirmed with the user, never silently overwritten
- `knowledge-base/index.md` and `knowledge-base/log.md` updated

### Query

Trigger: user asks a domain/project question.

Required outcomes:
- answer grounded in wiki pages (and graph data if available)
- explicit citations
- explicit uncertainty where information is incomplete

### Lint

Trigger: user asks for wiki health review.

Required checks:
- contradictions
- stale claims
- orphan pages
- missing index entries
- missing cross-references
- unresolved questions that block specification work

---

## 6) Specification Drafting Rules

Before drafting or modifying change artifacts:

- read relevant wiki context first
- check accepted specs for overlap
- check active/in-flight changes for conflicts
- identify assumptions and unresolved questions
- surface conflicts instead of silently resolving them

Traceability is mandatory:
- every major requirement/change rationale should reference wiki evidence (pages, decisions, source summaries)

---

## 7) Graphify Rules (Optional)

Graphify is an enhancement layer, not a hard dependency.

When available:
- use graph data to validate affected components and relationships
- use graph paths to reason about integration impact/blast radius

When unavailable:
- proceed normally using wiki/spec context
- do not fail the workflow because graph data is absent

---

## 8) Governance and Approval Boundaries

- Do not modify accepted specs without explicit human approval
- Do not claim certainty when context is ambiguous
- Record conflicts and open questions visibly
- Prefer explicit trade-offs over implicit assumptions

---

## 9) Runtime Prerequisites

This workflow is skill/prompt-driven, not just directory-driven. The following
must be present for the workflow to actually function, not merely for it to
"look" set up.

**Required:**

```text
knowledge-base/
  AGENTS.md
  index.md
  log.md
  raw/
  pages/

openspec/
  specs/
  changes/
  config.yaml

.agents/
  skills/                        # shared agent skill definitions
    openspec-explore/
    openspec-propose/
    openspec-apply-change/
    openspec-sync-specs/
    openspec-archive-change/
    openspec-update-change/
    wiki-*/
```

**Optional:**

```text
graphify-out/
  graph.json
  GRAPH_REPORT.md
```

If a required file/directory for OpenSpec is missing, this is a
preflight failure — see Section 4.

---

## 10) Behavioral Contract

In each task:

1. Run preflight (Section 4)
2. Gather context using the discovery order, resolve conflicts using the authority order (Section 3)
3. Draft output with traceability and explicit assumptions
4. Surface conflicts/questions early
5. Keep outputs consistent with project governance (Section 8)
