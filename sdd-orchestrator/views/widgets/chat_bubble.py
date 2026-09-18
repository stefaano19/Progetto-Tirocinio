"""Chat Bubble Widget.

Displays a single chat message (user or assistant) with markdown and rich code blocks.
"""

import re
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextBrowser,
    QFrame,
    QPushButton,
    QApplication,
)

CODE_BLOCK_PATTERN = re.compile(r"```([^\n]*)\n(.*?)```", re.DOTALL)


class _AutoHeightTextBrowser(QTextBrowser):
    """QTextBrowser that tracks its wrapped-content height as it is resized."""

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.update_height()

    def update_height(self) -> None:
        if self.lineWrapMode() != QTextBrowser.LineWrapMode.NoWrap:
            self.document().setTextWidth(self.viewport().width())
        height = int(self.document().size().height())
        self.setFixedHeight(max(height + 10, 20))


class CodeBlockWidget(QWidget):
    """Widget to display code IDE-style with a header and a copy button."""
    
    def __init__(self, language: str, code: str, parent=None):
        super().__init__(parent)
        self.code = code
        self.setObjectName("code_block_container")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        self.header = QWidget()
        self.header.setObjectName("code_block_header")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 6, 12, 6)
        
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
        
        # Monospace font
        font = self.code_browser.font()
        font.setFamily("Fira Code, JetBrains Mono, monospace")
        self.code_browser.setFont(font)
        
        self.code_browser.setPlainText(code.strip())
        
        layout.addWidget(self.code_browser)
        
    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.code.strip())
        self.btn_copy.setText("Copied!")
        QTimer.singleShot(2000, lambda: self.btn_copy.setText("Copy code"))


class ChatBubble(QWidget):
    """A bubble displaying a chat message.
    
    user: right-aligned, light bg.
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
            self.bubble.setMaximumWidth(700)
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
            self.bubble.setMaximumWidth(800)
            
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
        
        # Stili essenziali per il markdown
        browser.document().setDefaultStyleSheet('''
            code { 
                background-color: rgba(128, 128, 128, 0.15); 
                color: #d97757; 
                font-family: monospace;
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
            }
            th, td { 
                border: 1px solid #d1d5db; 
                padding: 6px; 
            }
            ul, ol { margin-top: 4px; margin-bottom: 4px; }
            li { margin-bottom: 4px; }
        ''')
        browser.setMarkdown(md_text)
        self.content_layout.addWidget(browser)

    def _add_code_block(self, lang: str, code: str):
        widget = CodeBlockWidget(lang, code)
        self.content_layout.addWidget(widget)
