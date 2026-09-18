"""WorkspaceController — MVC Mediator for the workspace.

Connects WorkspaceModel (pure logic) with PySide6 views via
Signal/Slot. NEVER imports Qt widgets (rule §10.1 of claude.md) —
only QObject and Signal from QtCore.

Flow (§8 of claude.md — Workspace Flow):

    WorkspaceView.open_requested(path)
      → WorkspaceController.open_workspace(path)
        → WorkspaceModel.validate_workspace(path)
          → workspace_validated(result)
            → (if invalid) Dialog init
              → WorkspaceController.initialize_workspace(path)
                → workspace_initialized(path)
                  → MainWindow._on_workspace_ready(path)
"""

from PySide6.QtCore import QObject, Signal, QSettings

from models.workspace_model import WorkspaceModel


# Key used in QSettings for the recent projects list
_RECENT_KEY = "workspace/recent_paths"
_MAX_RECENT = 5


class WorkspaceController(QObject):
    """Mediator between WorkspaceModel and the views.

    Emitted signals:
        workspace_opened(str)        — path of the successfully opened workspace
        workspace_validated(dict)    — validation result {valid, missing_*, stats}
        workspace_initialized(str)   — path of the just initialized workspace
        workspace_error(str)         — error message
        workspace_stats_ready(dict)  — info/stats of the workspace (for UI card)
    """

    workspace_opened = Signal(str)
    workspace_validated = Signal(dict)
    workspace_initialized = Signal(str)
    workspace_error = Signal(str)
    workspace_stats_ready = Signal(dict)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._model = WorkspaceModel()
        self._current_path: str | None = None
        self._settings = QSettings()

    # ════════════════════════════════════════════════════════════════════
    # PUBLIC ACTIONS (called by the views)
    # ════════════════════════════════════════════════════════════════════

    def open_workspace(self, path: str) -> None:
        """Opens a workspace: validates, and if valid emits workspace_opened.

        If validation fails emits workspace_validated with the
        details of the missing files/directories — the view will be able to propose
        the initialization to the user.
        """
        result = self._model.validate_workspace(path)
        self.workspace_validated.emit(result)

        if result["valid"]:
            self._current_path = path
            self._add_to_recent(path)
            self.workspace_opened.emit(path)

            # Also emits stats for the status bar / card
            info = self._model.get_workspace_info(path)
            self.workspace_stats_ready.emit(info)

    def initialize_workspace(self, path: str) -> None:
        """Initializes the SDD structure and then opens the workspace."""
        success = self._model.initialize_workspace(path)

        if success:
            self._current_path = path
            self._add_to_recent(path)
            self.workspace_initialized.emit(path)

            # After init the workspace is valid, so we open it
            info = self._model.get_workspace_info(path)
            self.workspace_stats_ready.emit(info)
            self.workspace_opened.emit(path)
        else:
            self.workspace_error.emit(
                f"Unable to initialize the workspace in:\n{path}"
            )

    def validate_workspace(self, path: str) -> None:
        """Standalone validation (without opening). Useful for preview."""
        result = self._model.validate_workspace(path)
        self.workspace_validated.emit(result)

    # ════════════════════════════════════════════════════════════════════
    # RECENT PROJECTS (persisted via QSettings)
    # ════════════════════════════════════════════════════════════════════

    def get_recent_workspaces(self) -> list[dict]:
        """Returns the list of recent workspaces with related info.

        Each element is a dict with name, path, stats.
        Paths that no longer exist on disk are filtered out.
        """
        paths = self._settings.value(_RECENT_KEY, [], type=list)
        model = self._model
        result: list[dict] = []

        for p in paths:
            from pathlib import Path as _Path
            if _Path(p).is_dir():
                info = model.get_workspace_info(p)
                result.append(info)

        return result

    def _add_to_recent(self, path: str) -> None:
        """Adds *path* to the head of the recent list (max 5)."""
        from pathlib import Path as _Path
        abs_path = str(_Path(path).resolve())

        paths: list[str] = self._settings.value(_RECENT_KEY, [], type=list)

        # Remove if already present (will be reinserted at the head)
        if abs_path in paths:
            paths.remove(abs_path)

        paths.insert(0, abs_path)
        paths = paths[:_MAX_RECENT]

        self._settings.setValue(_RECENT_KEY, paths)

    # ════════════════════════════════════════════════════════════════════
    # PROPERTIES
    # ════════════════════════════════════════════════════════════════════

    @property
    def current_path(self) -> str | None:
        """Path of the currently open workspace (None if none)."""
        return self._current_path
