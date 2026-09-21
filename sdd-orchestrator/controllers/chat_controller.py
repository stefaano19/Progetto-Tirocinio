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

        # Auto-generated title (Step 3.4): fires once per conversation, right
        # after the first exchange, replacing the truncated first-message
        # fallback below with a short AI-written summary of the chat.
        self._title_generated = False
        self._pending_user_text = ""
        self._title_worker = None

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
        self._title_generated = False
        self.conversation_loaded.emit(self._current_messages)

    def load_chat(self, chat_id: str) -> None:
        """Loads an existing conversation from disk."""
        title, messages = self._model.load_conversation(chat_id)
        self._current_chat_id = chat_id
        self._current_messages = messages
        self._current_title = title
        # A saved chat already has *some* title (even the old truncated
        # fallback) — don't fire a background title generation for it.
        self._title_generated = title != "New Chat"
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
        self._pending_user_text = text

        # 2. Temporary placeholder title, shown until the AI-generated
        # description (see _generate_title) replaces it after this
        # exchange completes.
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

        if not self._title_generated and len(self._current_messages) == 2:
            self._generate_title(self._pending_user_text, full_text)

    def _generate_title(self, user_text: str, assistant_text: str) -> None:
        """Fires a one-off, non-streamed CLI call to write a short chat title.

        Runs once per conversation, right after the first exchange, and
        replaces the truncated first-message placeholder set in
        ``send_message()`` with a real summary (à la ChatGPT/Claude chat
        titles). Reuses ``ChatWorker`` as a plain background subprocess
        runner — its output is routed to ``_on_title_generated`` instead of
        the message stream, so it never touches the visible conversation.
        """
        if not self._active_binary_path or not self._active_cli_key:
            return

        self._title_generated = True  # don't retry even if this call fails

        # Snapshot the target chat_id/messages: the user may switch to a
        # different conversation before this one-off CLI call returns, and
        # the result must land on the conversation it was generated for —
        # never overwrite whatever is "current" by the time it completes.
        target_chat_id = self._current_chat_id
        target_messages = list(self._current_messages)

        prompt = (
            "Summarize the following chat exchange in a short title of 3 to "
            "6 words. Respond with ONLY the title text: no quotes, no "
            "trailing punctuation, no explanation.\n\n"
            f"User: {user_text}\n"
            f"Assistant: {assistant_text[:500]}"
        )

        self._title_worker = ChatWorker(
            cli_key=self._active_cli_key,
            binary_path=self._active_binary_path,
            prompt=prompt,
            workspace_path=self._workspace_path,
            context="",
        )
        self._title_worker.response_complete.connect(
            lambda raw_title: self._on_title_generated(raw_title, target_chat_id, target_messages)
        )
        self._title_worker.response_error.connect(self._on_title_error)
        self._title_worker.start()

    def _on_title_generated(self, raw_title: str, chat_id: str, messages_snapshot: list) -> None:
        """Applies the AI-generated title once the one-off CLI call returns."""
        self._title_worker = None
        cleaned = raw_title.strip().splitlines()[0].strip() if raw_title.strip() else ""
        title = cleaned.strip('"').strip("'").rstrip(".")[:60]
        if not title:
            return

        if chat_id == self._current_chat_id:
            # Still the active conversation — go through the normal path so
            # we persist the live message list (it may have grown since).
            self._current_title = title
            self._save_state()
        else:
            # User navigated away while the CLI call was in flight —
            # persist directly against the snapshot taken at request time.
            self._model.save_conversation(chat_id, title, messages_snapshot)
            self._refresh_history()

    def _on_title_error(self, _message: str) -> None:
        """Keeps the truncated placeholder title if generation fails."""
        self._title_worker = None

    def _save_state(self) -> None:
        """Persists the current chat and updates the sidebar."""
        if self._current_chat_id:
            self._model.save_conversation(self._current_chat_id, self._current_title, self._current_messages)
            self._refresh_history()

    def shutdown(self) -> None:
        """Cancels and waits for any in-flight CLI subprocess before the app closes.

        A chat response (or the background title-generation call) can run
        for an arbitrarily long time, so closing the window would let Qt
        destroy a still-running ``QThread`` and abort the process. Called
        from ``app.aboutToQuit`` in ``main.py``.
        """
        for worker in (self._worker, self._title_worker):
            if worker is not None and worker.isRunning():
                worker.cancel()
                worker.wait()
