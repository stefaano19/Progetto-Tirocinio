"""WorkspaceModel — SDD workspace logic.

Responsibilities:
- Validate whether a folder is a valid SDD workspace
- Initialize the SDD structure (directories + template files)
- Obtain workspace statistics (pages count, specs, changes)
- Verify presence of optional Graphify data

ZERO dependencies on PySide6 — pure Python (rule §10.1 of claude.md).
Uses constants defined in utils/paths.py.
"""

from pathlib import Path

from utils.paths import (
    GRAPHIFY_GRAPH_FILE,
    KB_PAGES_DIR,
    OPENSPEC_CHANGES_DIR,
    OPENSPEC_SPECS_DIR,
    REQUIRED_DIRS,
    REQUIRED_FILES,
    resolve,
)


class WorkspaceModel:
    """Pure logic for SDD workspace management.

    No persistent internal state — all operations receive
    the workspace path as a parameter, so the Model remains
    stateless and easily testable.
    """

    def validate_workspace(self, path: str) -> dict:
        """Checks if *path* contains a valid SDD structure.

        Verifies that all directories in ``REQUIRED_DIRS`` and all
        files in ``REQUIRED_FILES`` exist. It also collects content
        statistics (number of wiki pages, accepted specs, active changes).

        Returns:
            A dictionary with these keys:

            - ``valid`` (bool): True if everything necessary is present.
            - ``missing_dirs`` (list[str]): missing directories.
            - ``missing_files`` (list[str]): missing files.
            - ``stats`` (dict): contains ``wiki_pages``, ``specs``,
              ``changes`` — useful counts for the Welcome Screen.
        """
        root = Path(path)

        missing_dirs: list[str] = []
        for d in REQUIRED_DIRS:
            if not (root / d).is_dir():
                missing_dirs.append(d)

        missing_files: list[str] = []
        for f in REQUIRED_FILES:
            if not (root / f).is_file():
                missing_files.append(f)

        stats = self._count_stats(root)

        return {
            "valid": len(missing_dirs) == 0 and len(missing_files) == 0,
            "missing_dirs": missing_dirs,
            "missing_files": missing_files,
            "stats": stats,
        }

    def initialize_workspace(self, path: str) -> bool:
        """Creates the complete SDD structure in the folder *path*.

        - Creates all required directories (``REQUIRED_DIRS``).
        - Creates all template files (``REQUIRED_FILES``) **only if they
          do not already exist** — never overwrites user content.

        Returns:
            True if initialization succeeds, False in case of an error.
        """
        root = Path(path)

        try:
            # Create directories (parents=True creates recursively,
            # exist_ok=True prevents errors if they already exist)
            for d in REQUIRED_DIRS:
                (root / d).mkdir(parents=True, exist_ok=True)

            # Create template files only if they don't exist
            for filepath, template in REQUIRED_FILES.items():
                full = root / filepath
                if not full.exists():
                    full.parent.mkdir(parents=True, exist_ok=True)
                    full.write_text(template, encoding="utf-8")

            return True

        except OSError:
            return False

    def get_workspace_info(self, path: str) -> dict:
        """Returns useful metadata for the workspace summary card.

        Returns:
            Dictionary with:
            - ``name`` (str): name of the workspace folder.
            - ``path`` (str): absolute path.
            - ``stats`` (dict): {wiki_pages, specs, changes}.
            - ``has_graphify`` (bool): True if graphify-out/graph.json exists.
        """
        root = Path(path)
        return {
            "name": root.name,
            "path": str(root.resolve()),
            "stats": self._count_stats(root),
            "has_graphify": self.has_graphify_data(path),
        }

    def has_graphify_data(self, path: str) -> bool:
        """Checks if ``graphify-out/graph.json`` exists in the workspace."""
        return resolve(path, GRAPHIFY_GRAPH_FILE).is_file()

    # ── Private methods ───────────────────────────────────────────────

    def _count_stats(self, root: Path) -> dict:
        """Counts wiki pages, specs and changes in the workspace.

        Uses glob to count ``.md`` files in their respective folders.
        If a folder does not exist, the count is 0.
        """
        return {
            "wiki_pages": self._count_md_files(root / KB_PAGES_DIR),
            "specs": self._count_md_files(root / OPENSPEC_SPECS_DIR),
            "changes": self._count_subdirs(root / OPENSPEC_CHANGES_DIR),
        }

    @staticmethod
    def _count_md_files(directory: Path) -> int:
        """Recursively counts .md files in *directory*."""
        if not directory.is_dir():
            return 0
        return sum(1 for _ in directory.rglob("*.md"))

    @staticmethod
    def _count_subdirs(directory: Path) -> int:
        """Counts direct subdirectories (= active changes)."""
        if not directory.is_dir():
            return 0
        return sum(1 for d in directory.iterdir() if d.is_dir())
