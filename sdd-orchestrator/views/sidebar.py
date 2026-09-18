"""Sidebar — Icon rail (48px) + expandable panel.

Two-component architecture, inspired by LLM Wiki:

- **IconSidebar** (`icon-sidebar.tsx`): 48px vertical rail with icon-only
  navigation buttons, status dot, settings and project switch.

- **SidebarPanel** (`sidebar-panel.tsx`): Expandable panel (150-400px,
  default 220px) with Knowledge Tree / File Tree tabs and activity panel.

Navigation buttons emit `nav_clicked(str)` with the view_id.
MainWindow handles routing and visibility.
"""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTabWidget,
    QTreeView,
    QVBoxLayout,
    QWidget,
    QFrame,
)



# ── Navigation buttons definition (§3.3 of claude.md) ────────────────
# Each tuple: (view_id, icon_name, tooltip, is_top_section)

NAV_BUTTONS: list[tuple[str, str, str, bool]] = [
    # Top Section — Main Views
    ("wiki",     "file-text", "Knowledge Base",    True),
    ("graph",    "network", "Knowledge Graph",    True),
    ("lint",     "clipboard-check", "Lint & Fix",         True),
    ("chat",     "message-square", "Chat",               True),
    ("review",   "clipboard-list", "Review",             True),
    ("sources",  "folder-open", "Sources",            True),
    ("search",   "search", "Search",             True),
    # Bottom Section — System
    ("cli_status", "zap", "CLI Status",       False),
    ("settings", "settings", "Settings (⌘,)",    False),
]


class IconSidebar(QWidget):
    """48px icon rail — main app navigation.

    Emits `nav_clicked(view_id)` when the user clicks a button.
    MainWindow receives the signal and updates QStackedWidget + visibility.
    """

    nav_clicked = Signal(str)  # view_id of the requested view

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("icon_sidebar")
        self.setFixedWidth(76)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(2)
        
        # Determine icons dir
        from pathlib import Path
        self.icons_dir = Path(__file__).parent.parent / "assets" / "icons"



        # ── Navigation buttons (top section) ───────────────────────
        self._nav_buttons: dict[str, QPushButton] = {}

        for view_id, icon, tooltip, is_top in NAV_BUTTONS:
            if is_top:
                btn = self._create_nav_button(view_id, icon, tooltip)
                layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # ── Spacer to push bottom section down ──────────
        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # ── Navigation buttons (bottom section) ────────────────────
        for view_id, icon, tooltip, is_top in NAV_BUTTONS:
            if not is_top:
                btn = self._create_nav_button(view_id, icon, tooltip)
                layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)


    # ── Button factory ─────────────────────────────────────────────

    def _create_nav_button(self, view_id: str, icon_name: str, tooltip: str) -> QPushButton:
        btn = QPushButton()
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QSize
        btn.setIcon(QIcon(str(self.icons_dir / f"{icon_name}.svg")))
        btn.setIconSize(QSize(20, 20))
        btn.setObjectName(f"nav_{view_id}")
        btn.setToolTip(tooltip)
        btn.setCheckable(True)
        btn.setFixedSize(40, 40)
        btn.clicked.connect(lambda checked, vid=view_id: self._on_nav_clicked(vid))
        self._nav_buttons[view_id] = btn
        return btn

    # ── Navigation handler ─────────────────────────────────────────

    def _on_nav_clicked(self, view_id: str) -> None:
        """Updates checked state and emits signal."""
        # Deselect all others (radio behavior)
        for vid, btn in self._nav_buttons.items():
            btn.setChecked(vid == view_id)
        self.nav_clicked.emit(view_id)

    # ── Public API ────────────────────────────────────────────────

    def set_active_view(self, view_id: str) -> None:
        """Sets the active button (called by MainWindow)."""
        for vid, btn in self._nav_buttons.items():
            btn.setChecked(vid == view_id)



class SidebarPanel(QWidget):
    """Expandable panel (150-400px) with Knowledge/Files tabs.

    Inspired by `sidebar-panel.tsx` from LLM Wiki. Contains:
    - "Knowledge" tab: semantic wiki tree (QTreeView placeholder)
    - "Files" tab: filesystem explorer (QTreeView placeholder)
    - Activity Panel at bottom (task queue placeholder)

    Visibility is controlled by MainWindow based on active view:
    - Standalone views (chat, settings): sidebar hidden
    - Embedded views (wiki, graph, ...): sidebar visible
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar_panel")
        self.setMinimumWidth(220)
        self.setMaximumWidth(450)
        self.resize(300, self.height())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # ── Card Container for Tabs & Tree ──────────────────────────
        self._tree_card = QFrame()
        self._tree_card.setObjectName("tree_card")
        card_layout = QVBoxLayout(self._tree_card)
        card_layout.setContentsMargins(6, 0, 6, 12)
        card_layout.setSpacing(0)

        # ── Tab Widget (Knowledge / Files) ──────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setObjectName("sidebar_tabs")
        self._tabs.setElideMode(Qt.TextElideMode.ElideNone)
        self._tabs.setUsesScrollButtons(False)

        # Knowledge Tree Tab (placeholder)
        self._knowledge_tree = QTreeView()
        self._knowledge_tree.setFrameShape(QFrame.Shape.NoFrame)
        self._knowledge_tree.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        self._knowledge_tree.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._knowledge_tree.setHeaderHidden(True)
        self._tabs.addTab(self._knowledge_tree, "Knowledge")

        # File Tree Tab (placeholder)
        self._file_tree = QTreeView()
        self._file_tree.setFrameShape(QFrame.Shape.NoFrame)
        self._file_tree.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        self._file_tree.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._file_tree.setHeaderHidden(True)
        self._tabs.addTab(self._file_tree, "Files")

        card_layout.addWidget(self._tabs)
        layout.addWidget(self._tree_card, stretch=1)

        # ── Activity Panel ────────────────────────────
        from views.widgets.activity_panel import ActivityPanel
        self._activity = ActivityPanel()
        layout.addWidget(self._activity)

    @property
    def knowledge_tree(self) -> QTreeView:
        return self._knowledge_tree

    @property
    def file_tree(self) -> QTreeView:
        return self._file_tree
        
    @property
    def activity_panel(self):
        return self._activity
