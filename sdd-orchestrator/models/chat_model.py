"""Chat Model — Handles conversation state and persistence.

Manages chat messages, saves/loads conversations, and builds context
for the LLM using the wiki.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional
import json
from pathlib import Path


@dataclass
class ChatMessage:
    """Represents a single message in a conversation."""
    
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    sources: list[str] = field(default_factory=list)
    tool_events: list[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "sources": self.sources,
            "tool_events": self.tool_events,
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> "ChatMessage":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            sources=data.get("sources", []),
            tool_events=data.get("tool_events", []),
        )


class ChatModel:
    """Handles conversation logic and I/O."""
    
    def __init__(self):
        self._conversations_dir = None
        
    def set_workspace(self, workspace_path: str) -> None:
        """Sets the workspace path and ensures the .sdd/conversations directory exists."""
        self._conversations_dir = Path(workspace_path) / ".sdd" / "conversations"
        self._conversations_dir.mkdir(parents=True, exist_ok=True)
        
    def save_conversation(self, chat_id: str, title: str, messages: list[ChatMessage]) -> None:
        """Saves a conversation to disk as JSON."""
        if not self._conversations_dir:
            return
            
        file_path = self._conversations_dir / f"{chat_id}.json"
        
        data = {
            "id": chat_id,
            "title": title,
            "updated_at": datetime.now().isoformat(),
            "messages": [msg.to_dict() for msg in messages],
        }
        
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        
    def load_conversation(self, chat_id: str) -> tuple[str, list[ChatMessage]]:
        """Loads a conversation from disk. Returns (title, messages)."""
        if not self._conversations_dir:
            return "New Chat", []
            
        file_path = self._conversations_dir / f"{chat_id}.json"
        if not file_path.exists():
            return "New Chat", []
            
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            title = data.get("title", "Unknown")
            messages = [ChatMessage.from_dict(m) for m in data.get("messages", [])]
            return title, messages
        except Exception as e:
            print(f"Error loading conversation {chat_id}: {e}")
            return "Error", []
            
    def list_conversations(self) -> list[dict]:
        """Returns a list of all conversations in the workspace.
        
        Each dict contains: 'id', 'title', 'updated_at', 'message_count'
        """
        if not self._conversations_dir or not self._conversations_dir.exists():
            return []
            
        results = []
        for file_path in self._conversations_dir.glob("*.json"):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                results.append({
                    "id": data.get("id", file_path.stem),
                    "title": data.get("title", "New Chat"),
                    "updated_at": datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
                    "message_count": len(data.get("messages", [])),
                })
            except Exception:
                continue
                
        # Sort descending by updated_at
        results.sort(key=lambda x: x["updated_at"], reverse=True)
        return results
        
    def build_context(self, wiki_model, workspace_path: str) -> str:
        """Builds system prompt context using the wiki."""
        if not workspace_path:
            return ""

        # In the future, this will intelligently inject index.md or relevant pages
        try:
            index_content = wiki_model.read_page(workspace_path, "index.md")
            return f"Project Context:\n{index_content}\n"
        except Exception:
            return ""


# ── CLI invocation conventions (Step 3.3.2 — real subprocess dispatch) ─────
#
# Best-effort non-interactive/"print mode" argv per CLI (`cli_key` from
# CLI_REGISTRY in models/cli_discovery_model.py). Exact flags may need
# adjustment for the specific CLI version installed — CLIs not listed here
# fall back to a single positional prompt argument (`_generic_args`).
#
# "claude" is the only entry with a documented structured streaming format
# (`--output-format stream-json`), so it is the only one that gets real
# tool-call events; everything else streams as plain text.

def _generic_args(prompt: str) -> list[str]:
    return [prompt]


CLI_ARGS_BUILDERS: dict[str, Callable[[str], list[str]]] = {
    "claude": lambda prompt: ["-p", prompt, "--output-format", "stream-json", "--verbose"],
    "codex": lambda prompt: ["exec", prompt],
    "gemini": lambda prompt: ["-p", prompt],
    "agy": lambda prompt: ["-p", prompt],
    "gh-copilot": lambda prompt: ["explain", prompt],
    "aider": lambda prompt: ["--message", prompt, "--yes-always", "--no-auto-commits"],
}

CLI_STREAM_FORMAT: dict[str, str] = {
    "claude": "claude_json",
}


def build_cli_args(cli_key: str, prompt: str) -> list[str]:
    """Builds the argv (without the binary itself) to run *cli_key* non-interactively."""
    builder = CLI_ARGS_BUILDERS.get(cli_key, _generic_args)
    return builder(prompt)


def get_stream_format(cli_key: str) -> str:
    """Returns the output-parsing strategy for *cli_key*: 'claude_json' or 'plain'."""
    return CLI_STREAM_FORMAT.get(cli_key, "plain")


def parse_claude_json_line(line: str) -> Optional[Dict[str, Any]]:
    """Parses one line of Claude Code's ``--output-format stream-json``.

    Returns a normalized event ``{"kind": "text"|"tool"|"result"|"other", ...}``,
    or ``None`` if the line is blank or not valid JSON.
    """
    line = line.strip()
    if not line:
        return None
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    event_type = data.get("type")
    if event_type == "assistant":
        message = data.get("message", {})
        for block in message.get("content", []):
            if block.get("type") == "text":
                return {"kind": "text", "text": block.get("text", "")}
            if block.get("type") == "tool_use":
                return {
                    "kind": "tool",
                    "name": block.get("name", "tool"),
                    "detail": str(block.get("input", "")),
                }
    elif event_type == "result":
        return {"kind": "result", "text": data.get("result", "")}

    return {"kind": "other"}
