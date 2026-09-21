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
    QSizePolicy,
    QSpacerItem
)

from views.widgets.conversation_sidebar import ConversationSidebar
from views.widgets.chat_input import ChatInput
from views.widgets.chat_bubble import ChatBubble
from views.widgets.tool_stage_widget import ToolStageWidget


class ChatView(QWidget):
    """Main view for the chat interface."""
    
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
        
        # 2. Main Chat Area with centered max-width container
        chat_area = QWidget()
        chat_area_layout = QHBoxLayout(chat_area)
        chat_area_layout.setContentsMargins(0, 0, 0, 0)
        chat_area_layout.setSpacing(0)
        
        # Spacer sinistro
        chat_area_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Contenitore centrale (max width 800)
        chat_center = QWidget()
        chat_center.setMaximumWidth(800)
        chat_center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        chat_layout = QVBoxLayout(chat_center)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Scrollable messages area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
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

        # Auto-follow the bottom as content grows (e.g. a streaming
        # response). Calling scroll_to_bottom() right after resizing a
        # bubble reads the scrollbar's maximum before Qt's layout pass has
        # recomputed it, so it scrolls to a stale (too-small) value and the
        # newest lines end up rendered below the viewport — visually
        # "hidden" under the composer bar. rangeChanged only fires once the
        # range is actually up to date, so following it here always lands
        # on the true bottom.
        self.scroll_area.verticalScrollBar().rangeChanged.connect(
            lambda _min, max_val: self.scroll_area.verticalScrollBar().setValue(max_val)
        )
        
        # Input area ancorata in basso
        self.chat_input = ChatInput()
        self.chat_input.send_requested.connect(self.send_requested)
        chat_layout.addWidget(self.chat_input)
        
        chat_area_layout.addWidget(chat_center, stretch=1)
        
        # Spacer destro
        chat_area_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        layout.addWidget(chat_area, stretch=1)
        
        # 3. Context Panel (Right, optional)
        self.context_panel = QFrame()
        self.context_panel.setObjectName("chat_context_panel")
        self.context_panel.setFixedWidth(300)
        context_layout = QVBoxLayout(self.context_panel)
        context_title = QLabel("Context")
        context_title.setObjectName("section_subtitle")
        context_layout.addWidget(context_title)
        context_layout.addStretch()
        
        self.context_panel.hide()
        layout.addWidget(self.context_panel)
        
    def add_message(self, role: str, content: str) -> ChatBubble:
        """Adds a message bubble to the chat."""
        self.empty_label.hide()
        bubble = ChatBubble(role, content)
        self.messages_layout.addWidget(bubble)
        self.scroll_to_bottom()
        return bubble
        
    def add_tool_stage(self, name: str, detail: str) -> ToolStageWidget:
        """Adds a tool stage widget to the chat."""
        self.empty_label.hide()
        stage = ToolStageWidget(name, detail)
        
        wrap = QHBoxLayout()
        wrap.setContentsMargins(20, 0, 16, 0)
        
        # Placeholder invisibile per allineare allo spazio dell'avatar dell'IA (28px) + margini
        avatar_spacer = QWidget()
        avatar_spacer.setFixedSize(28, 28)
        wrap.addWidget(avatar_spacer)
        
        wrap.addWidget(stage)
        wrap.addStretch()
        
        wrap_widget = QWidget()
        wrap_widget.setLayout(wrap)
        self.messages_layout.addWidget(wrap_widget)
        self.scroll_to_bottom()
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
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
        self.empty_label.show()
        self.messages_layout.addWidget(self.empty_label)
        
    def populate_sidebar(self, conversations: list[dict]) -> None:
        """Updates the conversation history in the sidebar."""
        self.sidebar.populate(conversations)

    def scroll_to_bottom(self) -> None:
        """Automatically scrolls to the latest message.

        Public so callers driving a bubble's content directly (e.g. token
        streaming, which bypasses add_message()) can keep the view pinned
        to the bottom as the message grows.
        """
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
