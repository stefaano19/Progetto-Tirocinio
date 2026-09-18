"""Tool Stage Widget.

A collapsible accordion to show LLM agent actions (tool calls, chain of thought).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)
from PySide6.QtGui import QIcon
from pathlib import Path


class ToolStageWidget(QWidget):
    """Displays a single tool call or agent thought process."""
    
    def __init__(self, stage_name: str, detail: str, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 4, 0, 4)
        
        # Header (clickable to expand/collapse)
        self.header = QFrame()
        self.header.setObjectName("tool_stage_header")
        self.header.setProperty("expanded", False)
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.mousePressEvent = self._toggle
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        icons_dir = Path(__file__).parent.parent.parent / "assets" / "icons"
        
        self.icon_label = QLabel()
        self.icon_label.setPixmap(QIcon(str(icons_dir / "settings.svg")).pixmap(16, 16))
        header_layout.addWidget(self.icon_label)
        
        self.title_label = QLabel(stage_name)
        self.title_label.setObjectName("tool_stage_title")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        self.chevron = QLabel()
        self.chevron.setPixmap(QIcon(str(icons_dir / "chevron-right.svg")).pixmap(14, 14))
        header_layout.addWidget(self.chevron)
        
        self.layout.addWidget(self.header)
        
        # Details (initially hidden)
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("tool_stage_detail_frame")
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(12, 8, 12, 8)

        self.detail_label = QLabel(detail)
        self.detail_label.setObjectName("tool_stage_detail_label")
        self.detail_label.setWordWrap(True)
        detail_layout.addWidget(self.detail_label)
        
        self.detail_frame.hide()
        self.layout.addWidget(self.detail_frame)
        self.layout.setSpacing(0)
        
        self._expanded = False
        
    def _toggle(self, event=None) -> None:
        self._expanded = not self._expanded
        self.detail_frame.setVisible(self._expanded)

        icons_dir = Path(__file__).parent.parent.parent / "assets" / "icons"
        icon_name = "chevron-down.svg" if self._expanded else "chevron-right.svg"
        self.chevron.setPixmap(QIcon(str(icons_dir / icon_name)).pixmap(14, 14))

        # Drives the QSS variant selector (QFrame#tool_stage_header[expanded=...])
        self.header.setProperty("expanded", self._expanded)
        self.header.style().unpolish(self.header)
        self.header.style().polish(self.header)
