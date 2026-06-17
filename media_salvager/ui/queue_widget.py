from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class QueueItem:
    def __init__(self, path: Path, duration: str = "Unknown", resolution: str = "Unknown", codec: str = "Unknown") -> None:
        self.path = path
        self.duration = duration
        self.resolution = resolution
        self.codec = codec
        self.status = "Pending"


class QueueWidget(QWidget):
    queue_changed = Signal()
    selection_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._items: list[QueueItem] = []
        self._build_ui()

    def _build_ui(self) -> None:
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Filename", "Duration", "Resolution", "Codec", "Status"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.selection_changed)

        self.remove_button = QToolButton()
        self.remove_button.setText("Remove")
        self.clear_button = QToolButton()
        self.clear_button.setText("Clear")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch(1)
        button_layout.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addLayout(button_layout)

        self.remove_button.clicked.connect(self.remove_selected)
        self.clear_button.clicked.connect(self.clear)

    def add_items(self, paths: Iterable[Path]) -> None:
        for path in paths:
            if path.is_file() and not self._contains(path):
                self._items.append(QueueItem(path))
        self._refresh_table()
        self.queue_changed.emit()

    def _contains(self, path: Path) -> bool:
        return any(item.path == path for item in self._items)

    def remove_selected(self) -> None:
        selected = list({item.row() for item in self.table.selectedItems()})
        for row in sorted(selected, reverse=True):
            if 0 <= row < len(self._items):
                del self._items[row]
        self._refresh_table()
        self.queue_changed.emit()

    def clear(self) -> None:
        self._items.clear()
        self._refresh_table()
        self.queue_changed.emit()

    def update_status(self, path: Path, status: str) -> None:
        for item in self._items:
            if item.path == path:
                item.status = status
        self._refresh_table()

    def _refresh_table(self) -> None:
        self.table.setRowCount(0)
        for item in self._items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item.path.name))
            self.table.setItem(row, 1, QTableWidgetItem(item.duration))
            self.table.setItem(row, 2, QTableWidgetItem(item.resolution))
            self.table.setItem(row, 3, QTableWidgetItem(item.codec))
            self.table.setItem(row, 4, QTableWidgetItem(item.status))

    @property
    def items(self) -> list[QueueItem]:
        return self._items

    def selected_paths(self) -> list[Path]:
        rows = sorted({item.row() for item in self.table.selectedItems()})
        return [self._items[row].path for row in rows if 0 <= row < len(self._items)]
