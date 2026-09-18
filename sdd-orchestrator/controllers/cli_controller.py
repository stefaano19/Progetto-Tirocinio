"""CLIController — MVC Mediator for AI CLI scanning.

Connects ``CLIDiscoveryModel`` (pure logic) and ``CLIScanWorker`` (thread)
with PySide6 views via Signal/Slot. NEVER imports Qt widgets
(rule §10.1 of claude.md) — only QObject and Signal from QtCore.

Flow (§8 of claude.md — CLI Scan Flow):

    MainWindow._on_workspace_ready(path)
      → CLIController.start_scan()
        → CLIScanWorker.start() [QThread, login shell probe]
          → CLIScanWorker.cli_found(info)
            → CLIController.cli_found(info)        [relay]
          → CLIScanWorker.scan_progress(cur, total)
            → CLIController.cli_scan_progress(cur, total)  [relay]
          → CLIScanWorker.scan_complete(results)
            → CLIController.cli_scan_complete(results)     [relay]

The Controller relays the Worker's signals — it does not add logic
to the data in transit, but makes them available to all views that
listen to them (CLIStatusView, AgentSelectorView, StatusBar).

Followed rules:
  - §10.1: Import only from PySide6.QtCore — NEVER widgets
  - §10.2: View emits signal, Controller handles — NEVER model.do_stuff()
  - §10.3: CLI scanning in QThread, NEVER on the main thread
"""

from PySide6.QtCore import QObject, Signal

from models.cli_discovery_model import CLIDiscoveryModel, CLIInfo
from workers.cli_scan_worker import CLIScanWorker


class CLIController(QObject):
    """Mediator between CLIDiscoveryModel, CLIScanWorker, and the views.

    Responsibilities:
      - Start the CLI scanning in a background thread
      - Relay the worker's signals to the views
      - Keep the list of found CLIs for subsequent queries

    Emitted signals (relay from worker):
        cli_scan_started()           — scanning has started
        cli_found(object)            — single CLIInfo found (cast to object)
        cli_scan_progress(int, int)  — progress (current, total)
        cli_scan_complete(list)      — complete CLIInfo list
        cli_scan_error(str)          — error during scanning
    """

    cli_scan_started = Signal()
    cli_found = Signal(object)
    cli_scan_progress = Signal(int, int)
    cli_scan_complete = Signal(list)
    cli_scan_error = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._model = CLIDiscoveryModel()
        self._worker: CLIScanWorker | None = None

        # Cache of the last scan's results — used by get_available_agents()
        # and by other controllers that need to know which CLIs exist
        self._last_results: list[CLIInfo] = []

    # ════════════════════════════════════════════════════════════════════
    # PUBLIC ACTIONS
    # ════════════════════════════════════════════════════════════════════

    def start_scan(self) -> None:
        """Start the CLI scanning in a background thread.

        If a scan is already in progress, it does not start a second one.
        Creates a new ``CLIScanWorker``, connects signals as relay,
        and starts it.

        This is the only action the UI needs to call. Everything else
        happens via signals:
          - ``cli_found`` → the CLIStatusView updates the single card
          - ``cli_scan_progress`` → the progress bar advances
          - ``cli_scan_complete`` → status bar and agent selector are updated
        """
        # Prevent parallel scans
        if self._worker is not None and self._worker.isRunning():
            return

        # Emits start signal (UI can show spinner/progress)
        self.cli_scan_started.emit()

        # Create the worker and connect the signals as relay
        self._worker = CLIScanWorker(self._model)

        # Relay: worker.signal → controller.signal → view.slot
        # Each worker signal is "relayed" by the controller
        # so the views connect ONLY to the controller (never to the worker)
        self._worker.cli_found.connect(self.cli_found.emit)
        self._worker.scan_progress.connect(self.cli_scan_progress.emit)
        self._worker.scan_complete.connect(self._on_scan_complete)
        self._worker.error.connect(self.cli_scan_error.emit)

        # Cleanup: when the thread finishes, it is marked for garbage collection
        self._worker.finished_work.connect(self._on_worker_finished)

        # Start the thread
        self._worker.start()

    def get_available_agents(self) -> list[CLIInfo]:
        """Returns the CLIs with ``found=True`` from the last scan.

        Useful for the agents dropdown and for other controllers that
        need to know which CLIs are available.

        Returns:
            List of ``CLIInfo`` with ``found=True``, or empty list
            if no scan has been completed yet.
        """
        return [info for info in self._last_results if info.found]

    @property
    def last_results(self) -> list[CLIInfo]:
        """All results from the last scan (found + not found)."""
        return self._last_results

    # ════════════════════════════════════════════════════════════════════
    # PRIVATE SLOTS
    # ════════════════════════════════════════════════════════════════════

    def _on_scan_complete(self, results: list) -> None:
        """Handles the completion of the scanning.

        Saves the results in the internal cache and relays the signal
        ``cli_scan_complete`` to the views.
        """
        self._last_results = results
        self.cli_scan_complete.emit(results)

    def _on_worker_finished(self) -> None:
        """Cleanup of the worker thread after completion.

        Calls ``deleteLater()`` to schedule garbage collection
        of the QThread — important to avoid memory leaks.
        """
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
