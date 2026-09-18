"""Chat Bubble Widget.

Displays a single chat message (user or assistant) with markdown and rich code blocks.
"""

import re

import markdown
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

CODE_BLOCK_PATTERN = re.compile(r"```([^\n]*)\n(.*?)```", re.DOTALL)

_MARKDOWN_EXTENSIONS = ["tables", "sane_lists", "nl2br"]

_MONOSPACE_FAMILIES = ["Fira Code", "JetBrains Mono", "SF Mono", "Consolas", "monospace"]


def _is_dark_theme() -> bool:
    """Reads the current app-wide color scheme (see main.py::apply_theme)."""
    app = QApplication.instance()
    if app is None:
        return True
    return app.styleHints().colorScheme() != Qt.ColorScheme.Light


def _zebra_stripe_tables(html: str, stripe_color: str) -> str:
    """Adds an alternating row background to <tbody> rows.

    QTextDocument's HTML/CSS engine does not support :nth-child, so the
    striping has to be baked into the markup itself.
    """

    def _stripe_body(match: "re.Match[str]") -> str:
        index = 0

        def _stripe_row(_row_match: "re.Match[str]") -> str:
            nonlocal index
            index += 1
            if index % 2 == 0:
                return f'<tr style="background-color:{stripe_color};">'
            return "<tr>"

        return re.sub(r"<tr>", _stripe_row, match.group(0))

    return re.sub(r"<tbody>.*?</tbody>", _stripe_body, html, flags=re.DOTALL)


def _render_markdown(text: str, role: str) -> str:
    """Converts markdown text to Qt-renderable HTML with table striping."""
    html = markdown.markdown(text, extensions=_MARKDOWN_EXTENSIONS)
    dark = _is_dark_theme()
    stripe = "rgba(255, 255, 255, 0.03)" if dark else "rgba(0, 0, 0, 0.03)"
    html = _zebra_stripe_tables(html, stripe)
    weight = 500 if role == "user" else 400
    return f'<div style="font-weight:{weight};">{html}</div>'


class _AutoHeightTextBrowser(QTextBrowser):
    """QTextBrowser that grows to fit its content via sizeHint, not a manual
    fixed-height guess.

    Sizing via setFixedHeight() inside resizeEvent() only recomputes on an
    actual resize — during streaming, new content is pushed in via setHtml()
    with no resize in between, so the cached height goes stale and the tail
    of the response gets clipped. Hooking documentSizeChanged and driving
    sizeHint() from the document lets Qt's layout system re-query the real
    height any time the content or the available width changes.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.document().documentLayout().documentSizeChanged.connect(
            lambda *_: self.updateGeometry()
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.lineWrapMode() != QTextBrowser.LineWrapMode.NoWrap:
            self.document().setTextWidth(self.viewport().width())
        self.updateGeometry()

    def sizeHint(self):
        return self.document().size().toSize()

    def minimumSizeHint(self):
        return self.sizeHint()


class CodeBlockWidget(QFrame):
    """IDE-style code block: dark container, header with language + copy button."""

    def __init__(self, language: str, code: str, parent=None):
        super().__init__(parent)
        self.code = code
        self.setObjectName("code_block_container")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self.header = QFrame()
        self.header.setObjectName("code_block_header")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 6, 8, 6)

        lang_label = QLabel(language.strip() if language.strip() else "text")
        lang_label.setObjectName("code_block_lang")

        self.btn_copy = QPushButton("Copy code")
        self.btn_copy.setObjectName("code_block_copy_btn")
        self.btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy.clicked.connect(self.copy_to_clipboard)

        header_layout.addWidget(lang_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_copy)

        layout.addWidget(self.header)

        # Code area
        self.code_browser = _AutoHeightTextBrowser()
        self.code_browser.setObjectName("code_block_content")
        self.code_browser.setFrameShape(QFrame.Shape.NoFrame)
        self.code_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.code_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.code_browser.setLineWrapMode(QTextBrowser.LineWrapMode.NoWrap)

        # Strict monospace font, with graceful fallback chain
        font = self.code_browser.font()
        font.setFamilies(_MONOSPACE_FAMILIES)
        font.setStyleHint(font.StyleHint.Monospace)
        self.code_browser.setFont(font)

        self.code_browser.setPlainText(code.strip())

        layout.addWidget(self.code_browser)

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.code.strip())
        self.btn_copy.setText("Copied!")
        QTimer.singleShot(2000, lambda: self.btn_copy.setText("Copy code"))


class ChatBubble(QWidget):
    """A bubble displaying a chat message.

    user: right-aligned, muted bg, bolder text.
    assistant: left-aligned, transparent bg, avatar.
    """

    def __init__(self, role: str, content: str, parent=None):
        super().__init__(parent)
        self.role = role

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 8, 16, 8)

        self.bubble = QFrame()
        self.bubble.setObjectName("chat_bubble")
        self.bubble.setProperty("bubble_role", role)

        self.content_layout = QVBoxLayout(self.bubble)
        self.content_layout.setSpacing(12)

        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        if role == "user":
            self.content_layout.setContentsMargins(16, 12, 16, 12)
            main_layout.addStretch()
            main_layout.addWidget(self.bubble)
            self.bubble.setMaximumWidth(650)
        else:
            # Avatar
            avatar_label = QLabel()
            avatar_label.setFixedSize(28, 28)
            avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar_label.setObjectName("chat_avatar_assistant")
            avatar_label.setText("✦")

            avatar_layout = QVBoxLayout()
            avatar_layout.setContentsMargins(0, 4, 0, 0)
            avatar_layout.addWidget(avatar_label)
            avatar_layout.addStretch()

            self.content_layout.setContentsMargins(4, 4, 16, 12)

            main_layout.addLayout(avatar_layout)
            main_layout.addWidget(self.bubble)
            main_layout.addStretch()
            self.bubble.setMaximumWidth(720)

        self.update_content(content)

    def update_content(self, new_content: str) -> None:
        """Update content by parsing markdown and creating appropriate widgets."""
        # Clear existing layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        last_end = 0
        for match in CODE_BLOCK_PATTERN.finditer(new_content):
            start = match.start()
            text_part = new_content[last_end:start].strip()
            if text_part:
                self._add_text_browser(text_part)

            lang = match.group(1).strip()
            code = match.group(2)
            self._add_code_block(lang, code)

            last_end = match.end()

        remaining = new_content[last_end:].strip()
        if remaining:
            self._add_text_browser(remaining)

        if last_end == 0 and not remaining:
            self._add_text_browser("")

    def _add_text_browser(self, md_text: str):
        browser = _AutoHeightTextBrowser()
        browser.setObjectName("chat_bubble_text")
        browser.setOpenExternalLinks(True)
        browser.setFrameShape(QFrame.Shape.NoFrame)
        browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        browser.viewport().setAutoFillBackground(False)

        # Rich-text CSS subset supported by QTextDocument (no pseudo-classes).
        browser.document().setDefaultStyleSheet('''
            body { line-height: 1.5; }
            p { margin: 4px 0; }
            h1, h2, h3 { margin: 8px 0 4px 0; }
            code {
                background-color: rgba(128, 128, 128, 0.18);
                color: #d97757;
                font-family: monospace;
                padding: 1px 4px;
                border-radius: 4px;
            }
            blockquote {
                margin-left: 0px;
                padding-left: 10px;
                border-left: 3px solid #3b82f6;
                color: #6b7280;
                font-style: italic;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 6px 0;
            }
            th, td {
                border: 1px solid rgba(128, 128, 128, 0.35);
                padding: 6px 10px;
            }
            th {
                background-color: rgba(128, 128, 128, 0.15);
                font-weight: 600;
            }
            ul, ol { margin-top: 4px; margin-bottom: 4px; padding-left: 22px; }
            li { margin-bottom: 4px; }
        ''')
        browser.setHtml(_render_markdown(md_text, self.role))
        self.content_layout.addWidget(browser)

    def _add_code_block(self, lang: str, code: str):
        widget = CodeBlockWidget(lang, code)
        self.content_layout.addWidget(widget)
