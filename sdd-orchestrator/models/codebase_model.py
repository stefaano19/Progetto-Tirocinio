"""Codebase Model — Local codebase structure and language analysis.

Walks a workspace directory tree, counts files/lines per language, and
generates a Markdown summary report (§5.8 of claude.md — RF7).

ZERO PySide6 dependencies — pure Python (rule §10.1). This can be slow on
large trees (line counting), so callers MUST run it in a QThread
(``workers/codebase_worker.py``), NEVER on the main thread (rule §10.3).
"""

from __future__ import annotations

import os
from pathlib import Path


# ── Directories excluded from analysis (dependency/build/VCS noise) ────
EXCLUDED_DIRS: set[str] = {
    ".git", ".hg", ".svn",
    ".venv", "venv", "env",
    "node_modules",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".idea", ".vscode",
    "dist", "build", "target",
    ".next", ".nuxt",
}

# ── File extension → language display name ─────────────────────────────
EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript (JSX)",
    ".mjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (TSX)",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".c": "C",
    ".h": "C Header",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".m": "Objective-C",
    ".scala": "Scala",
    ".sh": "Shell",
    ".bash": "Shell",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".md": "Markdown",
    ".sql": "SQL",
    ".xml": "XML",
    ".toml": "TOML",
    ".lua": "Lua",
    ".dart": "Dart",
    ".r": "R",
    ".pl": "Perl",
    ".vue": "Vue",
}


class CodebaseModel:
    """Local codebase structure and language analysis.

    Main methods:
      - ``analyze_structure()``: full stats (files, dirs, lines, languages, largest files)
      - ``detect_languages()``: file count per recognized language
      - ``generate_report()``: Markdown report built from ``analyze_structure()``
    """

    def _iter_files(self, root: Path):
        """Yields every file Path under *root*, skipping ``EXCLUDED_DIRS`` and dotfolders."""
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                d for d in dirnames
                if d not in EXCLUDED_DIRS and not d.startswith(".")
            ]
            for filename in filenames:
                yield Path(dirpath) / filename

    @staticmethod
    def _count_lines(file_path: Path) -> int:
        """Counts lines in a text file, ignoring decode errors. 0 if unreadable."""
        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except OSError:
            return 0

    @staticmethod
    def _format_size(num_bytes: int) -> str:
        """Human-readable file size (B / KB / MB / GB)."""
        size = float(num_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} GB"

    def analyze_structure(self, workspace: str) -> dict:
        """Analyzes file/folder structure, languages, and stats.

        Returns:
            dict with ``total_files``, ``total_dirs``, ``total_lines``
            (recognized source files only), ``languages`` (dict, sorted
            descending by file count), and ``largest_files``
            (list of ``(relative_path, size_bytes)``, top 10).
        """
        root = Path(workspace)
        if not root.is_dir():
            return {
                "total_files": 0,
                "total_dirs": 0,
                "total_lines": 0,
                "languages": {},
                "largest_files": [],
            }

        total_files = 0
        total_dirs = 0
        total_lines = 0
        languages: dict[str, int] = {}
        file_sizes: list[tuple[str, int]] = []

        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                d for d in dirnames
                if d not in EXCLUDED_DIRS and not d.startswith(".")
            ]
            total_dirs += len(dirnames)

            for filename in filenames:
                file_path = Path(dirpath) / filename
                total_files += 1

                language = EXTENSION_LANGUAGE_MAP.get(file_path.suffix.lower())
                if language:
                    languages[language] = languages.get(language, 0) + 1
                    total_lines += self._count_lines(file_path)

                try:
                    size = file_path.stat().st_size
                    file_sizes.append((str(file_path.relative_to(root)), size))
                except OSError:
                    continue

        file_sizes.sort(key=lambda item: item[1], reverse=True)
        sorted_languages = dict(sorted(languages.items(), key=lambda kv: kv[1], reverse=True))

        return {
            "total_files": total_files,
            "total_dirs": total_dirs,
            "total_lines": total_lines,
            "languages": sorted_languages,
            "largest_files": file_sizes[:10],
        }

    def detect_languages(self, workspace: str) -> dict[str, int]:
        """Counts files per recognized language (sorted descending)."""
        root = Path(workspace)
        if not root.is_dir():
            return {}

        languages: dict[str, int] = {}
        for file_path in self._iter_files(root):
            language = EXTENSION_LANGUAGE_MAP.get(file_path.suffix.lower())
            if language:
                languages[language] = languages.get(language, 0) + 1

        return dict(sorted(languages.items(), key=lambda kv: kv[1], reverse=True))

    def generate_report(self, workspace: str) -> str:
        """Generates a Markdown analysis report for *workspace*.

        Convenience wrapper: runs ``analyze_structure()`` then formats it.
        Callers that already have a ``stats`` dict (e.g. a worker that just
        ran ``analyze_structure()``) should call ``format_report()``
        directly instead, to avoid walking the tree twice.
        """
        stats = self.analyze_structure(workspace)
        return self.format_report(workspace, stats)

    def format_report(self, workspace: str, stats: dict) -> str:
        """Formats an already-computed ``analyze_structure()`` result as Markdown."""
        lines = [
            "# Codebase Analysis Report",
            "",
            f"**Workspace:** `{workspace}`",
            "",
            "## Summary",
            "",
            f"- Files: {stats['total_files']}",
            f"- Directories: {stats['total_dirs']}",
            f"- Lines of code (recognized languages): {stats['total_lines']}",
            "",
            "## Languages",
            "",
        ]

        if stats["languages"]:
            lines.append("| Language | Files |")
            lines.append("|----------|-------|")
            for lang, count in stats["languages"].items():
                lines.append(f"| {lang} | {count} |")
        else:
            lines.append("No recognized source files found.")

        lines.append("")
        lines.append("## Largest Files")
        lines.append("")

        if stats["largest_files"]:
            lines.append("| File | Size |")
            lines.append("|------|------|")
            for rel_path, size in stats["largest_files"]:
                lines.append(f"| `{rel_path}` | {self._format_size(size)} |")
        else:
            lines.append("No files found.")

        return "\n".join(lines)
