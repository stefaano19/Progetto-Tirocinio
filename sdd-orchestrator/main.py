"""SDD Orchestrator — Entry point.

Starts the PySide6 application, loads the global QSS theme, instantiates
the MVC architecture and shows the MainWindow.

Step 1.1 — Wiring Workspace:
  Creates Model → Controller → View and connects them via signal/slot.
  The flow is defined in §8 of claude.md:

  1. App started → WorkspaceView shows Welcome Screen with recent projects
  2. User clicks "Open Workspace" → QFileDialog → open_requested(path)
  3. WorkspaceController.open_workspace(path)
     → model.validate_workspace(path)
  4. If valid → workspace_opened(path) → updates status bar + info panel
  5. If invalid → workspace_validated({valid: False, missing: [...]})
     → View shows QMessageBox: "Initialize?"
     → If yes → controller.initialize_workspace(path)
       → workspace_initialized(path) → workspace_opened(path)

Rules followed:
  - §10.5: QSS at QApplication level (NEVER inline)
  - §10.2: View emits signal, Controller handles logic
  - §12:   Font SF Pro 14px, size 1280×800
"""

import signal
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox

from controllers.cli_controller import CLIController
from controllers.workspace_controller import WorkspaceController
from views.main_window import MainWindow
from views.workspace_view import WorkspaceView
from models.agent_model import AgentModel


def apply_theme(app: QApplication) -> None:
    """Applies the correct theme based on system preferences."""
    scheme = app.styleHints().colorScheme()
    theme_file = "dark-theme.qss" if scheme == Qt.ColorScheme.Dark else "light-theme.qss"
    qss_path = Path(__file__).parent / "styles" / theme_file
    if qss_path.exists():
        qss_content = qss_path.read_text(encoding="utf-8")
        assets_dir = (Path(__file__).parent / "assets").as_posix()
        qss_content = qss_content.replace("%ASSETS_DIR%", assets_dir)
        app.setStyleSheet(qss_content)


def main() -> None:
    # Let Ctrl+C terminate the process immediately via the default OS
    # handler instead of Python's default SIGINT behavior, which raises
    # KeyboardInterrupt asynchronously — including, occasionally, in the
    # middle of a Qt->Python metacall (e.g. a running QPropertyAnimation),
    # producing a noisy but harmless traceback right as the app exits.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setApplicationName("SDD Orchestrator")
    app.setOrganizationName("SDD")

    # ── Base font 14px (like LLM Wiki Geist 14px) ──────────────────
    # On macOS we use SF Pro, cross-platform fallback Segoe UI / Helvetica
    font = QFont("SF Pro", 14)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # ── Global QSS loading ─────────────────────────────────────
    # Palette derived from LLM Wiki OKLCH analysis (§3.8 / §6)
    # Supports light and dark theme based on system settings
    apply_theme(app)
    app.styleHints().colorSchemeChanged.connect(lambda _: apply_theme(app))

    # ── MVC: Model → Controller → View ─────────────────────────────
    # The Controller instantiates the Model internally (see workspace_controller.py)
    ws_controller = WorkspaceController()
    cli_controller = CLIController()
    ws_view = WorkspaceView()

    # ── MainWindow ──────────────────────────────────────────────────
    window = MainWindow()
    window.resize(1280, 800)

    # Injects the real WorkspaceView instead of the placeholder
    # (uses the replace_view method defined in MainWindow §7.1)
    window.replace_view("workspace", ws_view)
    
    # Injects the real CLIStatusView (Step 1.4.2)
    from views.cli_status_view import CLIStatusView
    cli_status_view = CLIStatusView(cli_controller)
    window.replace_view("cli_status", cli_status_view)

    # ── Agent Model (Step 1.5 partial - removed selector view) ───────
    agent_model = AgentModel()

    # Load preferred CLI from settings immediately (on startup)
    settings = QSettings()
    preferred_cli = settings.value("settings/preferred_cli")
    if preferred_cli:
        window.set_active_agent(str(preferred_cli))

    # Injects the real SettingsView
    from views.settings_view import SettingsView
    settings_view = SettingsView(cli_controller, agent_model)
    window.replace_view("settings", settings_view)

    # ── Wiki Browser (Step 2.2) ─────────────────────────────────────
    from models.wiki_model import WikiModel
    from controllers.wiki_controller import WikiController
    from views.wiki_browser_view import WikiBrowserView
    
    wiki_model = WikiModel()
    wiki_controller = WikiController(wiki_model)
    wiki_browser_view = WikiBrowserView(wiki_controller, window.sidebar_panel.knowledge_tree)
    window.replace_view("wiki", wiki_browser_view)

    # ── Chat (Step 3.3) ─────────────────────────────────────────────
    from models.chat_model import ChatModel
    from controllers.chat_controller import ChatController
    from views.chat_view import ChatView

    chat_model = ChatModel()
    chat_controller = ChatController(chat_model)
    chat_controller.set_wiki_model(wiki_model)
    chat_view = ChatView()
    window.replace_view("chat", chat_view)

    # Agent picked manually from Settings → status bar + ChatController's
    # active CLI for subprocess invocation (§10.1: SettingsView resolves
    # the binary path itself, the controller only receives the result)
    settings_view.agent_changed.connect(
        lambda name, cli_key, path: (
            window.set_active_agent(name),
            chat_controller.set_active_cli(cli_key, path),
        )
    )

    # ── Codebase Analysis (Step 4.1.5) ──────────────────────────────
    from controllers.codebase_controller import CodebaseController
    from views.codebase_view import CodebaseView

    codebase_controller = CodebaseController()
    codebase_view = CodebaseView(codebase_controller)
    window.replace_view("codebase", codebase_view)

    ws_controller.workspace_opened.connect(codebase_view.set_workspace_root)

    # ── Signal/Slot Wiring (§8 of claude.md) ───────────────────────
    _wire_workspace(ws_view, ws_controller, window)
    _wire_chat(chat_view, chat_controller)
    
    # ── Additional Wiring Workspace -> Wiki & Files & Chat ───────────────────
    ws_controller.workspace_opened.connect(wiki_controller.set_workspace)
    ws_controller.workspace_opened.connect(chat_controller.set_workspace)
    
    # Setup Files tab (raw filesystem view)
    from PySide6.QtWidgets import QFileSystemModel, QFileIconProvider
    from PySide6.QtCore import QDir, QFileInfo
    from PySide6.QtGui import QIcon
    from pathlib import Path
    
    class LucideIconProvider(QFileIconProvider):
        def __init__(self):
            super().__init__()
            self.icons_dir = Path(__file__).parent / "assets" / "icons"
            self.folder_icon = QIcon(str(self.icons_dir / "folder.svg"))
            self.file_icon = QIcon(str(self.icons_dir / "file.svg"))
            
        def icon(self, file_info: QFileInfo) -> QIcon:
            if file_info.isDir():
                return self.folder_icon
            return self.file_icon

    file_system_model = QFileSystemModel()
    file_system_model.setIconProvider(LucideIconProvider())
    file_system_model.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllEntries)
    
    def _on_workspace_opened(path: str):
        # Set root path for the model and the view
        file_system_model.setRootPath(path)
        window.sidebar_panel.file_tree.setModel(file_system_model)
        window.sidebar_panel.file_tree.setRootIndex(file_system_model.index(path))
        
        # Hide standard columns (size, type, date) for a cleaner "tree" look
        for i in range(1, file_system_model.columnCount()):
            window.sidebar_panel.file_tree.hideColumn(i)
            
    ws_controller.workspace_opened.connect(_on_workspace_opened)
    
    # ── Import Wiring (Step 2.3.5) ──────────────────────────────────
    # The controller only emits signals (§10.1) — this wiring layer
    # connects them to the ActivityPanel widget and to user-facing dialogs.
    from views.wiki_import_view import WikiImportView

    activity_panel = window.sidebar_panel.activity_panel
    wiki_controller.import_started.connect(activity_panel.start_task)
    wiki_controller.import_progress.connect(activity_panel.update_task)
    wiki_controller.import_complete.connect(
        lambda task_id, count: (
            activity_panel.complete_task(task_id),
            QMessageBox.information(
                window,
                "Import Complete",
                f"Successfully imported {count} document(s) into the knowledge base raw folder.",
            ),
        )
    )

    def _show_import_dialog():
        if not ws_controller.current_path:
            QMessageBox.warning(
                window, "No Workspace", "Please open a workspace before importing documents."
            )
            return
        dialog = WikiImportView(window)
        dialog.import_requested.connect(wiki_controller.start_import)
        dialog.exec()

    window.btn_import_docs.clicked.connect(_show_import_dialog)

    # ── Welcome Screen quick actions (§5.1) ──────────────────────────
    # "Import Docs" reuses the same dialog as the toolbar button.
    ws_view.import_docs_requested.connect(_show_import_dialog)

    # "Analyze Codebase" switches to the Codebase view and starts analysis.
    def _on_analyze_codebase_requested():
        window.icon_sidebar.nav_clicked.emit("codebase")
        codebase_controller.analyze()

    ws_view.analyze_codebase_requested.connect(_on_analyze_codebase_requested)

    # "New Change" (OpenSpec workflow) is not implemented yet (Iteration 6) —
    # the signal exists and is emitted, just nothing listens to it yet.

    # ── CLI Scanning (Step 1.6) ─────────────────────────────────────
    # Start CLI scan automatically after opening workspace (Step 1.6.1)
    ws_controller.workspace_opened.connect(lambda path: cli_controller.start_scan())
    
    # ── CLI scan completed (Step 1.6.2, 1.6.3, 1.6.5 adapted) ──
    cli_controller.cli_scan_complete.connect(
        lambda results: _handle_cli_scan_complete(
            results, cli_controller, window, agent_model, chat_controller
        )
    )

    # Automatically start scanning on boot so the UI doesn't stay pending
    cli_controller.start_scan()

    # ── Populate recent projects on startup ────────────────────────────
    recent = ws_controller.get_recent_workspaces()
    ws_view.populate_recent(recent)

    if recent:
        # Auto-load the most recent project
        ws_controller.open_workspace(recent[0]["path"])
        # Switch to the wiki view by simulating a click on the wiki nav button
        window.icon_sidebar.nav_clicked.emit("wiki")

    # ── Show the window ──────────────────────────────────────────
    window.show()

    sys.exit(app.exec())


def _wire_workspace(
    view: WorkspaceView,
    controller: WorkspaceController,
    window: MainWindow,
) -> None:
    """Connects signal/slots between WorkspaceView, Controller and MainWindow.

    Complete signal flow (§8 — Workspace Flow):

    VIEW → CONTROLLER:
      view.open_requested(path)  →  controller.open_workspace(path)
      view.init_requested(path)  →  controller.initialize_workspace(path)

    CONTROLLER → VIEW:
      controller.workspace_validated(result)  →  view.on_workspace_validated(result)
      controller.workspace_stats_ready(info)  →  view.on_workspace_opened(info)
      controller.workspace_error(msg)         →  view.on_workspace_error(msg)

    CONTROLLER → MAIN WINDOW:
      controller.workspace_opened(path)       →  window.set_workspace_path(path)

    Why it works like this:
    - The View emits signals when the user interacts (click on Open,
      click on recent, confirm init). NEVER call the Model directly.
    - The Controller receives, executes logic via the Model, and emits
      result signals.
    - The View and MainWindow listen to results and update the UI.
    """
    # VIEW → CONTROLLER
    # User selects a folder → controller validates and opens it
    view.open_requested.connect(controller.open_workspace)

    # User confirms initialization → controller creates SDD structure
    view.init_requested.connect(controller.initialize_workspace)

    # CONTROLLER → VIEW
    # Validation result → view shows dialog if invalid
    controller.workspace_validated.connect(view.on_workspace_validated)

    # Stats ready → view updates info card with name, path, counts
    controller.workspace_stats_ready.connect(view.on_workspace_opened)

    # Error → view shows a critical QMessageBox
    controller.workspace_error.connect(view.on_workspace_error)

    # CONTROLLER → MAIN WINDOW
    # Workspace opened successfully → updates the bottom status bar
    controller.workspace_opened.connect(window.set_workspace_path)


def _wire_chat(
    view: "ChatView",
    controller: "ChatController",
) -> None:
    """Connects signal/slots for the Chat feature."""
    # View -> Controller
    # Show the user's own message immediately — nothing else does this,
    # the controller only persists it and drives the assistant's reply.
    view.send_requested.connect(lambda text: view.add_message("user", text))
    view.send_requested.connect(controller.send_message)
    view.new_chat_requested.connect(controller.start_new_chat)
    view.conversation_selected.connect(controller.load_chat)
    
    # Controller -> View
    controller.history_updated.connect(view.populate_sidebar)
    
    # To handle streaming properly without maintaining state in main.py,
    # we bind stateful closures here
    active_bubble = [None]
    
    def on_conversation_loaded(messages):
        view.clear_messages()
        for msg in messages:
            view.add_message(msg.role, msg.content)
            
    def on_stream_token(text):
        if not active_bubble[0]:
            active_bubble[0] = view.add_message("assistant", "")
        active_bubble[0].update_content(text)
        # update_content() bypasses add_message(), which is what normally
        # keeps the view pinned to the bottom — without this, the visible
        # area stays put while the bubble grows and the tail looks clipped.
        view.scroll_to_bottom()
        
    def on_tool_executed(name, detail):
        active_bubble[0] = None  # Reset so the next text gets a new bubble
        view.add_tool_stage(name, detail)
        
    def on_stream_finished():
        active_bubble[0] = None
        
    def on_stream_error(err):
        active_bubble[0] = None
        view.add_message("system", f"**Error:** {err}")
        
    controller.conversation_loaded.connect(on_conversation_loaded)
    controller.stream_token.connect(on_stream_token)
    controller.tool_executed.connect(on_tool_executed)
    controller.stream_finished.connect(on_stream_finished)
    controller.stream_error.connect(on_stream_error)


def _handle_cli_scan_complete(
    results: list, cli_controller: CLIController, window: MainWindow,
    agent_model: AgentModel, chat_controller: "ChatController"
) -> None:
    """Handles CLI scan completion and preferred selection."""
    settings = QSettings()
    preferred_cli = settings.value("settings/preferred_cli")

    # Update AgentModel
    configs = agent_model.get_available_agents(results)

    available_names = [config.display_name for config in configs]

    window.set_cli_count(len(configs), len(results))

    def set_active(name: str):
        for config in configs:
            if config.display_name == name:
                agent_model.set_active_agent(config)
                window.set_active_agent(config.display_name)
                settings.setValue("settings/preferred_cli", config.display_name)

                # Resolve the binary path for this CLI so ChatController can
                # actually spawn it (§10.1: the controller doesn't resolve
                # this itself from a display name)
                binary_path = next(
                    (info.path for info in results if info.key == config.cli_key and info.found),
                    None,
                )
                chat_controller.set_active_cli(config.cli_key, binary_path or "")
                return
        window.set_active_agent("No selection")

    if preferred_cli and preferred_cli in available_names:
        set_active(str(preferred_cli))
    else:
        if available_names:
            # Set the first available CLI silently without prompting
            set_active(available_names[0])
        else:
            window.set_active_agent("No CLI found")


if __name__ == "__main__":
    main()
