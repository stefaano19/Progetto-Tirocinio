"""Chat Controller.

Mediates between the ChatView, ChatModel, and the background ChatWorker.
"""

from PySide6.QtCore import QObject, Signal
import uuid

from models.chat_model import ChatModel, ChatMessage
from workers.chat_worker import ChatWorker


class ChatController(QObject):
    """Orchestrates chat logic and state."""
    
    # Signals emitted to the view
    conversation_loaded = Signal(list)  # list of ChatMessage
    history_updated = Signal(list)      # list of dicts (recent chats)
    
    # Streaming signals
    stream_token = Signal(str)
    tool_executed = Signal(str, str)
    stream_finished = Signal()
    stream_error = Signal(str)
    
    def __init__(self, model: ChatModel, parent=None):
        super().__init__(parent)
        self._model = model
        self._current_chat_id = None
        self._current_messages = []
        self._current_title = "New Chat"
        self._workspace_path = None
        self._worker = None
        self._wiki_model = None
        self._active_cli_key: str | None = None
        self._active_binary_path: str | None = None

    def set_workspace(self, path: str) -> None:
        """Sets the active workspace and loads history."""
        self._workspace_path = path
        self._model.set_workspace(path)
        self._refresh_history()
        self.start_new_chat()

    def set_wiki_model(self, wiki_model) -> None:
        """Injects the WikiModel used to build chat context from the knowledge base."""
        self._wiki_model = wiki_model

    def set_active_cli(self, cli_key: str, binary_path: str) -> None:
        """Sets the AI CLI to invoke for the next messages.

        Called from the wiring layer (main.py) whenever the active agent
        changes — either automatically after a CLI scan or manually from
        SettingsView (§10.1: the controller never resolves this itself
        from widget state).
        """
        self._active_cli_key = cli_key
        self._active_binary_path = binary_path or None
        
    def _refresh_history(self) -> None:
        """Reloads the sidebar list."""
        history = self._model.list_conversations()
        self.history_updated.emit(history)
        
    def start_new_chat(self) -> None:
        """Initializes a blank conversation."""
        self._current_chat_id = str(uuid.uuid4())
        self._current_messages = []
        self._current_title = "New Chat"
        self.conversation_loaded.emit(self._current_messages)
        
    def load_chat(self, chat_id: str) -> None:
        """Loads an existing conversation from disk."""
        title, messages = self._model.load_conversation(chat_id)
        self._current_chat_id = chat_id
        self._current_messages = messages
        self._current_title = title
        self.conversation_loaded.emit(self._current_messages)
        
    def send_message(self, text: str) -> None:
        """Handles the user sending a new message."""
        if not text.strip():
            return

        if not self._active_binary_path or not self._active_cli_key:
            self.stream_error.emit(
                "No AI CLI selected or available. Check the CLI Status view."
            )
            return

        # 1. Add user message
        user_msg = ChatMessage(role="user", content=text)
        self._current_messages.append(user_msg)

        # 2. Update title if this is the first message
        if self._current_title == "New Chat":
            self._current_title = text[:30] + ("..." if len(text) > 30 else "")

        # 3. Save state
        self._save_state()

        # 4. Start assistant response worker
        context = self._model.build_context(self._wiki_model, self._workspace_path)

        self._worker = ChatWorker(
            cli_key=self._active_cli_key,
            binary_path=self._active_binary_path,
            prompt=text,
            workspace_path=self._workspace_path,
            context=context
        )

        self._worker.token_received.connect(self.stream_token)
        self._worker.tool_stage.connect(self.tool_executed)
        self._worker.response_complete.connect(self._on_worker_complete)
        self._worker.response_error.connect(self.stream_error)

        self._worker.start()
        
    def _on_worker_complete(self, full_text: str) -> None:
        """Handles the end of the AI response."""
        assistant_msg = ChatMessage(role="assistant", content=full_text)
        self._current_messages.append(assistant_msg)
        self._save_state()
        self.stream_finished.emit()
        self._worker = None
        
    def _save_state(self) -> None:
        """Persists the current chat and updates the sidebar."""
        if self._current_chat_id:
            self._model.save_conversation(self._current_chat_id, self._current_title, self._current_messages)
            self._refresh_history()
