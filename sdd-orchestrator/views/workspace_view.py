"""WorkspaceView — Welcome Screen and workspace info panel.

Two states (inspired by LLM Wiki ``welcome-screen.tsx``):

1. **Welcome Screen** (no workspace open):
   - Logo + title "SDD Orchestrator"
   - "Open Workspace" button → QFileDialog
   - Recent projects list (path + stats)

2. **Workspace Info Panel** (after opening):
   - Summary card: name, path, statistics (wiki pages, specs, changes)
   - Quick actions: [Import Docs] [New Change] [Analyze Codebase]

The view emits signals — the controller handles the logic (rule §10.2).
NEVER put business logic in here.
"""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class WorkspaceView(QWidget):
    """Welcome screen + workspace info panel.

    Signals emitted:
        open_requested(str)   — the user selected a folder to open
        init_requested(str)   — the user confirmed SDD initialization
        import_docs_requested()      — quick action: "Import Docs" clicked
        new_change_requested()       — quick action: "New Change" clicked
        analyze_codebase_requested() — quick action: "Analyze Codebase" clicked
    """

    open_requested = Signal(str)
    init_requested = Signal(str)
    import_docs_requested = Signal()
    new_change_requested = Signal()
    analyze_codebase_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("workspace_view")

        # Path awaiting init confirmation (used in validation dialog)
        self._pending_path: str | None = None

        self._setup_ui()

    # ════════════════════════════════════════════════════════════════════
    # UI SETUP
    # ════════════════════════════════════════════════════════════════════

    def _setup_ui(self) -> None:
        """Builds the two-layer stacked interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area wrapping all content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(scroll)

        # Centered inner container
        container = QWidget()
        container.setObjectName("workspace_container")
        self._container_layout = QVBoxLayout(container)
        self._container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._container_layout.setSpacing(24)
        self._container_layout.setContentsMargins(40, 60, 40, 40)

        scroll.setWidget(container)

        # ── Welcome Section ─────────────────────────────────────────
        self._welcome_section = QWidget()
        welcome_layout = QVBoxLayout(self._welcome_section)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.setSpacing(16)

        # Logo
        logo = QLabel("S")
        logo.setObjectName("welcome_logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        welcome_layout.addWidget(logo)

        # Title
        title = QLabel("SDD Orchestrator")
        title.setObjectName("welcome_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        welcome_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Spec-Driven Development Workspace Manager")
        subtitle.setObjectName("welcome_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(subtitle)

        welcome_layout.addSpacing(8)

        # Open Workspace Button
        self._open_btn = QPushButton("📂  Open Workspace")
        self._open_btn.setObjectName("primary_button")
        self._open_btn.setFixedHeight(44)
        self._open_btn.setMinimumWidth(240)
        self._open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_btn.clicked.connect(self._on_open_clicked)
        welcome_layout.addWidget(
            self._open_btn, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self._container_layout.addWidget(self._welcome_section)

        # ── Recent Section ─────────────────────────────────────────
        self._recent_section = QWidget()
        self._recent_section.setMinimumWidth(600)
        self._recent_section.setMaximumWidth(760)
        recent_layout = QVBoxLayout(self._recent_section)
        recent_layout.setSpacing(8)

        recent_title = QLabel("RECENT WORKSPACES")
        recent_title.setObjectName("recent_title")
        recent_layout.addWidget(recent_title)

        self._recent_list_layout = QVBoxLayout()
        self._recent_list_layout.setSpacing(4)
        recent_layout.addLayout(self._recent_list_layout)

        # Placeholder "No recent workspaces"
        self._no_recent_label = QLabel("No recent workspaces")
        self._no_recent_label.setObjectName("section_subtitle")
        self._no_recent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._recent_list_layout.addWidget(self._no_recent_label)

        self._container_layout.addWidget(
            self._recent_section, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # ── Info Panel (initially hidden) ──────────────────────
        self._info_section = QWidget()
        self._info_section.setMaximumWidth(600)
        self._info_section.hide()
        info_layout = QVBoxLayout(self._info_section)
        info_layout.setSpacing(16)

        # Summary card
        self._info_card = QFrame()
        self._info_card.setObjectName("info_card")
        
        card_layout = QVBoxLayout(self._info_card)
        card_layout.setSpacing(12)

        self._ws_name_label = QLabel("Workspace Name")
        self._ws_name_label.setObjectName("ws_name_label")
        card_layout.addWidget(self._ws_name_label)

        self._ws_path_label = QLabel("/path/to/workspace")
        self._ws_path_label.setObjectName("section_subtitle")
        self._ws_path_label.setWordWrap(True)
        card_layout.addWidget(self._ws_path_label)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(24)

        self._stat_wiki = self._create_stat_widget("📄", "Wiki Pages", "0")
        self._stat_specs = self._create_stat_widget("📐", "Specs", "0")
        self._stat_changes = self._create_stat_widget("🔀", "Changes", "0")

        stats_row.addWidget(self._stat_wiki)
        stats_row.addWidget(self._stat_specs)
        stats_row.addWidget(self._stat_changes)
        stats_row.addStretch()

        card_layout.addLayout(stats_row)
        info_layout.addWidget(self._info_card)

        # Quick actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        btn_import = QPushButton("📥  Import Docs")
        btn_import.setObjectName("primary_button")
        btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_import.clicked.connect(self.import_docs_requested.emit)
        actions_layout.addWidget(btn_import)

        btn_change = QPushButton("📐  New Change")
        btn_change.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_change.clicked.connect(self.new_change_requested.emit)
        actions_layout.addWidget(btn_change)

        btn_analyze = QPushButton("🔧  Analyze Codebase")
        btn_analyze.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_analyze.clicked.connect(self.analyze_codebase_requested.emit)
        actions_layout.addWidget(btn_analyze)

        actions_layout.addStretch()
        info_layout.addLayout(actions_layout)

        self._container_layout.addWidget(
            self._info_section, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self._container_layout.addStretch()

    # ════════════════════════════════════════════════════════════════════
    # PRIVATE SLOTS (respond to user interactions)
    # ════════════════════════════════════════════════════════════════════

    def _on_open_clicked(self) -> None:
        """User clicks 'Open Workspace' → opens file dialog."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select SDD Workspace Directory",
            "",
            QFileDialog.Option.ShowDirsOnly,
        )
        if path:
            self._pending_path = path
            self.open_requested.emit(path)

    def _on_recent_clicked(self, path: str) -> None:
        """User clicks a recent workspace."""
        self._pending_path = path
        self.open_requested.emit(path)

    # ════════════════════════════════════════════════════════════════════
    # PUBLIC SLOTS (called by controller via signal)
    # ════════════════════════════════════════════════════════════════════

    def on_workspace_validated(self, result: dict) -> None:
        """Handles the validation result.

        If the workspace is invalid, shows a dialog asking
        the user if they want to initialize the SDD structure.
        """
        if result["valid"]:
            # Validation OK — controller will emit workspace_opened
            return

        # Invalid workspace: propose initialization
        missing_count = len(result["missing_dirs"]) + len(result["missing_files"])

        reply = QMessageBox.question(
            self,
            "Invalid SDD Workspace",
            f"The selected folder does not have a complete SDD structure.\n\n"
            f"Missing {missing_count} items "
            f"({len(result['missing_dirs'])} directories, "
            f"{len(result['missing_files'])} files).\n\n"
            f"Do you want to initialize the SDD structure in this folder?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if reply == QMessageBox.StandardButton.Yes and self._pending_path:
            self.init_requested.emit(self._pending_path)

    def on_workspace_opened(self, info: dict) -> None:
        """Updates the UI to show opened workspace info."""
        self._ws_name_label.setText(info.get("name", "Workspace"))
        self._ws_path_label.setText(info.get("path", ""))

        stats = info.get("stats", {})
        self._update_stat(self._stat_wiki, str(stats.get("wiki_pages", 0)))
        self._update_stat(self._stat_specs, str(stats.get("specs", 0)))
        self._update_stat(self._stat_changes, str(stats.get("changes", 0)))

        # Show the info panel, hide welcome
        self._welcome_section.hide()
        self._recent_section.hide()
        self._info_section.show()

    def on_workspace_error(self, message: str) -> None:
        """Shows a workspace error."""
        QMessageBox.critical(self, "Workspace Error", message)

    def populate_recent(self, recent: list[dict]) -> None:
        """Populates the list of recent workspaces.

        Each element of *recent* is a dict with 'name', 'path', 'stats'.
        """
        # Clear previous list
        while self._recent_list_layout.count():
            item = self._recent_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not recent:
            self._no_recent_label = QLabel("No recent workspaces")
            self._no_recent_label.setObjectName("section_subtitle")
            self._no_recent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._recent_list_layout.addWidget(self._no_recent_label)
            return

        for info in recent:
            row = self._create_recent_row(info)
            self._recent_list_layout.addWidget(row)

    # ════════════════════════════════════════════════════════════════════
    # FACTORY WIDGET HELPER
    # ════════════════════════════════════════════════════════════════════

    def _create_stat_widget(self, icon: str, label: str, value: str) -> QWidget:
        """Creates a mini-stat widget (icon + label + value)."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        val = QLabel(f"{icon}  {value}")
        val.setObjectName("stat_value")
        
        layout.addWidget(val)

        lbl = QLabel(label)
        lbl.setObjectName("section_subtitle")
        
        layout.addWidget(lbl)

        return w

    @staticmethod
    def _update_stat(widget: QWidget, value: str) -> None:
        """Updates the numeric value in a stat widget."""
        val_label = widget.findChild(QLabel, "stat_value")
        if val_label:
            # Preserve icon from current text
            current = val_label.text()
            icon = current.split("  ")[0] if "  " in current else ""
            val_label.setText(f"{icon}  {value}")

    def _create_recent_row(self, info: dict) -> QWidget:
        """Creates a row for a recent workspace.

        Shows name, abbreviated path, and compact stats.
        Clicking the entire row emits open_requested.
        """
        row = QFrame()
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setObjectName("recent_row")

        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(16, 14, 16, 14)
        row_layout.setSpacing(6)

        name = QLabel(info.get("name", "Unknown"))
        name.setObjectName("recent_row_name")
        name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row_layout.addWidget(name)

        path_text = info.get("path", "")
        if len(path_text) > 90:
            path_text = "..." + path_text[-85:]
        path_label = QLabel(path_text)
        path_label.setObjectName("section_subtitle")
        path_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row_layout.addWidget(path_label)

        stats = info.get("stats", {})
        stats_text = (
            f"📄 {stats.get('wiki_pages', 0)} pages  •  "
            f"📐 {stats.get('specs', 0)} specs  •  "
            f"🔀 {stats.get('changes', 0)} changes"
        )
        stats_label = QLabel(stats_text)
        stats_label.setObjectName("section_subtitle")
        stats_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row_layout.addWidget(stats_label)

        ws_path = info.get("path", "")
        # Handle click directly on the frame
        row.mousePressEvent = lambda e, p=ws_path: self._on_recent_clicked(p)

        return row
