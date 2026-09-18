"""Codebase View.

QSplitter with a filesystem tree on the left and a report panel (stat
widgets + rendered Markdown report) on the right (§5.8 of claude.md).
"""

import markdown
from PySide6.QtCore import QDir, Qt
from PySide6.QtWidgets import (
    QFileSystemModel,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from controllers.codebase_controller import CodebaseController


class CodebaseView(QWidget):
    """Main view for local codebase analysis."""

    def __init__(self, controller: CodebaseController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("codebase_view")
        self._controller = controller
        self._workspace_path: str | None = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Toolbar ──────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setObjectName("codebase_toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel("Codebase Analysis")
        title.setObjectName("h2")
        toolbar_layout.addWidget(title)
        toolbar_layout.addStretch()

        self.btn_analyze = QPushButton("Analyze")
        self.btn_analyze.setObjectName("primary_button")
        toolbar_layout.addWidget(self.btn_analyze)

        layout.addWidget(toolbar)

        # ── Splitter: file tree | report panel ──────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("codebase_splitter")

        self._file_model = QFileSystemModel()
        self._file_model.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllEntries)

        self._file_tree = QTreeView()
        self._file_tree.setObjectName("codebase_file_tree")
        self._file_tree.setModel(self._file_model)
        self._file_tree.setHeaderHidden(True)
        splitter.addWidget(self._file_tree)

        report_panel = QWidget()
        report_layout = QVBoxLayout(report_panel)
        report_layout.setContentsMargins(16, 16, 16, 16)
        report_layout.setSpacing(16)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(24)
        self._stat_files = self._create_stat_widget("Files", "0")
        self._stat_dirs = self._create_stat_widget("Directories", "0")
        self._stat_lines = self._create_stat_widget("Lines of code", "0")
        for stat in (self._stat_files, self._stat_dirs, self._stat_lines):
            stats_row.addWidget(stat)
        stats_row.addStretch()
        report_layout.addLayout(stats_row)

        self._report_browser = QTextBrowser()
        self._report_browser.setObjectName("codebase_report")
        self._report_browser.setOpenExternalLinks(True)
        report_layout.addWidget(self._report_browser, stretch=1)

        splitter.addWidget(report_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter, stretch=1)

    def _create_stat_widget(self, label: str, value: str) -> QWidget:
        """Mini-stat widget (value + label), same pattern as WorkspaceView."""
        w = QWidget()
        w_layout = QVBoxLayout(w)
        w_layout.setContentsMargins(0, 0, 0, 0)
        w_layout.setSpacing(2)

        val = QLabel(value)
        val.setObjectName("stat_value")
        w_layout.addWidget(val)

        lbl = QLabel(label)
        lbl.setObjectName("section_subtitle")
        w_layout.addWidget(lbl)

        return w

    @staticmethod
    def _update_stat(widget: QWidget, value: str) -> None:
        val_label = widget.findChild(QLabel, "stat_value")
        if val_label:
            val_label.setText(value)

    def _connect_signals(self) -> None:
        self.btn_analyze.clicked.connect(lambda: self._controller.analyze())
        self._controller.analysis_started.connect(self._on_analysis_started)
        self._controller.analysis_complete.connect(self._on_analysis_complete)
        self._controller.analysis_error.connect(self._on_analysis_error)

    def set_workspace_root(self, path: str) -> None:
        """Called from the wiring layer when the workspace changes."""
        self._workspace_path = path
        self._controller.set_workspace(path)

        self._file_model.setRootPath(path)
        self._file_tree.setRootIndex(self._file_model.index(path))
        for i in range(1, self._file_model.columnCount()):
            self._file_tree.hideColumn(i)

    def _on_analysis_started(self) -> None:
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.setText("Analyzing...")

    def _on_analysis_complete(self, stats: dict, report: str) -> None:
        self.btn_analyze.setEnabled(True)
        self.btn_analyze.setText("Analyze")

        self._update_stat(self._stat_files, str(stats.get("total_files", 0)))
        self._update_stat(self._stat_dirs, str(stats.get("total_dirs", 0)))
        self._update_stat(self._stat_lines, str(stats.get("total_lines", 0)))

        html = markdown.markdown(report, extensions=["fenced_code", "tables"])
        styled_html = f"""
        <html>
        <head>
        <style>
            body {{ font-family: -apple-system, system-ui, sans-serif; line-height: 1.6; color: #dddddd; padding: 20px; }}
            h1, h2, h3 {{ color: #ffffff; border-bottom: 1px solid #444; padding-bottom: 5px; }}
            code {{ background-color: #2b2d31; padding: 2px 4px; border-radius: 4px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #444; padding: 8px; }}
        </style>
        </head>
        <body>
        {html}
        </body>
        </html>
        """
        self._report_browser.setHtml(styled_html)

    def _on_analysis_error(self, message: str) -> None:
        self.btn_analyze.setEnabled(True)
        self.btn_analyze.setText("Analyze")
        self._report_browser.setHtml(f"<h3 style='color:red;'>Error</h3><p>{message}</p>")
