"""Conversation Sidebar Widget.

Lists recent chat conversations, allows creating new ones.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFrame,
)


class ConversationSidebar(QWidget):
    """Sidebar for managing chat history."""
    
    conversation_selected = Signal(str)
    new_chat_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self.setObjectName("conversation_sidebar")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(16)
        
        # New Chat Button
        self.btn_new = QPushButton("＋ New Chat")
        self.btn_new.setObjectName("primary_button")
        self.btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new.clicked.connect(self.new_chat_requested.emit)
        layout.addWidget(self.btn_new)
        
        # Section Title
        lbl = QLabel("Recent Chats")
        lbl.setObjectName("section_subtitle")
        layout.addWidget(lbl)
        
        # List
        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget.viewport().setAutoFillBackground(False)
        self.list_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        
        layout.addWidget(self.list_widget)
        
    def populate(self, conversations: list[dict]) -> None:
        """Populate the list with conversation dictionaries."""
        self.list_widget.clear()
        
        for conv in conversations:
            item = QListWidgetItem(f"💬 {conv.get('title', 'Unknown')}")
            item.setData(Qt.ItemDataRole.UserRole, conv["id"])
            item.setToolTip(f"Messages: {conv.get('message_count', 0)}")
            self.list_widget.addItem(item)
            
    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        if chat_id:
            self.conversation_selected.emit(chat_id)
