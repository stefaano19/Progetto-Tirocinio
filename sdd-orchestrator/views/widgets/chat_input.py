"""Chat Input Widget.

Multi-line auto-resizing input area for sending messages, with a bottom toolbar.
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ChatTextEdit(QTextEdit):
    """A QTextEdit that auto-resizes its height and handles Enter vs Shift+Enter."""

    send_requested = Signal()
    focus_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Message AI...")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.viewport().setAutoFillBackground(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.textChanged.connect(self._adjust_height)

        self._min_height = 40
        self._max_height = 150
        self.setMinimumHeight(self._min_height)
        self.setMaximumHeight(self._max_height)

    def _adjust_height(self):
        doc_height = int(self.document().size().height())
        margins = self.contentsMargins()
        # Calcolo dell'altezza necessaria
        target_height = doc_height + margins.top() + margins.bottom() + 10

        if target_height > self._max_height:
            self.setFixedHeight(self._max_height)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.setFixedHeight(max(self._min_height, target_height))
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def keyPressEvent(self, event):
        # Enter invia, Shift+Enter a capo
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.send_requested.emit()
                event.accept()
        else:
            super().keyPressEvent(event)

    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        self.focus_changed.emit(True)

    def focusOutEvent(self, event) -> None:
        super().focusOutEvent(event)
        self.focus_changed.emit(False)


class ChatInput(QWidget):
    """The main chat input field with send button and toolbar."""

    send_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("chat_input_container")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 16)

        self.frame = QFrame()
        self.frame.setObjectName("chat_input_frame")
        self.frame.setProperty("focused", False)

        # Subtle elevation, like a floating composer bar.
        shadow = QGraphicsDropShadowEffect(self.frame)
        shadow.setBlurRadius(24)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 90))
        self.frame.setGraphicsEffect(shadow)

        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(12, 12, 12, 8)
        frame_layout.setSpacing(4)

        # Text Edit
        self.text_edit = ChatTextEdit()
        self.text_edit.setObjectName("chat_input_text")
        self.text_edit.send_requested.connect(self._on_send)
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.text_edit.focus_changed.connect(self._on_focus_changed)

        frame_layout.addWidget(self.text_edit)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)

        icons_dir = Path(__file__).parent.parent.parent / "assets" / "icons"

        # Attach Button
        self.btn_attach = QPushButton()
        self.btn_attach.setObjectName("chat_attach_button")
        icon_path = icons_dir / "folder-open.svg"
        if icon_path.exists():
            self.btn_attach.setIcon(QIcon(str(icon_path)))
        else:
            self.btn_attach.setText("📁")  # Fallback se l'icona manca
        self.btn_attach.setToolTip("Attach Context")
        self.btn_attach.setFixedSize(32, 32)
        toolbar.addWidget(self.btn_attach)

        toolbar.addStretch()

        # Send Button — circular, icon-only, Claude/ChatGPT-style
        self.btn_send = QPushButton("↑")
        self.btn_send.setObjectName("chat_send_button")
        self.btn_send.setFixedSize(32, 32)
        self.btn_send.setToolTip("Send message (Enter)")
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.setEnabled(False)  # Disabilitato all'inizio
        self.btn_send.clicked.connect(self._on_send)
        toolbar.addWidget(self.btn_send)

        frame_layout.addLayout(toolbar)
        layout.addWidget(self.frame)

    def _on_text_changed(self):
        # Abilita il pulsante Invia solo se c'è testo
        has_text = bool(self.text_edit.toPlainText().strip())
        self.btn_send.setEnabled(has_text)

    def _on_focus_changed(self, focused: bool) -> None:
        self.frame.setProperty("focused", focused)
        self.frame.style().unpolish(self.frame)
        self.frame.style().polish(self.frame)

    def _on_send(self) -> None:
        text = self.text_edit.toPlainText().strip()
        if text:
            self.send_requested.emit(text)
            self.text_edit.clear()
