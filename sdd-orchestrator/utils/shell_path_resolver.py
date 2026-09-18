"""Shell Path Resolver — Login shell PATH probe for macOS.

Resolves a critical issue: desktop apps launched from Finder/Dock on macOS
inherit a minimal ``$PATH`` (only ``/usr/bin:/bin``) that DOES NOT include tools
installed via Homebrew, nvm, asdf, fnm, etc.

Inspired by ``cli_resolver.rs`` from LLM Wiki (§3.5 / §5.2 of claude.md).

Resolution pipeline:
  1. ``shutil.which(command)`` with the app's current $PATH
  2. If it fails → interactive login shell probe to get
     the user's full PATH (the one they would have in a terminal)
  3. Search for the command in the obtained full PATH

The probe works as follows:
  - Reads the user's ``$SHELL`` (e.g. ``/bin/zsh``)
  - For minimal shells (sh, dash): ``-ic`` flag
  - For full shells (zsh, bash, fish): ``-ilc`` flag (interactive + login)
  - Executes: ``printf '\\x1ePATH=%s\\x1e\\n' "$PATH"``
  - The ``\\x1e`` delimiter (ASCII Record Separator) isolates the PATH
    from any shell MOTD/banner output
  - 10-second timeout to avoid hangs

ZERO dependencies on PySide6 — pure Python (rule §10.1).
"""

import os
import shutil
import subprocess
from functools import lru_cache


# ── Constants (from LLM Wiki cli_resolver.rs) ──────────────────────────
LOGIN_SHELL_TIMEOUT = 10  # seconds — like LLM Wiki
RECORD_SEP = "\x1e"       # ASCII Record Separator — framing delimiter


@lru_cache(maxsize=1)
def resolve_login_shell_path() -> str:
    """Probes the interactive login shell to get the full PATH.

    Inspired by ``login_shell_path()`` in ``cli_resolver.rs`` of LLM Wiki.

    How it works:
      1. Reads the user's $SHELL (default /bin/sh)
      2. Determines the flags: minimal shells (-ic) vs full (-ilc)
      3. Launches the shell with a command that prints $PATH between \\x1e delimiters
      4. Parses the output to extract the clean PATH

    The result is cached with ``lru_cache`` — the probe happens only once
    for the entire life of the process (like LLM Wiki which uses an in-memory HashMap).

    Returns:
        The full PATH string of the login shell, or the current process PATH
        if the probe fails.
    """
    # Determines which shell the user uses
    shell = os.environ.get("SHELL", "/bin/sh")
    shell_name = os.path.basename(shell)

    # Minimal shells: only -ic (interactive)
    # Full shells: -ilc (interactive + login → loads .zshrc, .bashrc, etc.)
    # This is identical to LLM Wiki cli_resolver.rs logic
    if shell_name in ("sh", "dash", "ash"):
        flags = ["-ic"]
    else:
        flags = ["-ilc"]

    # Command that prints PATH between \x1e delimiters to isolate it from MOTD/banner.
    # Uses printf (POSIX) for maximum compatibility.
    cmd = f"printf '{RECORD_SEP}PATH=%s{RECORD_SEP}\\n' \"$PATH\""

    # Prevents flash of a black terminal window on Windows (GUI apps)
    kwargs = {}
    if os.name == 'nt':
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

    try:
        result = subprocess.run(
            [shell] + flags + [cmd],
            capture_output=True,
            text=True,
            timeout=LOGIN_SHELL_TIMEOUT,
            # LC_ALL=C avoids encoding problems with local output
            env={**os.environ, "LC_ALL": "C"},
            **kwargs
        )

        output = result.stdout

        # Search for the \x1ePATH=...\x1e pattern in the output
        start_marker = f"{RECORD_SEP}PATH="
        start = output.find(start_marker)
        if start >= 0:
            # Skip the marker to get to the value
            value_start = start + len(start_marker)
            end = output.find(RECORD_SEP, value_start)
            if end > value_start:
                return output[value_start:end]

    except subprocess.TimeoutExpired:
        # The shell took more than 10s → probably
        # has a problematic .zshrc. Use fallback.
        pass
    except OSError:
        # Shell not found or not executable
        pass

    # Fallback: returns the current process PATH
    return os.environ.get("PATH", "")


def find_cli_command(
    command: str,
    candidates: list[str] | None = None,
) -> str | None:
    """Searches for a CLI command with fallback to the login shell PATH.

    Pipeline identical to ``find_cli_command()`` in LLM Wiki:

    1. ``shutil.which(command)`` — searches in the current process PATH
    2. If there are alternative candidates (e.g. ``claude.cmd`` on Windows),
       try each with ``shutil.which``
    3. If still not found → login shell probe to get the
       full PATH → search for the command in the expanded PATH

    Args:
        command: The name of the binary to search for (e.g. ``"claude"``).
        candidates: Alternative names to try (e.g. ``["claude.cmd", "claude.exe"]``
                    for Windows). Optional.

    Returns:
        The absolute path of the found binary, or ``None`` if not present.

    Example:
        >>> find_cli_command("claude")
        '/Users/user/.local/bin/claude'

        >>> find_cli_command("claude", candidates=["claude.cmd", "claude.exe"])
        None  # on macOS without Claude installed
    """
    # Step 1: Search with the current process PATH
    path = shutil.which(command)
    if path:
        return path

    # Step 1b: Alternative candidates (useful for Windows where binaries
    # can have different extensions: .cmd, .exe, .bat)
    if candidates:
        for candidate in candidates:
            path = shutil.which(candidate)
            if path:
                return path

    # Step 2: Fallback — login shell PATH probe
    # This solves the macOS Finder case where the PATH is minimal
    full_path = resolve_login_shell_path()
    if full_path:
        # Searches for the command in each directory of the expanded PATH
        for directory in full_path.split(os.pathsep):
            full = os.path.join(directory, command)
            if os.path.isfile(full) and os.access(full, os.X_OK):
                return full

    return None
