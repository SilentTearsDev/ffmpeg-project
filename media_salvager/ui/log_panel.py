from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QFileDialog, QPlainTextEdit, QPushButton, QWidget


class LogPanel(QWidget):
    """Scrollable logger panel with save capability."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("FFmpeg log output appears here.")

        self.save_button = QPushButton("Save Log")
        self.clear_button = QPushButton("Clear Log")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.save_button)
        button_layout.setContentsMargins(0, 0, 0, 0)

        layout = QHBoxLayout(self)
        layout.addWidget(self.log_view)
        layout.addLayout(button_layout)

        self.save_button.clicked.connect(self.save_log)
        self.clear_button.clicked.connect(self.clear)

    def append(self, text: str) -> None:
        self.log_view.appendPlainText(text)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    def clear(self) -> None:
        self.log_view.clear()

    def save_log(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, "Save FFmpeg Log", "media_salvager_log.txt", "Text Files (*.txt);;All Files (*)")
        if filename:
            with open(filename, "w", encoding="utf-8") as handle:
                handle.write(self.log_view.toPlainText())
