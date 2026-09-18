"""MainWindow — SDD Orchestrator main window.

4-zone layout like LLM Wiki (`app-layout.tsx`, §7.1 of claude.md):

┌────┬──────────────────┬──────────────────────────┬──────────────────┐
│Icon│  Sidebar Panel   │      Content Area        │ Research Panel   │
│Side│  (150-400px,     │  (flex-1, QStackedWidget)│ (collapsible,    │
│bar │   collapsible)   │                          │  hidden init.)   │
│48px│                  │                          │                  │
└────┴──────────────────┴──────────────────────────┴──────────────────┘

Visibility rules (§7.2):
- STANDALONE views (chat, settings, cli_status): sidebar and research hidden
- EMBEDDED views (wiki, sources, search, graph, ...): sidebar visible

View routing (§7.3) uses a QStackedWidget to switch views.
Each view is created as a placeholder QWidget at this stage — they will be
replaced with real implementations in subsequent iterations.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from views.sidebar import IconSidebar, SidebarPanel


# ── Mapping view_id → index in QStackedWidget ───────────────────────
# Order defined in §7.1 of claude.md

VIEW_INDEX_MAP: dict[str, int] = {
    "workspace": 0,
    "chat": 1,
    "wiki": 2,
    "codebase": 3,
    "graph": 4,
    "openspec": 5,
    "search": 6,
    "review": 7,
    "cli_status": 8,
    "settings": 9,
    "sources": 10,
    "lint": 11,
    "skills": 12,
}

# ── Visibility rules (§7.2) ─────────────────────────────────────────
STANDALONE_VIEWS: set[str] = {"chat", "settings", "cli_status", "skills"}
EMBEDDED_VIEWS: set[str] = {
    "workspace", "wiki", "sources", "search", "graph",
    "openspec", "review", "codebase", "lint",
}


class MainWindow(QMainWindow):
    """Main window. Layout and view routing orchestrator."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SDD Orchestrator")
        self.setMinimumSize(960, 600)

        self._current_view: str = "workspace"
        self._return_view: str | None = None  # for "back" navigation

        self._setup_ui()
        self._setup_menu()
        self._connect_signals()

        # Initial view: workspace (welcome screen)
        self._switch_view("workspace")

    # ════════════════════════════════════════════════════════════════════
    # UI SETUP
    # ════════════════════════════════════════════════════════════════════

    def _setup_menu(self) -> None:
        """Configures the QMenuBar (on macOS it integrates into the top system menu)."""
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("File")
        
        switch_action = file_menu.addAction("Switch Workspace...")
        switch_action.setShortcut("Ctrl+O")
        switch_action.triggered.connect(lambda: self._switch_view("workspace"))
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

    def _setup_ui(self) -> None:
        """Builds the complete widget hierarchy."""
        central = QWidget()
        central.setObjectName("central_widget")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # ── 1 and 2. Left Group (IconSidebar + SidebarPanel) ──────────
        self._left_group = QFrame()
        self._left_group.setObjectName("left_group")
        left_layout = QHBoxLayout(self._left_group)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Icon Sidebar (fixed 48px)
        self._icon_sidebar = IconSidebar()
        left_layout.addWidget(self._icon_sidebar)

        # Sidebar Panel (150-400px, collapsible)
        self._sidebar_panel = SidebarPanel()
        left_layout.addWidget(self._sidebar_panel)

        main_layout.addWidget(self._left_group)

        # ── 3. Content Area (stretch=1, takes up all space) ─────
        self._content_area = QWidget()
        self._content_area.setObjectName("content_area")
        content_layout = QVBoxLayout(self._content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 3a. Toolbar bar (search + agent selector + actions)
        self._toolbar_bar = QWidget()
        self._toolbar_bar.setObjectName("toolbar_bar")
        toolbar_layout = QHBoxLayout(self._toolbar_bar)
        toolbar_layout.setContentsMargins(12, 0, 12, 0)

        self._toolbar_title = QLabel("SDD Orchestrator")
        self._toolbar_title.setObjectName("toolbar_title")
        toolbar_layout.addWidget(self._toolbar_title)
        toolbar_layout.addStretch()

        self.btn_import_docs = QPushButton("+ Import Docs")
        toolbar_layout.addWidget(self.btn_import_docs)

        content_layout.addWidget(self._toolbar_bar)

        # 3b. QStackedWidget (dynamic view switch)
        self._page_stack = QStackedWidget()
        self._page_stack.setObjectName("page_stack")
        self._create_placeholder_views()
        content_layout.addWidget(self._page_stack, stretch=1)

        # 3c. Status bar
        self._status_bar_widget = QWidget()
        self._status_bar_widget.setObjectName("status_bar")
        status_layout = QHBoxLayout(self._status_bar_widget)
        status_layout.setContentsMargins(12, 0, 12, 0)

        self._workspace_label = QLabel("No workspace open")
        status_layout.addWidget(self._workspace_label)
        status_layout.addStretch()

        self._cli_count_label = QLabel("CLI: pending scan")
        status_layout.addWidget(self._cli_count_label)

        self._agent_label = QLabel("Agent: none")
        status_layout.addWidget(self._agent_label)

        content_layout.addWidget(self._status_bar_widget)

        main_layout.addWidget(self._content_area, stretch=1)

        # ── 4. Research Panel (collapsible, hidden at startup) ─────
        self._research_panel = QWidget()
        self._research_panel.setObjectName("research_panel")
        self._research_panel.setMinimumWidth(250)
        self._research_panel.setMaximumWidth(600)
        research_layout = QVBoxLayout(self._research_panel)
        research_layout.setContentsMargins(8, 8, 8, 8)
        research_label = QLabel("Research Panel")
        research_label.setObjectName("section_subtitle")
        research_layout.addWidget(research_label)
        research_layout.addStretch()

        self._research_panel.hide()  # hidden at startup
        main_layout.addWidget(self._research_panel)

    def _create_placeholder_views(self) -> None:
        """Creates placeholder widgets for each view in the stack.

        In this iteration, they are all simple placeholders.
        They will be replaced with real implementations (WorkspaceView,
        ChatView, WikiBrowserView, etc.) in subsequent iterations.
        """
        view_labels: dict[str, str] = {
            "workspace": "🏠  Welcome — Open or create a workspace",
            "chat": "💬  Chat — Conversation with AI",
            "wiki": "📄  Wiki — Knowledge Base Browser",
            "codebase": "🔧  Codebase — Analysis & Structure",
            "graph": "🕸  Graph — Knowledge Graph Visualization",
            "openspec": "📐  OpenSpec — Specification Workflow",
            "search": "🔍  Search — Semantic Search",
            "review": "📋  Review — Human-in-the-Loop",
            "cli_status": "⚡  CLI Status — AI Tools Discovery",
            "settings": "⚙️  Settings — Configuration",
            "sources": "📂  Sources — Raw Documents",
            "lint": "✅  Lint — Wiki Health Check",
            "skills": "✨  Skills — Agent Skills Library",
        }

        for view_id in VIEW_INDEX_MAP:
            page = QWidget()
            page.setObjectName(f"page_{view_id}")
            page_layout = QVBoxLayout(page)
            page_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            label = QLabel(view_labels.get(view_id, view_id))
            label.setObjectName("section_title")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            page_layout.addWidget(label)

            subtitle = QLabel(f"This view will be implemented in a future iteration.")
            subtitle.setObjectName("section_subtitle")
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            page_layout.addWidget(subtitle)

            self._page_stack.addWidget(page)

    # ════════════════════════════════════════════════════════════════════
    # SIGNAL/SLOT WIRING
    # ════════════════════════════════════════════════════════════════════

    def _connect_signals(self) -> None:
        """Connects sidebar signals to view routing."""
        self._icon_sidebar.nav_clicked.connect(self._on_nav_clicked)

    # ════════════════════════════════════════════════════════════════════
    # VIEW ROUTING (§7.3 of claude.md)
    # ════════════════════════════════════════════════════════════════════

    def _on_nav_clicked(self, view_id: str) -> None:
        """Navigation click handler: changes view and updates layout.

        Logic inspired by wiki-store.ts from LLM Wiki:
        - Save return view for "back" navigation
        - Update QStackedWidget
        - Update sidebar/research visibility
        """
        # Save return view (like LLM Wiki previewReturnView)
        if view_id == "wiki" and self._current_view in ("search", "review"):
            self._return_view = self._current_view

        self._switch_view(view_id)

    def _switch_view(self, view_id: str) -> None:
        """Switch active view in QStackedWidget + update layout."""
        if view_id not in VIEW_INDEX_MAP:
            return

        self._page_stack.setCurrentIndex(VIEW_INDEX_MAP[view_id])
        self._update_layout_visibility(view_id)
        self._icon_sidebar.set_active_view(view_id)
        self._current_view = view_id

        # Update toolbar title
        titles: dict[str, str] = {
            "workspace": "SDD Orchestrator",
            "chat": "Chat",
            "wiki": "Knowledge Base",
            "sources": "Sources",
            "search": "Search",
            "graph": "Knowledge Graph",
            "lint": "Lint",
            "review": "Review",
            "skills": "Skills",
            "settings": "Settings",
            "cli_status": "CLI Status",
            "codebase": "Codebase Analysis",
            "openspec": "OpenSpec Workflow",
        }
        self._toolbar_title.setText(titles.get(view_id, view_id.title()))

    def _update_layout_visibility(self, view_id: str) -> None:
        """Applies standalone/embedded visibility rules (§7.2).

        - STANDALONE (chat, settings, cli_status, skills):
          sidebar_panel and research_panel hidden → content uses 100% width
        - EMBEDDED (wiki, sources, search, graph, ...):
          sidebar_panel visible, research_panel available
        """
        if view_id in STANDALONE_VIEWS:
            self._sidebar_panel.hide()
            self._research_panel.hide()
            self._left_group.setFixedWidth(76)
        elif view_id in EMBEDDED_VIEWS:
            self._sidebar_panel.show()
            self._left_group.setMinimumWidth(0)
            self._left_group.setMaximumWidth(16777215)
            # research panel remains hidden until activated by the user
        else:
            # Fallback: show sidebar
            self._sidebar_panel.show()
            self._left_group.setMinimumWidth(0)
            self._left_group.setMaximumWidth(16777215)

    # ════════════════════════════════════════════════════════════════════
    # PUBLIC API (used by Controllers in subsequent iterations)
    # ════════════════════════════════════════════════════════════════════

    @property
    def icon_sidebar(self) -> IconSidebar:
        return self._icon_sidebar

    @property
    def sidebar_panel(self) -> SidebarPanel:
        return self._sidebar_panel

    @property
    def page_stack(self) -> QStackedWidget:
        return self._page_stack

    def set_workspace_path(self, path: str) -> None:
        """Updates the workspace label in the status bar."""
        self._workspace_label.setText(path)

    def set_cli_count(self, found: int, total: int) -> None:
        """Updates the CLI count in the status bar."""
        self._cli_count_label.setText(f"CLI: {found}/{total} found")

    def set_active_agent(self, name: str) -> None:
        """Updates the active agent name in the status bar."""
        self._agent_label.setText(f"Agent: {name}")

    def replace_view(self, view_id: str, widget: QWidget) -> None:
        """Replaces a placeholder with the real widget.

        Used by subsequent iterations to inject the implemented
        views (WorkspaceView, ChatView, etc.) in place of the
        placeholders.
        """
        if view_id not in VIEW_INDEX_MAP:
            return
        index = VIEW_INDEX_MAP[view_id]
        old = self._page_stack.widget(index)
        self._page_stack.removeWidget(old)
        old.deleteLater()
        self._page_stack.insertWidget(index, widget)
