"""Chat Input Widget.

Multi-line input area for sending messages, with a bottom toolbar.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QFrame,
)
from PySide6.QtGui import QIcon
from pathlib import Path


class ChatInput(QWidget):
    """The main chat input field with send button and toolbar."""
    
    send_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("chat_input_container")
        self.setMaximumHeight(160)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 16)
        
        self.frame = QFrame()
        self.frame.setObjectName("chat_input_frame")

        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(12, 12, 12, 8)
        frame_layout.setSpacing(8)
        
        # Text Edit
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("chat_input_text")
        self.text_edit.setPlaceholderText("Message AI...")
        self.text_edit.setFrameShape(QFrame.Shape.NoFrame)
        self.text_edit.viewport().setAutoFillBackground(False)
        self.text_edit.setMaximumHeight(100)
        
        frame_layout.addWidget(self.text_edit)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        
        icons_dir = Path(__file__).parent.parent.parent / "assets" / "icons"
        
        # Attach Button
        self.btn_attach = QPushButton()
        self.btn_attach.setObjectName("chat_attach_button")
        self.btn_attach.setIcon(QIcon(str(icons_dir / "folder-open.svg")))
        self.btn_attach.setToolTip("Attach Context")
        self.btn_attach.setFixedSize(32, 32)
        toolbar.addWidget(self.btn_attach)
        
        toolbar.addStretch()
        
        # Send Button
        self.btn_send = QPushButton("Send")
        self.btn_send.setObjectName("primary_button")
        self.btn_send.setFixedHeight(32)
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.clicked.connect(self._on_send)
        toolbar.addWidget(self.btn_send)
        
        frame_layout.addLayout(toolbar)
        layout.addWidget(self.frame)
        
    def _on_send(self) -> None:
        text = self.text_edit.toPlainText().strip()
        if text:
            self.send_requested.emit(text)
            self.text_edit.clear()
