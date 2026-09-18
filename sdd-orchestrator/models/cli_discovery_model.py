"""CLI Discovery Model — Filesystem scanning for AI CLIs.

Searches for 8 AI CLIs in the system and verifies their
availability and version. Extends the LLM Wiki logic (which searches
only for ``claude`` and ``codex``) to 8 tools (§5.2 of claude.md).

Uses ``shell_path_resolver.find_cli_command()`` for discovery logic
with login shell PATH probe fallback — crucial on macOS where Finder apps
inherit a minimal $PATH.

ZERO PySide6 dependencies — pure Python (rule §10.1).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field

from utils.shell_path_resolver import find_cli_command


# ── Timeout for version check (same as LLM Wiki) ────────────────────
VERSION_CHECK_TIMEOUT = 3  # seconds


@dataclass
class CLIInfo:
    """Information about a single AI CLI found (or not found).

    This dataclass is the "data packet" that travels from the Model
    through the Controller up to the View — it is the only shared type
    among the three MVC layers.

    Attributes:
        key: Unique identifier of the CLI (e.g., ``"claude"``).
        binary_name: Name of the binary to search for in PATH (e.g., ``"claude"``).
        display_name: Human-readable name for the UI (e.g., ``"Claude Code"``).
        found: ``True`` if the binary was found in the system.
        path: Absolute path of the binary, or ``None`` if not found.
        version: Version string (e.g., ``"1.0.3"``), or ``None``.
        cli_type: Category for UI grouping (e.g., ``"anthropic"``).
    """

    key: str
    binary_name: str
    display_name: str
    found: bool = False
    path: str | None = None
    version: str | None = None
    cli_type: str = ""


# ── CLI Registry (§5.2 of claude.md — full table) ────────────
# Each entry defines a CLI to search for. The ``version_cmd`` field
# specifies how to obtain the version (some tools use subcommands).
# ``candidates`` are alternative names for Windows (.cmd, .exe).

CLI_REGISTRY: list[dict] = [
    {
        "key": "claude",
        "binary_name": "claude",
        "display_name": "Claude Code",
        "version_cmd": ["--version"],
        "candidates": ["claude.cmd", "claude.exe"],
        "cli_type": "anthropic",
    },
    {
        "key": "codex",
        "binary_name": "codex",
        "display_name": "OpenAI Codex",
        "version_cmd": ["--version"],
        "candidates": ["codex.cmd", "codex.exe"],
        "cli_type": "openai",
    },
    {
        "key": "gemini",
        "binary_name": "gemini",
        "display_name": "Gemini CLI",
        "version_cmd": ["--version"],
        "candidates": [],
        "cli_type": "google",
    },
    {
        "key": "agy",
        "binary_name": "agy",
        "display_name": "Antigravity",
        "version_cmd": ["--version"],
        "candidates": [],
        "cli_type": "google",
    },
    {
        "key": "aider",
        "binary_name": "aider",
        "display_name": "Aider",
        "version_cmd": ["--version"],
        "candidates": [],
        "cli_type": "opensource",
    },
    {
        "key": "gh-copilot",
        "binary_name": "copilot",
        "display_name": "GitHub Copilot",
        "version_cmd": ["--version"],
        "candidates": ["copilot.cmd", "copilot.exe"],
        "cli_type": "github",
    },
    {
        "key": "ollama",
        "binary_name": "ollama",
        "display_name": "Ollama (local)",
        # Ollama has no --version, but "ollama list" works if the
        # server is active. We use --version as a first attempt.
        "version_cmd": ["--version"],
        "candidates": [],
        "cli_type": "local",
    },
    {
        "key": "continue",
        "binary_name": "continue",
        "display_name": "Continue.dev",
        # Continue is an IDE extension, it might not have a CLI binary.
        # The scan looks for it anyway for completeness.
        "version_cmd": [],
        "candidates": [],
        "cli_type": "ide",
    },
]


class CLIDiscoveryModel:
    """Filesystem scanning for AI CLIs.

    No PySide6 dependency. Uses ``find_cli_command()`` from
    ``shell_path_resolver`` for discovery logic with fallback
    login shell PATH probe.

    Main methods:
      - ``scan_all()``: scans all 8 CLIs in the registry
      - ``scan_single(key)``: scans a single CLI
      - ``get_version(path, args)``: performs version check

    The design is stateless: each call returns an independent
    result, with no internal cache (the cache is in the resolver).
    """

    @property
    def registry(self) -> list[dict]:
        """Returns the CLI registry (useful for the Worker which needs to iterate)."""
        return CLI_REGISTRY

    def scan_all(self) -> list[CLIInfo]:
        """Scans all CLIs in the registry.

        Iterates over each entry in ``CLI_REGISTRY``, searches for the binary
        in the system, and verifies the version if found.

        Returns:
            List of ``CLIInfo``, one for each CLI — ``found=True`` if
            the binary was located in PATH.

        Note:
            This operation can take several seconds (up to 10s
            for the login shell probe + 3s for each version check).
            For this reason it must ALWAYS be executed in a QThread,
            NEVER on the main thread (rule §10.3).
        """
        results: list[CLIInfo] = []
        for cli_def in CLI_REGISTRY:
            info = self.scan_single(cli_def["key"])
            results.append(info)
        return results

    def scan_single(self, key: str) -> CLIInfo:
        """Scans a single CLI by key.

        Pipeline (identical to LLM Wiki):
          1. Look for definition in registry
          2. Call ``find_cli_command()`` with Windows candidates
          3. If found, execute version check with 3s timeout

        Args:
            key: The CLI key in the registry (e.g., ``"claude"``).

        Returns:
            ``CLIInfo`` with ``found=True/False`` and details.
        """
        # Find definition in registry
        cli_def = None
        for entry in CLI_REGISTRY:
            if entry["key"] == key:
                cli_def = entry
                break

        if cli_def is None:
            return CLIInfo(key=key, binary_name=key, display_name=key)

        # Search for binary in the system (with login shell fallback)
        candidates = cli_def.get("candidates", [])
        path = find_cli_command(
            cli_def["binary_name"],
            candidates=candidates if candidates else None,
        )

        if path is None:
            # CLI not found
            return CLIInfo(
                key=cli_def["key"],
                binary_name=cli_def["binary_name"],
                display_name=cli_def["display_name"],
                found=False,
                cli_type=cli_def["cli_type"],
            )

        # CLI found — check version
        version = None
        version_cmd = cli_def.get("version_cmd", [])
        if version_cmd:
            version = self.get_version(path, version_cmd)

        return CLIInfo(
            key=cli_def["key"],
            binary_name=cli_def["binary_name"],
            display_name=cli_def["display_name"],
            found=True,
            path=path,
            version=version,
            cli_type=cli_def["cli_type"],
        )

    @staticmethod
    def get_version(
        binary_path: str,
        version_args: list[str],
        timeout: int = VERSION_CHECK_TIMEOUT,
    ) -> str | None:
        """Executes version check on a found binary.

        Like LLM Wiki ``claude_cli_detect`` / ``codex_cli_detect``:
        launches the binary with version arguments and parses the output.

        Args:
            binary_path: Absolute path to the binary (e.g., ``"/usr/local/bin/claude"``).
            version_args: Arguments to get version (e.g., ``["--version"]``).
            timeout: Timeout in seconds (default 3s like LLM Wiki).

        Returns:
            Extracted version string (first non-empty line of output),
            or ``None`` if the check fails.
        """
        # Prevents black terminal window flash on Windows (GUI apps)
        kwargs = {}
        import os
        if os.name == 'nt':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

        try:
            result = subprocess.run(
                [binary_path] + version_args,
                capture_output=True,
                text=True,
                timeout=timeout,
                **kwargs
            )

            # Get the first non-empty line of output
            # (some CLIs print version on stdout, others on stderr)
            output = result.stdout.strip() or result.stderr.strip()
            if output:
                # Return only the first line (avoid multiline output)
                return output.splitlines()[0].strip()

        except subprocess.TimeoutExpired:
            # Binary exists but is slow to respond
            pass
        except OSError:
            # Execution error
            pass

        return None
