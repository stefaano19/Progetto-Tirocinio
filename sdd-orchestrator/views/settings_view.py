"""Settings View.

Implements the standalone settings view, including the Agent Selector (Step 1.5).
"""

from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from controllers.cli_controller import CLIController
from models.agent_model import AgentModel


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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        # Title
        title = QLabel("Settings")
        title.setObjectName("h1")
        main_layout.addWidget(title)

        # Form layout for settings
        form_layout = QFormLayout()
        form_layout.setSpacing(16)
        
        # Agent Selector
        self.agent_combo = QComboBox()
        self.agent_combo.setMinimumWidth(200)
        
        form_layout.addRow("Preferred AI Agent:", self.agent_combo)

        main_layout.addLayout(form_layout)
        main_layout.addStretch()

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

            binary_path = ""
            for info in self.cli_controller.last_results:
                if info.key == config.cli_key and info.found:
                    binary_path = info.path or ""
                    break

            self.agent_changed.emit(config.display_name, config.cli_key, binary_path)
