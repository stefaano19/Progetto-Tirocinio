"""Chat Worker.

Runs the active AI CLI as a subprocess and streams its output back to the UI.

Extends ``BaseWorker`` (§10.1 / Step 1.3.1) instead of ``QThread`` directly,
so exceptions raised in ``do_work()`` are caught automatically and relayed
as ``response_error`` (aliased from ``BaseWorker.error``).

Command construction and output parsing are pure logic and live in
``models/chat_model.py`` (``build_cli_args``, ``get_stream_format``,
``parse_claude_json_line``) — this worker only does I/O and signal emission.
"""

from PySide6.QtCore import Signal
import subprocess

from models.chat_model import build_cli_args, get_stream_format, parse_claude_json_line
from workers.base_worker import BaseWorker


class ChatWorker(BaseWorker):
    """Runs a background task to fetch a response from an AI CLI."""

    # Emits the accumulated response text as it streams in
    token_received = Signal(str)

    # Emits when the agent uses a tool (name, detail)
    tool_stage = Signal(str, str)

    # Emits when the response is fully generated
    response_complete = Signal(str)

    # Emitted on error — alias of BaseWorker.error for API compatibility
    # with ChatController, which was written against this signal name.
    response_error = Signal(str)

    def __init__(
        self,
        cli_key: str,
        binary_path: str,
        prompt: str,
        workspace_path: str,
        context: str,
    ) -> None:
        super().__init__()
        self.cli_key = cli_key
        self.binary_path = binary_path
        self.prompt = prompt
        self.workspace_path = workspace_path
        self.context = context
        self._is_cancelled = False
        self._process: subprocess.Popen | None = None

        self.error.connect(self.response_error.emit)

    def cancel(self) -> None:
        """Requests cancellation and terminates the subprocess if running."""
        self._is_cancelled = True
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()

    def do_work(self) -> None:
        """Spawns the CLI and streams its stdout into the UI.

        Any exception here (missing binary, non-zero exit with no output, ...)
        propagates to ``BaseWorker.run()``, which emits ``error`` — relayed
        to ``response_error`` above.
        """
        full_prompt = f"{self.context}\n\n{self.prompt}" if self.context else self.prompt
        args = build_cli_args(self.cli_key, full_prompt)
        cmd = [self.binary_path, *args]

        process = subprocess.Popen(
            cmd,
            cwd=self.workspace_path or None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._process = process

        stream_format = get_stream_format(self.cli_key)
        accumulated_text = ""

        for line in process.stdout:
            if self._is_cancelled:
                process.terminate()
                return

            if stream_format == "claude_json":
                event = parse_claude_json_line(line)
                if not event:
                    continue
                if event["kind"] == "text":
                    accumulated_text += event["text"]
                    self.token_received.emit(accumulated_text)
                elif event["kind"] == "tool":
                    self.tool_stage.emit(event["name"], event["detail"])
                elif event["kind"] == "result" and event.get("text"):
                    accumulated_text = event["text"]
            else:
                accumulated_text += line
                self.token_received.emit(accumulated_text)

        process.wait()

        if self._is_cancelled:
            return

        if process.returncode != 0 and not accumulated_text.strip():
            stderr_output = process.stderr.read() if process.stderr else ""
            raise RuntimeError(
                stderr_output.strip() or f"'{self.cli_key}' exited with code {process.returncode}"
            )

        self.response_complete.emit(accumulated_text)
