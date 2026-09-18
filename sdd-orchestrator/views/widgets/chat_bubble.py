"""Chat Bubble Widget.

Displays a single chat message (user or assistant) with markdown support.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextBrowser,
    QFrame,
)


class _AutoHeightTextBrowser(QTextBrowser):
    """QTextBrowser that tracks its wrapped-content height as it is resized.

    A plain ``document().adjustSize()`` call right after construction (before
    the widget has ever been laid out) sizes the document to its unwrapped
    "ideal" width, not the width it will actually render at once placed in
    the bubble layout — the height computed from that is wrong, and the
    text ends up clipped. Recomputing on every ``resizeEvent`` (which fires
    once real geometry is assigned) uses the real, wrapped width instead.
    """

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.update_height()

    def update_height(self) -> None:
        self.document().setTextWidth(self.viewport().width())
        height = int(self.document().size().height())
        self.setFixedHeight(max(height + 10, 20))


class ChatBubble(QWidget):
    """A bubble displaying a chat message.
    
    If role == 'user', aligns to the right with accent color.
    If role == 'assistant', aligns to the left with muted color.
    """
    
    def __init__(self, role: str, content: str, parent=None):
        super().__init__(parent)
        self.role = role
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 8, 16, 8)
        
        self.bubble = QFrame()
        self.bubble.setObjectName("chat_bubble")
        # Role drives the QSS variant selector (QFrame#chat_bubble[bubble_role=...])
        self.bubble.setProperty("bubble_role", role)

        bubble_layout = QVBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(16, 12, 16, 12)

        # Markdown display
        self.text_browser = _AutoHeightTextBrowser()
        self.text_browser.setObjectName("chat_bubble_text")
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setFrameShape(QFrame.Shape.NoFrame)
        self.text_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_browser.viewport().setAutoFillBackground(False)
        self.text_browser.setMarkdown(content)

        bubble_layout.addWidget(self.text_browser)
        
        # Alignment & Colors
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        if role == "user":
            main_layout.addStretch()
            main_layout.addWidget(self.bubble)
            self.bubble.setMaximumWidth(700)
        else:
            # Avatar
            avatar_label = QLabel()
            avatar_label.setFixedSize(28, 28)
            avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar_label.setObjectName("chat_avatar_assistant")
            avatar_label.setText("✦")
            
            # Keep avatar aligned to top
            avatar_layout = QVBoxLayout()
            avatar_layout.setContentsMargins(0, 10, 0, 0)
            avatar_layout.addWidget(avatar_label)
            avatar_layout.addStretch()
            
            # Ridurre i margini della bolla dell'assistente dato che non ha più sfondo
            bubble_layout.setContentsMargins(4, 4, 16, 12)
            
            main_layout.addLayout(avatar_layout)
            main_layout.addWidget(self.bubble)
            main_layout.addStretch()
            self.bubble.setMaximumWidth(800)
            
    def update_content(self, new_content: str) -> None:
        """Update markdown content (useful for streaming)."""
        self.text_browser.setMarkdown(new_content)
        # setMarkdown() doesn't trigger resizeEvent (geometry is unchanged) —
        # recompute the height explicitly for the new content.
        self.text_browser.update_height()
