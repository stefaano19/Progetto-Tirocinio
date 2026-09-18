"""CLI Scan Worker — Background AI CLI scan.

Scans all CLIs in the registry in a separate QThread,
emitting progress signals for each CLI found. This is fundamental
because the login shell probe can take up to 10 seconds and the
version check of each CLI up to 3 seconds — running them on the main thread
would block the UI (rule §10.3).

Flow (§8 of claude.md — CLI Scan Flow):

    MainWindow._on_workspace_ready(path)
      → CLIController.start_scan()
        → CLIScanWorker.start() [QThread]
          → cli_found(info)        [for each CLI found]
          → scan_progress(int,int) [numeric progress]
          → scan_complete(list)    [complete final list]

Followed rules:
  - §10.3: I/O in QThread — the login shell probe can take 10s!
  - §10.1: Import only from PySide6.QtCore — NEVER widgets
"""

from PySide6.QtCore import Signal

from models.cli_discovery_model import CLIDiscoveryModel, CLIInfo
from workers.base_worker import BaseWorker


class CLIScanWorker(BaseWorker):
    """Thread for background AI CLI scanning.

    Iterates through all CLIs in the model's ``CLI_REGISTRY``, executes the binary
    search (with login shell PATH probe) and the version check for each,
    emitting progressive signals.

    Signals:
        cli_found(object): Emitted for each single scanned CLI.
                           The payload is a ``CLIInfo`` (cast to ``object``
                           because PySide6 Signal doesn't support custom types
                           as direct type). The View receives and updates
                           the corresponding card in real time.

        scan_progress(int, int): Emitted after each scanned CLI.
                                 (current_index, total) — e.g. (3, 8)
                                 for "scanned 3 out of 8 CLIs".
                                 The View uses this for the progress bar.

        scan_complete(list): Emitted once when all CLIs
                             have been scanned. The payload is the complete
                             list of ``CLIInfo``. The Controller uses
                             this to update the status bar and agent selector.

    Usage:
        >>> model = CLIDiscoveryModel()
        >>> worker = CLIScanWorker(model)
        >>> worker.cli_found.connect(on_single_cli)
        >>> worker.scan_complete.connect(on_all_done)
        >>> worker.start()  # starts the thread
    """

    # Signal for progressive update (one CLI at a time)
    cli_found = Signal(object)

    # Signal for numeric progress (for progress bar)
    scan_progress = Signal(int, int)

    # Signal for complete final result
    scan_complete = Signal(list)

    def __init__(self, model: CLIDiscoveryModel) -> None:
        super().__init__()
        self._model = model

    def do_work(self) -> None:
        """Scans all CLIs in the registry sequentially.

        For each CLI in the registry:
          1. Calls ``model.scan_single(key)`` — searches for binary + version
          2. Emits ``cli_found(info)`` — the UI updates the card in real time
          3. Emits ``scan_progress(i+1, total)`` — the UI updates the progress bar

        Upon completion, emits ``scan_complete(results)`` with the full list.

        Note:
            The login shell PATH probe (which can take 10s) is executed
            only on the first call to ``find_cli_command()`` thanks to the
            ``@lru_cache`` in the resolver. Subsequent CLIs are fast.
        """
        registry = self._model.registry
        total = len(registry)
        results: list[CLIInfo] = []

        for i, cli_def in enumerate(registry):
            # Scans the single CLI (includes PATH probe + version check)
            info = self._model.scan_single(cli_def["key"])

            # Emits the single result → the View updates immediately
            self.cli_found.emit(info)

            # Emits numeric progress → the View updates the progress bar
            self.scan_progress.emit(i + 1, total)

            results.append(info)

        # Emits the full list → Controller updates status bar and agent selector
        self.scan_complete.emit(results)
