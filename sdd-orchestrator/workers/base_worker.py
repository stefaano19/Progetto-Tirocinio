"""BaseWorker — Reusable base QThread for I/O-bound tasks.

Provides a standard pattern for application worker threads:
  - ``error`` Signal for caught errors
  - ``finished_work`` Signal to indicate completion
  - ``run()`` wrapper with automatic try/except
  - Abstract ``do_work()`` method to be implemented in subclasses

Followed rules:
  - §10.3: I/O ALWAYS in QThread, NEVER on the main thread
  - §10.1: Import only from PySide6.QtCore (QThread, Signal) — NEVER widgets
"""

from PySide6.QtCore import QThread, Signal


class BaseWorker(QThread):
    """Reusable base thread for I/O-bound operations.

    Subclasses implement ``do_work()`` with specific logic.
    The ``run()`` method wraps ``do_work()`` in a try/except that
    emits the ``error`` signal if something goes wrong.

    Signals:
        error(str): Emitted when ``do_work()`` raises an exception.
                    Contains the error message.
        finished_work(): ALWAYS emitted at the end of ``run()``,
                         whether successful or on error.
                         Useful for UI cleanup (hiding spinners, etc.).

    Example:
        >>> class MyWorker(BaseWorker):
        ...     result = Signal(object)
        ...     def do_work(self):
        ...         data = expensive_computation()
        ...         self.result.emit(data)
        ...
        >>> worker = MyWorker()
        >>> worker.error.connect(lambda msg: print(f"Error: {msg}"))
        >>> worker.finished_work.connect(lambda: print("Done!"))
        >>> worker.start()
    """

    error = Signal(str)
    finished_work = Signal()

    def run(self) -> None:
        """Thread entry point. DO NOT override — use ``do_work()``."""
        try:
            self.do_work()
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished_work.emit()

    def do_work(self) -> None:
        """Specific worker logic. To be overridden in subclasses.

        This method is executed in a separate thread. It is safe here
        to perform long I/O operations (filesystem, subprocess, network).

        To communicate results to the UI, emit signals defined
        in the subclass — they will be received in the main thread.
        """
        raise NotImplementedError("Subclasses must implement do_work()")
