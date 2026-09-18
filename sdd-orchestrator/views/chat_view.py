"""Chat View.

Assembles the ConversationSidebar, Chat message list, and ChatInput.
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QScrollArea,
    QFrame,
    QLabel,
)

from views.widgets.conversation_sidebar import ConversationSidebar
from views.widgets.chat_input import ChatInput
from views.widgets.chat_bubble import ChatBubble
from views.widgets.tool_stage_widget import ToolStageWidget


class ChatView(QWidget):
    """Main view for the chat interface."""
    
    # Signals to pass to the controller
    send_requested = Signal(str)
    new_chat_requested = Signal()
    conversation_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("chat_view")
        
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Left Sidebar
        self.sidebar = ConversationSidebar()
        self.sidebar.new_chat_requested.connect(self.new_chat_requested)
        self.sidebar.conversation_selected.connect(self.conversation_selected)
        layout.addWidget(self.sidebar)
        
        # Separator
        sep = QFrame()
        sep.setObjectName("chat_sidebar_separator")
        sep.setFrameShape(QFrame.Shape.VLine)
        layout.addWidget(sep)
        
        # 2. Main Chat Area
        chat_area = QWidget()
        chat_layout = QVBoxLayout(chat_area)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Scrollable messages area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        # QScrollArea is already transparent by default (styles/*.qss)
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(16)
        self.messages_layout.setContentsMargins(24, 24, 24, 24)
        
        # Placeholder / Empty state
        self.empty_label = QLabel("How can I help you today?")
        self.empty_label.setObjectName("welcome_title")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.messages_layout.addWidget(self.empty_label)
        
        self.scroll_area.setWidget(self.messages_container)
        chat_layout.addWidget(self.scroll_area, stretch=1)
        
        # Input area
        self.chat_input = ChatInput()
        self.chat_input.send_requested.connect(self.send_requested)
        chat_layout.addWidget(self.chat_input)
        
        layout.addWidget(chat_area, stretch=1)
        
        # 3. Context Panel (Right, optional, can be hidden)
        self.context_panel = QFrame()
        self.context_panel.setObjectName("chat_context_panel")
        self.context_panel.setFixedWidth(300)
        context_layout = QVBoxLayout(self.context_panel)
        context_title = QLabel("Context")
        context_title.setObjectName("section_subtitle")
        context_layout.addWidget(context_title)
        context_layout.addStretch()
        
        # Initially hidden to save space, will be populated by skills later
        self.context_panel.hide()
        
        layout.addWidget(self.context_panel)
        
    def add_message(self, role: str, content: str) -> ChatBubble:
        """Adds a message bubble to the chat."""
        self.empty_label.hide()
        bubble = ChatBubble(role, content)
        self.messages_layout.addWidget(bubble)
        self._scroll_to_bottom()
        return bubble
        
    def add_tool_stage(self, name: str, detail: str) -> ToolStageWidget:
        """Adds a tool stage widget to the chat."""
        self.empty_label.hide()
        stage = ToolStageWidget(name, detail)
        # Add it with left/right padding to look like it's part of the assistant's response
        wrap = QHBoxLayout()
        wrap.setContentsMargins(16, 0, 16, 0)
        wrap.addWidget(stage)
        wrap.addStretch()
        
        wrap_widget = QWidget()
        wrap_widget.setLayout(wrap)
        self.messages_layout.addWidget(wrap_widget)
        self._scroll_to_bottom()
        return stage
        
    def clear_messages(self) -> None:
        """Clears all messages from the chat area."""
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                if widget is not self.empty_label:
                    widget.deleteLater()
            elif item.layout():
                # For tool stages wrapped in QHBoxLayout
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
        self.empty_label.show()
        self.messages_layout.addWidget(self.empty_label)
        
    def populate_sidebar(self, conversations: list[dict]) -> None:
        """Updates the conversation history in the sidebar."""
        self.sidebar.populate(conversations)

    def _scroll_to_bottom(self) -> None:
        """Automatically scrolls to the latest message."""
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
