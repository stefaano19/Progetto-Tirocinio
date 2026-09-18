from PySide6.QtCore import QObject, Signal

from models.wiki_model import WikiModel
from utils.markdown_parser import ParsedIndex

class WikiController(QObject):
    """Controller for Knowledge Base (Wiki) exploration.
    
    Handles the logic of reading the index, loading pages
    and notifies the View via signals.
    """
    
    # Signals
    index_loaded = Signal(object)      # Emits ParsedIndex or None
    page_selected = Signal(str)        # relative path (emitted by the view)
    page_loaded = Signal(str, str)     # title/path, markdown content
    error_occurred = Signal(str)       # error message

    # Import signals (Step 2.3.5) — the controller never touches widgets
    # directly (§10.1); the view/wiring layer connects these to ActivityPanel.
    import_started = Signal(str, str)          # task_id, title
    import_progress = Signal(str, int, int, str)  # task_id, current, total, detail
    import_complete = Signal(str, int)         # task_id, imported_count

    def __init__(self, wiki_model: WikiModel, parent=None):
        super().__init__(parent)
        self._model = wiki_model
        self._workspace_path: str = ""
        self._workers: list = []

        # Connect the signal (incoming from the view) to the method to load it
        self.page_selected.connect(self._load_page)

    def set_workspace(self, path: str) -> None:
        """Sets the current workspace and triggers the index loading."""
        self._workspace_path = path
        self.load_index()

    def load_index(self) -> None:
        """Reads index.md via WikiModel and emits the event to update the UI."""
        if not self._workspace_path:
            return
            
        parsed_index = self._model.parse_index(self._workspace_path)
        self.index_loaded.emit(parsed_index)

    def _load_page(self, page_rel_path: str) -> None:
        """Reads the content of a single markdown page."""
        if not self._workspace_path:
            return
            
        try:
            content = self._model.read_page(self._workspace_path, page_rel_path)
            self.page_loaded.emit(page_rel_path, content)
        except Exception as e:
            self.error_occurred.emit(f"Unable to load the page:\n{e}")

    def start_import(self, source_paths: list[str]) -> None:
        """Starts the background worker to import documents.

        Emits ``import_started``/``import_progress``/``import_complete``
        instead of touching the Activity Panel widget directly — the
        wiring layer connects these signals to the view (§10.1/§10.2).
        """
        if not self._workspace_path:
            self.error_occurred.emit("Please open a workspace before importing documents.")
            return

        from workers.import_worker import ImportWorker
        import uuid

        task_id = f"import_{uuid.uuid4().hex[:8]}"
        worker = ImportWorker(self._model, self._workspace_path, source_paths)

        # Keep reference to prevent GC
        self._workers.append(worker)

        title = f"Importing {len(source_paths)} documents..."
        self.import_started.emit(task_id, title)

        worker.import_progress.connect(
            lambda current, total, filename: self.import_progress.emit(
                task_id, current, total, f"Copying {filename}"
            )
        )

        def on_complete(files):
            self._workers.remove(worker)
            self.load_index()  # Refresh the wiki browser
            self.import_complete.emit(task_id, len(files))

        def on_error(msg):
            self._workers.remove(worker)
            self.import_progress.emit(task_id, 0, 0, f"Error: {msg}")
            self.error_occurred.emit(msg)

        worker.import_complete.connect(on_complete)
        worker.error.connect(on_error)

        # Start background task
        worker.start()
