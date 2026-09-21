"""CodebaseController — MVC Mediator for codebase analysis.

Connects ``CodebaseModel`` (pure logic) and ``CodebaseWorker`` (thread)
with PySide6 views via Signal/Slot. NEVER imports Qt widgets (rule §10.1
of claude.md) — only QObject and Signal from QtCore.

Followed rules:
  - §10.1: Import only from PySide6.QtCore — NEVER widgets
  - §10.2: View emits signal, Controller handles — NEVER model.do_stuff()
  - §10.3: Analysis in QThread, NEVER on the main thread
"""

from PySide6.QtCore import QObject, Signal

from models.codebase_model import CodebaseModel
from workers.codebase_worker import CodebaseWorker


class CodebaseController(QObject):
    """Mediator between CodebaseModel, CodebaseWorker, and the views.

    Emitted signals:
        analysis_started()           — analysis has started
        analysis_complete(dict, str) — stats dict + Markdown report
        analysis_error(str)          — error during analysis
    """

    analysis_started = Signal()
    analysis_complete = Signal(dict, str)
    analysis_error = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._model = CodebaseModel()
        self._worker: CodebaseWorker | None = None
        self._workspace_path: str | None = None

    def set_workspace(self, path: str) -> None:
        """Sets the current workspace (used for a later manual re-analyze)."""
        self._workspace_path = path

    def analyze(self, workspace_path: str | None = None) -> None:
        """Starts codebase analysis in a background thread.

        If a scan is already in progress, it does not start a second one.
        Uses *workspace_path* if given, otherwise the last workspace set
        via ``set_workspace()``.
        """
        path = workspace_path or self._workspace_path
        if not path:
            self.analysis_error.emit("No workspace open.")
            return

        # Prevent parallel analysis runs
        if self._worker is not None and self._worker.isRunning():
            return

        self.analysis_started.emit()

        self._worker = CodebaseWorker(self._model, path)
        self._worker.analysis_complete.connect(self.analysis_complete.emit)
        self._worker.error.connect(self.analysis_error.emit)
        self._worker.finished_work.connect(self._on_worker_finished)

        self._worker.start()

    def _on_worker_finished(self) -> None:
        """Cleanup of the worker thread after completion."""
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None

    def shutdown(self) -> None:
        """Waits for an in-flight analysis before the app closes.

        Prevents Qt from aborting the process if the window closes while
        ``CodebaseWorker`` is still walking a large tree. Called from
        ``app.aboutToQuit`` in ``main.py``.
        """
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait()
