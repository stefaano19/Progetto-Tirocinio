"""Status Indicator — colored pulsing dot.

Inspired by LLM Wiki daemon status dot (`icon-sidebar.tsx`):
  - Pulsing green  = ok / CLI found
  - Pulsing amber  = scanning / starting
  - Solid red     = error
  - Solid gray    = idle / no CLI

Implemented with QPainter + QPropertyAnimation for the pulse.
"""

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QSize,
    Qt,
)
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget


class StatusIndicator(QWidget):
    """Circular dot with pulse animation to indicate status."""

    # ── Colors by status (from claude.md palette §6) ──────────────
    STATUS_COLORS: dict[str, str] = {
        "ok": "#40c057",       # success green
        "scanning": "#fab005", # warning amber
        "error": "#fa5252",    # error red
        "idle": "#909296",     # muted gray
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("status_indicator")
        self.setFixedSize(16, 16)
        self.setToolTip("System status")

        # Internal state
        self._status = "idle"
        self._color = QColor(self.STATUS_COLORS["idle"])
        self._opacity = 1.0

        # Pulse animation (opacity oscillates between 0.4 and 1.0)
        self._pulse_anim = QPropertyAnimation(self, b"pulse_opacity")
        self._pulse_anim.setDuration(1200)
        self._pulse_anim.setStartValue(1.0)
        self._pulse_anim.setEndValue(0.4)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_anim.setLoopCount(-1)  # infinite loop
        
        # Ensure it stops when the application quits (e.g. Ctrl+C)
        from PySide6.QtCore import QCoreApplication
        app = QCoreApplication.instance()
        if app:
            app.aboutToQuit.connect(self._pulse_anim.stop)

    # ── Property for QPropertyAnimation ─────────────────────────────

    def _get_pulse_opacity(self) -> float:
        return self._opacity

    def _set_pulse_opacity(self, value: float) -> None:
        try:
            self._opacity = value
            self.update()  # trigger repaint
        except RuntimeError:
            pass

    pulse_opacity = Property(
        float, _get_pulse_opacity, _set_pulse_opacity,
    )

    # ── Public API ────────────────────────────────────────────────

    def set_status(self, status: str) -> None:
        """Change status: 'ok', 'scanning', 'error', 'idle'."""
        if status not in self.STATUS_COLORS:
            status = "idle"

        self._status = status
        self._color = QColor(self.STATUS_COLORS[status])

        # Pulse only for "active" states (ok and scanning)
        if status in ("ok", "scanning"):
            if self._pulse_anim.state() != QPropertyAnimation.State.Running:
                self._pulse_anim.start()
        else:
            self._pulse_anim.stop()
            self._opacity = 1.0

        self.setToolTip(f"Status: {status}")
        self.update()

    def get_status(self) -> str:
        return self._status

    # ── Rendering ───────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Color with animated opacity
        color = QColor(self._color)
        color.setAlphaF(self._opacity)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)

        # Draw centered circle (10px diameter inside 16px widget)
        dot_size = 10
        x = (self.width() - dot_size) // 2
        y = (self.height() - dot_size) // 2
        painter.drawEllipse(x, y, dot_size, dot_size)

        painter.end()

    def sizeHint(self) -> QSize:
        return QSize(16, 16)

    def hideEvent(self, event) -> None:
        """Stop animation when hidden or closing to prevent PySide destruction crashes."""
        if hasattr(self, "_pulse_anim") and self._pulse_anim.state() == QPropertyAnimation.State.Running:
            self._pulse_anim.stop()
        super().hideEvent(event)
