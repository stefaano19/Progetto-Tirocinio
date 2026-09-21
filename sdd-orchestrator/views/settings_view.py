"""Settings View.

Implements the standalone settings view, including the Agent Selector (Step 1.5).
"""

from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from controllers.cli_controller import CLIController
from models.agent_model import AgentModel
from views.widgets.status_indicator import StatusIndicator


class SettingsView(QWidget):
    """Main settings view."""

    agent_changed = Signal(str, str, str)  # display_name, cli_key, binary_path

    def __init__(self, cli_controller: CLIController, agent_model: AgentModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.cli_controller = cli_controller
        self.agent_model = agent_model
        self.settings = QSettings()

        self._setup_ui()
        self._connect_signals()
        self._populate_agents()

    def _setup_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(32, 32, 32, 32)
        outer_layout.setSpacing(4)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Settings")
        title.setObjectName("h1")
        outer_layout.addWidget(title)

        subtitle = QLabel("Configure how SDD Orchestrator talks to your AI CLIs.")
        subtitle.setObjectName("section_subtitle")
        outer_layout.addWidget(subtitle)

        # Content column with a capped width so the card reads well instead
        # of stretching edge-to-edge on a wide window.
        content = QWidget()
        content.setMaximumWidth(560)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 24, 0, 0)
        content_layout.setSpacing(16)
        content_layout.addWidget(self._build_agent_card())

        outer_layout.addWidget(content)
        outer_layout.addStretch()

    def _build_agent_card(self) -> QFrame:
        """"Preferred AI Agent" card: combo box + live found/not-found status."""
        card = QFrame()
        card.setObjectName("settings_card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(4)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        icon = QLabel("\U0001F916")  # robot emoji
        icon.setObjectName("settings_card_icon")
        header_row.addWidget(icon)

        card_title = QLabel("Preferred AI Agent")
        card_title.setObjectName("h2")
        header_row.addWidget(card_title)
        header_row.addStretch()
        layout.addLayout(header_row)

        description = QLabel("Used for chat responses and OpenSpec generation.")
        description.setObjectName("section_subtitle")
        description.setWordWrap(True)
        layout.addWidget(description)

        layout.addSpacing(12)

        self.agent_combo = QComboBox()
        self.agent_combo.setObjectName("settings_combo")
        self.agent_combo.setMinimumHeight(36)
        layout.addWidget(self.agent_combo)

        layout.addSpacing(10)

        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        self.agent_status_indicator = StatusIndicator()
        status_row.addWidget(self.agent_status_indicator)

        self.agent_status_label = QLabel("No agent selected")
        self.agent_status_label.setObjectName("settings_status_label")
        status_row.addWidget(self.agent_status_label)
        status_row.addStretch()
        layout.addLayout(status_row)

        return card

    def _connect_signals(self) -> None:
        self.agent_combo.currentTextChanged.connect(self._on_agent_changed)
        self.cli_controller.cli_scan_complete.connect(self._on_scan_complete)

    def _populate_agents(self) -> None:
        """Populates the combo box with available agents from the last scan."""
        configs = self.agent_model.get_available_agents(self.cli_controller.last_results)
        self.agent_combo.blockSignals(True)
        self.agent_combo.clear()

        if not configs:
            self.agent_combo.addItem("No agents available")
            self.agent_combo.setEnabled(False)
            self.agent_combo.blockSignals(False)
            self._update_agent_status(None)
            return

        self.agent_combo.setEnabled(True)
        for config in configs:
            self.agent_combo.addItem(config.display_name, userData=config)

        # Select the preferred one if it exists
        preferred = self.settings.value("settings/preferred_cli")
        if preferred:
            idx = self.agent_combo.findText(str(preferred))
            if idx >= 0:
                self.agent_combo.setCurrentIndex(idx)
        self.agent_combo.blockSignals(False)
        self._update_agent_status(self.agent_combo.currentData())

    def _update_agent_status(self, config) -> None:
        """Reflects whether the selected agent's CLI was found on the last scan."""
        if config is None:
            self.agent_status_indicator.set_status("idle")
            self.agent_status_label.setText("No agent selected")
            return

        found = any(
            info.key == config.cli_key and info.found
            for info in self.cli_controller.last_results
        )
        if found:
            self.agent_status_indicator.set_status("ok")
            self.agent_status_label.setText(f"{config.display_name} is available")
        else:
            self.agent_status_indicator.set_status("error")
            self.agent_status_label.setText(f"{config.display_name} was not found on last scan")

    def _on_scan_complete(self, results: list) -> None:
        """Updates the list of agents when a scan completes."""
        self._populate_agents()

    def _on_agent_changed(self, text: str) -> None:
        """Saves the preferred agent when changed."""
        if not self.agent_combo.isEnabled():
            return

        config = self.agent_combo.currentData()
        if config:
            self.agent_model.set_active_agent(config)
            self.settings.setValue("settings/preferred_cli", config.display_name)
            self._update_agent_status(config)

            binary_path = ""
            for info in self.cli_controller.last_results:
                if info.key == config.cli_key and info.found:
                    binary_path = info.path or ""
                    break

            self.agent_changed.emit(config.display_name, config.cli_key, binary_path)
