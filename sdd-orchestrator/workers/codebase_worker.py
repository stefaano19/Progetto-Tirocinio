"""Codebase Worker — Background codebase analysis.

Runs ``CodebaseModel.analyze_structure()`` in a separate QThread — walking
a large codebase and counting lines can take a noticeable amount of time,
so it must never run on the main thread (rule §10.3).

Extends ``BaseWorker`` (§10.1 / Step 1.3.1) for the standard error/finished
signal pattern instead of reimplementing ``run()``.
"""

from PySide6.QtCore import Signal

from models.codebase_model import CodebaseModel
from workers.base_worker import BaseWorker


class CodebaseWorker(BaseWorker):
    """Thread for background codebase structure/language analysis.

    Signals:
        analysis_complete(dict, str): Emitted once with the stats dict
            from ``analyze_structure()`` and the Markdown report built
            from it (``format_report()`` — no second directory walk).
    """

    analysis_complete = Signal(dict, str)

    def __init__(self, model: CodebaseModel, workspace_path: str) -> None:
        super().__init__()
        self._model = model
        self._workspace_path = workspace_path

    def do_work(self) -> None:
        stats = self._model.analyze_structure(self._workspace_path)
        report = self._model.format_report(self._workspace_path, stats)
        self.analysis_complete.emit(stats, report)
