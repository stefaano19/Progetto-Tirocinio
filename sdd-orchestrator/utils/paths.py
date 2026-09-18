"""Path constants for the SDD workspace structure.

This module defines all relative paths to the workspace root
used by the project. ZERO dependencies on PySide6 — pure Python.
"""

from pathlib import Path


# ── Mandatory directories of the SDD structure ──────────────────────────
AGENTS_SKILLS_DIR = ".agents/skills"

KB_DIR = "knowledge-base"
KB_RAW_DIR = f"{KB_DIR}/raw"
KB_RAW_PROCESSED_DIR = f"{KB_DIR}/raw/processed"
KB_PAGES_DIR = f"{KB_DIR}/pages"
KB_PAGES_ENTITIES_DIR = f"{KB_DIR}/pages/entities"
KB_PAGES_CONCEPTS_DIR = f"{KB_DIR}/pages/concepts"
KB_PAGES_SOURCES_DIR = f"{KB_DIR}/pages/sources"
KB_PAGES_DECISIONS_DIR = f"{KB_DIR}/pages/decisions"
KB_PAGES_QUESTIONS_DIR = f"{KB_DIR}/pages/questions"

OPENSPEC_DIR = "openspec"
OPENSPEC_SPECS_DIR = f"{OPENSPEC_DIR}/specs"
OPENSPEC_CHANGES_DIR = f"{OPENSPEC_DIR}/changes"

# List of all mandatory directories — used for validation and init
REQUIRED_DIRS: list[str] = [
    AGENTS_SKILLS_DIR,
    KB_RAW_DIR,
    KB_RAW_PROCESSED_DIR,
    KB_PAGES_DIR,
    KB_PAGES_ENTITIES_DIR,
    KB_PAGES_CONCEPTS_DIR,
    KB_PAGES_SOURCES_DIR,
    KB_PAGES_DECISIONS_DIR,
    KB_PAGES_QUESTIONS_DIR,
    OPENSPEC_SPECS_DIR,
    OPENSPEC_CHANGES_DIR,
]

# ── Mandatory files with template content ─────────────────────────────
REQUIRED_FILES: dict[str, str] = {
    f"{KB_DIR}/index.md": (
        "# Knowledge Base Index\n\n"
        "## Categories\n\n"
        "- [Entities](pages/entities/)\n"
        "- [Concepts](pages/concepts/)\n"
        "- [Sources](pages/sources/)\n"
        "- [Decisions](pages/decisions/)\n"
        "- [Questions](pages/questions/)\n"
    ),
    f"{KB_DIR}/log.md": "# Knowledge Base Log\n",
    f"{KB_DIR}/AGENTS.md": "# Wiki Conventions\n",
    f"{OPENSPEC_DIR}/config.yaml": "version: 1\n",
    "AGENTS.md": "# Agent Contract\n",
}

# ── Optional directories (Graphify) ──────────────────────────────────────
GRAPHIFY_DIR = "graphify-out"
GRAPHIFY_GRAPH_FILE = f"{GRAPHIFY_DIR}/graph.json"
GRAPHIFY_REPORT_FILE = f"{GRAPHIFY_DIR}/GRAPH_REPORT.md"

# ── Internal application path ───────────────────────────────────────────
SDD_INTERNAL_DIR = ".sdd"


def resolve(workspace: str, relative: str) -> Path:
    """Resolves a relative path against the workspace root."""
    return Path(workspace) / relative
