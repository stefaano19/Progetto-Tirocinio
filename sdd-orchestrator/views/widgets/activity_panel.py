"""Activity Panel Widget.

Displays background tasks queue, progress bars, and status.
Usually placed at the bottom of the sidebar.
"""

from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
)


class ActivityTaskWidget(QWidget):
    """Widget representing a single active background task."""

    def __init__(self, task_name: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        self.label = QLabel(task_name)
        self.label.setObjectName("activity_task_title")

        self.detail_label = QLabel("Starting...")
        self.detail_label.setObjectName("activity_task_detail")
        
        self.progress = QProgressBar()
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0) # Infinite progress by default
        
        layout.addWidget(self.label)
        layout.addWidget(self.detail_label)
        layout.addWidget(self.progress)
        
    def set_progress(self, current: int, total: int, detail: str = "") -> None:
        self.progress.setRange(0, total)
        self.progress.setValue(current)
        if detail:
            self.detail_label.setText(detail)


class ActivityPanel(QWidget):
    """Bottom drawer for task queue."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("activity_panel")
        self.setMinimumHeight(60)
        self.setMaximumHeight(200)
        
        self._tasks: dict[str, ActivityTaskWidget] = {}
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        header = QLabel("Activity")
        header.setObjectName("section_subtitle")
        header.setContentsMargins(8, 8, 8, 4)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_area.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.scroll_area.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 0, 8, 8)
        self.content_layout.setSpacing(8)
        self.content_layout.addStretch()
        
        self.scroll_area.setWidget(self.content_widget)
        
        # Initially empty state
        self.empty_label = QLabel("No active tasks")
        self.empty_label.setObjectName("activity_empty_label")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.insertWidget(0, self.empty_label)
        
        main_layout.addWidget(header)
        main_layout.addWidget(self.scroll_area)

    @Slot(str)
    def start_task(self, task_id: str, title: str) -> None:
        """Adds a new task to the panel."""
        if not self._tasks:
            self.empty_label.hide()
            
        if task_id in self._tasks:
            return
            
        task_widget = ActivityTaskWidget(title)
        self._tasks[task_id] = task_widget
        
        # Insert at the top (before stretch)
        self.content_layout.insertWidget(len(self._tasks) - 1, task_widget)
        
    @Slot(str, int, int, str)
    def update_task(self, task_id: str, current: int, total: int, detail: str = "") -> None:
        """Updates progress of a task."""
        if task_id in self._tasks:
            self._tasks[task_id].set_progress(current, total, detail)
            
    @Slot(str)
    def complete_task(self, task_id: str) -> None:
        """Removes a completed task."""
        if task_id in self._tasks:
            task_widget = self._tasks.pop(task_id)
            self.content_layout.removeWidget(task_widget)
            task_widget.deleteLater()
            
        if not self._tasks:
            self.empty_label.show()
