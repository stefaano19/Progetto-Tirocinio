"""CLI Status View — Shows the status of AI CLIs.

Implements the view defined in claude.md (Step 1.4.1):
card grid for each CLI, pulsating status indicator,
progress bar for scanning, and "Rescan" button.
"""

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from controllers.cli_controller import CLIController
from models.cli_discovery_model import CLIInfo
from views.widgets.status_indicator import StatusIndicator


class CLICard(QFrame):
    """Single card for a CLI."""

    def __init__(self, cli_info: CLIInfo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("cli_card")
        # Apply some inline style or rely on global QSS (using the name)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        self.cli_key = cli_info.key

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Header: Name + Indicator
        header_layout = QHBoxLayout()
        self.name_label = QLabel(cli_info.display_name)
        self.name_label.setObjectName("cli_card_name")

        self.indicator = StatusIndicator()
        
        header_layout.addWidget(self.name_label)
        header_layout.addStretch()
        header_layout.addWidget(self.indicator)
        
        layout.addLayout(header_layout)

        # Details: Path and Version
        self.path_label = QLabel()
        self.path_label.setObjectName("cli_card_path")
        self.path_label.setWordWrap(True)

        self.version_label = QLabel()
        self.version_label.setObjectName("cli_card_version")

        layout.addWidget(self.path_label)
        layout.addWidget(self.version_label)
        layout.addStretch()
        
        self._set_pending()

    def _set_pending(self) -> None:
        """Sets initial pending state before the first scan."""
        self.indicator.set_status("idle")
        self.path_label.setText("Pending scan...")
        self.version_label.setText("-")

    def update_info(self, info: CLIInfo) -> None:
        """Updates visual data based on CLI status."""
        if info.found:
            self.indicator.set_status("ok")
            self.path_label.setText(info.path or "Unknown path")
            self.version_label.setText(info.version or "Unknown version")
        else:
            self.indicator.set_status("error") # Or "idle" if preferred for not found
            self.path_label.setText("Not installed or not in PATH")
            self.version_label.setText("-")

    def set_scanning(self) -> None:
        """Sets status to scanning in progress."""
        self.indicator.set_status("scanning")
        self.path_label.setText("Scanning in progress...")
        self.version_label.setText("")


class CLIStatusView(QWidget):
    """Main view for CLI status."""

    def __init__(self, controller: CLIController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.cards: dict[str, CLICard] = {}

        self._setup_ui()
        self._connect_signals()
        
        # Initialize with empty data from registry (to have gray cards)
        # We don't expose the controller's Model directly,
        # but we can do it if we add registry_keys
        self._populate_initial_cards()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        # Header: Title and Rescan Button
        header_layout = QHBoxLayout()
        title = QLabel("System Requirements")
        title.setObjectName("h1")

        self.rescan_btn = QPushButton("Rescan System")
        self.rescan_btn.setMinimumWidth(120)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.rescan_btn)
        
        main_layout.addLayout(header_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # Grid for cards
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(16)
        main_layout.addLayout(self.grid_layout)
        
        main_layout.addStretch()

    def _populate_initial_cards(self) -> None:
        """Creates initial cards using registry data."""
        registry = self.controller._model.registry
        row, col = 0, 0
        max_cols = 3

        for cli_def in registry:
            info = CLIInfo(
                key=cli_def["key"],
                binary_name=cli_def["binary_name"],
                display_name=cli_def["display_name"],
                cli_type=cli_def["cli_type"],
            )
            card = CLICard(info)
            self.cards[info.key] = card
            
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
        # If there were already results (e.g., scan occurred), update them
        if self.controller.last_results:
            for info in self.controller.last_results:
                if info.key in self.cards:
                    self.cards[info.key].update_info(info)

    def _connect_signals(self) -> None:
        self.rescan_btn.clicked.connect(self.controller.start_scan)
        self.controller.cli_scan_started.connect(self._on_scan_started)
        self.controller.cli_found.connect(self._on_cli_found)
        self.controller.cli_scan_progress.connect(self._on_scan_progress)
        self.controller.cli_scan_complete.connect(self._on_scan_complete)
        self.controller.cli_scan_error.connect(self._on_scan_error)

    @Slot()
    def _on_scan_started(self) -> None:
        self.rescan_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        for card in self.cards.values():
            card.set_scanning()

    @Slot(object)
    def _on_cli_found(self, info: CLIInfo) -> None:
        if info.key in self.cards:
            self.cards[info.key].update_info(info)

    @Slot(int, int)
    def _on_scan_progress(self, current: int, total: int) -> None:
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"Scanning: {current}/{total}")

    @Slot(list)
    def _on_scan_complete(self, results: list) -> None:
        self.rescan_btn.setEnabled(True)
        self.progress_bar.hide()
        
    @Slot(str)
    def _on_scan_error(self, error_msg: str) -> None:
        self.rescan_btn.setEnabled(True)
        self.progress_bar.hide()
        # Reset any cards still in scanning state to error
        for card in self.cards.values():
            if card.indicator._status == "scanning":
                card.indicator.set_status("error")
                card.path_label.setText("Scan failed")
