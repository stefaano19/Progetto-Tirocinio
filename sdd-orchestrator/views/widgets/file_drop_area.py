"""File Drop Area Widget.

Provides a drag-and-drop zone for importing files into the knowledge base.
Emits a signal with the list of dropped file paths.
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDragLeaveEvent
from PySide6.QtWidgets import QLabel


class FileDropArea(QLabel):
    """A custom widget that accepts file drag-and-drop operations.
    
    Provides visual feedback when files are dragged over it (via QSS property)
    and filters for local files.
    """
    
    # Signal emitted when valid files are dropped. Contains list of absolute paths.
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("file_drop_area")
        self.setText("Drag and drop files here\nor click to browse")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        
        # We use a custom property to drive the QSS styling for visual feedback
        self.setProperty("drag_active", False)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Called when a drag enters the widget's boundaries."""
        if event.mimeData().hasUrls():
            # Check if there is at least one local file
            urls = event.mimeData().urls()
            if any(url.isLocalFile() for url in urls):
                event.acceptProposedAction()
                self._set_drag_active(True)
                return
        event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        """Called when a drag leaves the widget's boundaries."""
        self._set_drag_active(False)
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        """Called when the user drops the files."""
        self._set_drag_active(False)
        
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    # We convert to string path immediately
                    path = Path(url.toLocalFile())
                    if path.is_file():
                        file_paths.append(str(path))
            
            if file_paths:
                event.acceptProposedAction()
                self.files_dropped.emit(file_paths)
                return
                
        event.ignore()
        
    def _set_drag_active(self, active: bool) -> None:
        """Updates the property and forces a style re-evaluation."""
        if self.property("drag_active") != active:
            self.setProperty("drag_active", active)
            # Necessary to force the QSS to re-evaluate the custom property
            self.style().unpolish(self)
            self.style().polish(self)
