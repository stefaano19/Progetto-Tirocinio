"""Wiki Import View.

Dialog to manage file imports via drag-and-drop.
Lists dropped files with status indicators.
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QProgressBar,
    QFileDialog,
)

from views.widgets.file_drop_area import FileDropArea
from models.wiki_model import SUPPORTED_EXTENSIONS


class WikiImportView(QDialog):
    """Dialog window to import documents into the Wiki."""
    
    # Emitted when the user clicks "Import All" with a list of absolute paths
    import_requested = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Documents to Knowledge Base")
        self.setMinimumSize(500, 400)
        
        self.pending_files: list[str] = []
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        title = QLabel("Add Sources")
        title.setObjectName("h2")
        layout.addWidget(title)

        subtitle = QLabel(f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")
        subtitle.setObjectName("section_subtitle")
        layout.addWidget(subtitle)

        # Drop Area (visual feedback via QSS [drag_active] property, see styles/*.qss)
        self.drop_area = FileDropArea()
        self.drop_area.setMinimumHeight(100)
        layout.addWidget(self.drop_area)
        
        # File List
        self.file_list = QListWidget()
        self.file_list.setObjectName("import_file_list")
        layout.addWidget(self.file_list, stretch=1)
        
        # Progress Bar (hidden by default, can be controlled externally)
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Bottom Buttons
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_import = QPushButton("Import All")
        self.btn_import.setObjectName("primary_action")
        self.btn_import.setEnabled(False) # Disabled until files are added
        
        # We can add a browse button directly to the drop area logic, or just a button here
        self.btn_browse = QPushButton("Browse Files...")
        
        btn_layout.addWidget(self.btn_browse)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_import)
        
        layout.addLayout(btn_layout)

    def _connect_signals(self) -> None:
        self.drop_area.files_dropped.connect(self._add_files)
        self.drop_area.mousePressEvent = self._on_drop_area_clicked # override click to browse
        
        self.btn_browse.clicked.connect(self._browse_files)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_import.clicked.connect(self._on_import_clicked)

    def _on_drop_area_clicked(self, event) -> None:
        """Allows clicking the drop area to open file browser."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._browse_files()

    def _browse_files(self) -> None:
        """Opens standard file dialog to pick files."""
        # Build filter from SUPPORTED_EXTENSIONS
        ext_filter = " ".join([f"*{ext}" for ext in SUPPORTED_EXTENSIONS])
        filters = f"Supported Files ({ext_filter});;All Files (*.*)"
        
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Documents", "", filters)
        if paths:
            self._add_files(paths)

    def _add_files(self, paths: list[str]) -> None:
        """Validates and adds files to the list widget."""
        added = False
        for path in paths:
            p = Path(path)
            # Check extension and duplicates
            if p.suffix.lower() in SUPPORTED_EXTENSIONS and str(p) not in self.pending_files:
                self.pending_files.append(str(p))
                
                # Add visually to list
                item = QListWidgetItem(f"📄 {p.name}")
                item.setToolTip(str(p))
                # Store the path in the item
                item.setData(Qt.ItemDataRole.UserRole, str(p))
                self.file_list.addItem(item)
                added = True
                
        if added:
            self.btn_import.setEnabled(True)

    def _on_import_clicked(self) -> None:
        """Emits the import signal and updates UI state to importing."""
        if not self.pending_files:
            return
            
        self.btn_import.setEnabled(False)
        self.btn_browse.setEnabled(False)
        self.drop_area.setEnabled(False)
        self.import_requested.emit(self.pending_files)
        
        # Typically the parent controller will close this dialog once it finishes or moves
        # the task to the background Activity Panel. 
        self.accept()
