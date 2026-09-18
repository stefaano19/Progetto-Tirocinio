import markdown
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser, QTreeView, QLabel
)

from utils.markdown_parser import ParsedIndex
from controllers.wiki_controller import WikiController


class KnowledgeTreeModel(QStandardItemModel):
    """Model to populate the Sidebar QTreeView with index categories and links."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def populate(self, parsed_index: ParsedIndex | None):
        self.clear()
        if not parsed_index:
            return
            
        # Icon map by category
        ICONS = {
            "Entities": "users",
            "Concepts": "lightbulb",
            "Sources": "book-open",
            "Decisions": "target",
            "Open Questions": "help-circle",
        }
            
        from PySide6.QtGui import QIcon
        from pathlib import Path
        
        icons_dir = Path(__file__).parent.parent / "assets" / "icons"
        
        for category in parsed_index.categories:
            icon_name = ICONS.get(category.name, "folder-open")
            cat_icon = QIcon(str(icons_dir / f"{icon_name}.svg"))
            
            cat_item = QStandardItem(cat_icon, category.name)
            cat_item.setSelectable(False)
            
            for link in category.links:
                link_icon = QIcon(str(icons_dir / "file-text.svg"))
                link_item = QStandardItem(link_icon, link.title)
                # Save the path in UserRole to retrieve it on click
                link_item.setData(link.url, Qt.ItemDataRole.UserRole)
                # Tooltip with description
                if link.description:
                    link_item.setToolTip(link.description)
                    
                cat_item.appendRow(link_item)
                
            self.appendRow(cat_item)


class WikiBrowserView(QWidget):
    """Main view to read Knowledge Base pages.
    Includes a top navigation toolbar and a QTextBrowser.
    """
    def __init__(self, controller: WikiController, sidebar_tree: QTreeView, parent=None):
        super().__init__(parent)
        self.setObjectName("wiki_browser")
        self._controller = controller
        self._sidebar_tree = sidebar_tree
        
        self._setup_ui()
        self._setup_tree()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        self._toolbar = QWidget()
        self._toolbar.setObjectName("reader_toolbar")
        toolbar_layout = QHBoxLayout(self._toolbar)
        toolbar_layout.setContentsMargins(16, 8, 16, 8)
        
        self._btn_back = QPushButton("◀ Back")
        self._btn_forward = QPushButton("Forward ▶")
        self._btn_refresh = QPushButton("↻ Refresh")
        
        # Base styles
        self._btn_back.setFlat(True)
        self._btn_forward.setFlat(True)
        self._btn_refresh.setFlat(True)
        
        self._page_title = QLabel("Select a page from the Knowledge Tree")
        self._page_title.setObjectName("section_subtitle")
        self._page_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        toolbar_layout.addWidget(self._btn_back)
        toolbar_layout.addWidget(self._btn_forward)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self._page_title)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self._btn_refresh)
        
        layout.addWidget(self._toolbar)
        
        # Text Browser to display HTML
        self._reader = QTextBrowser()
        self._reader.setObjectName("page_reader")
        self._reader.setOpenExternalLinks(True)
        # Readable base font for content
        font = self._reader.font()
        font.setPointSize(14)
        self._reader.setFont(font)
        
        layout.addWidget(self._reader, stretch=1)

    def _setup_tree(self):
        """Prepares the model for the QTreeView passed from the MainWindow."""
        self._tree_model = KnowledgeTreeModel(self)
        self._sidebar_tree.setModel(self._tree_model)
        self._sidebar_tree.setHeaderHidden(True)
        
        # When an item is clicked
        self._sidebar_tree.clicked.connect(self._on_tree_clicked)
        
    def _connect_signals(self):
        self._controller.index_loaded.connect(self._on_index_loaded)
        self._controller.page_loaded.connect(self._on_page_loaded)
        self._controller.error_occurred.connect(self._on_error)
        
        self._btn_refresh.clicked.connect(self._controller.load_index)
        
        # QTextBrowser has built-in back/forward
        self._btn_back.clicked.connect(self._reader.backward)
        self._btn_forward.clicked.connect(self._reader.forward)
        self._reader.backwardAvailable.connect(self._btn_back.setEnabled)
        self._reader.forwardAvailable.connect(self._btn_forward.setEnabled)
        
        self._btn_back.setEnabled(False)
        self._btn_forward.setEnabled(False)

    def _on_tree_clicked(self, index):
        # Ignore clicks on unselectable categories
        item = self._tree_model.itemFromIndex(index)
        if not item or not item.isSelectable():
            return
            
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            # Emits to the controller to load the page
            self._controller.page_selected.emit(path)

    def _on_index_loaded(self, parsed_index: ParsedIndex | None):
        """The index has been read, populate the tree."""
        self._tree_model.populate(parsed_index)
        self._sidebar_tree.expandAll()
        
    def _on_page_loaded(self, page_path: str, markdown_content: str):
        """Renders markdown to HTML and displays it in the reader."""
        self._page_title.setText(page_path)
        
        # Use the 'markdown' module to convert
        # We could use extensions for tables or fenced code blocks
        html = markdown.markdown(
            markdown_content, 
            extensions=['fenced_code', 'tables']
        )
        
        # Add basic inline CSS for page styling
        styled_html = f"""
        <html>
        <head>
        <style>
            body {{ font-family: -apple-system, system-ui, sans-serif; line-height: 1.6; color: #dddddd; padding: 20px; }}
            h1, h2, h3 {{ color: #ffffff; border-bottom: 1px solid #444; padding-bottom: 5px; }}
            a {{ color: #58a6ff; text-decoration: none; }}
            code {{ background-color: #2b2d31; padding: 2px 4px; border-radius: 4px; }}
            pre code {{ display: block; padding: 10px; overflow-x: auto; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #444; padding: 8px; }}
        </style>
        </head>
        <body>
        {html}
        </body>
        </html>
        """
        self._reader.setHtml(styled_html)
        
    def _on_error(self, message: str):
        self._reader.setHtml(f"<h3 style='color:red;'>Error</h3><p>{message}</p>")
