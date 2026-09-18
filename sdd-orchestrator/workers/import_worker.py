"""Import Worker.

Background QThread to import documents into the knowledge-base safely.
Emits progress signals for the Activity Panel.
"""

from PySide6.QtCore import Signal

from models.wiki_model import WikiModel
from workers.base_worker import BaseWorker


class ImportWorker(BaseWorker):
    """Thread for copying files into the knowledge base raw/ directory."""

    # Emits (current, total, filename) for the UI progress bar
    import_progress = Signal(int, int, str)
    
    # Emitted when all files are successfully imported
    import_complete = Signal(list)

    def __init__(self, model: WikiModel, workspace_path: str, source_paths: list[str]) -> None:
        super().__init__()
        self._model = model
        self._workspace_path = workspace_path
        self._source_paths = source_paths

    def do_work(self) -> None:
        """Executes the file copying process in the background.
        
        Iterates through the provided source paths and calls the Model
        to import each document. Progress is reported step-by-step.
        """
        total = len(self._source_paths)
        imported_files = []
        
        for i, source_path in enumerate(self._source_paths):
            # Extract just the filename for cleaner UI reporting
            import os
            filename = os.path.basename(source_path)
            
            # Update progress UI
            self.import_progress.emit(i + 1, total, filename)
            
            # The model handles the secure atomic copy operation
            dest_path = self._model.import_document(self._workspace_path, source_path)
            imported_files.append(dest_path)
            
        self.import_complete.emit(imported_files)
