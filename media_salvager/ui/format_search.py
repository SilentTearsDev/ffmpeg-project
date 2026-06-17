from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QWidget


class SearchableComboBox(QWidget):
    """A searchable drop-down list with live filtering."""

    value_changed = Signal(str)

    def __init__(self, label: str, items: Sequence[Tuple[str, str]] | None = None, parent=None) -> None:
        super().__init__(parent)
        self._items: List[Tuple[str, str]] = []
        self._build_ui(label)
        self.set_items(items or [])

    def _build_ui(self, label: str) -> None:
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText(f"Search {label.lower()}...")
        self.filter_input.textChanged.connect(self._filter_items)

        self.combo = QComboBox()
        self.combo.setEditable(False)
        self.combo.currentTextChanged.connect(self._emit_value_changed)

        descriptor = QLabel(label)
        descriptor.setFixedWidth(90)

        layout = QHBoxLayout(self)
        layout.addWidget(descriptor)
        layout.addWidget(self.filter_input)
        layout.addWidget(self.combo)
        layout.setContentsMargins(0, 0, 0, 0)

    def _filter_items(self, text: str) -> None:
        self.combo.clear()
        lower_search = text.lower()
        for key, label in self._items:
            if lower_search in key.lower() or lower_search in label.lower():
                self.combo.addItem(label, key)

    def _emit_value_changed(self, _: str) -> None:
        self.value_changed.emit(self.selected_key)

    def set_items(self, items: Sequence[Tuple[str, str]]) -> None:
        self._items = list(items)
        self._filter_items(self.filter_input.text())
        if self.combo.count() > 0:
            self.combo.setCurrentIndex(0)

    @property
    def selected_key(self) -> str:
        return self.combo.currentData() or ""

    @property
    def selected_text(self) -> str:
        return self.combo.currentText()

    def set_selected_key(self, key: str) -> None:
        for index in range(self.combo.count()):
            if self.combo.itemData(index) == key:
                self.combo.setCurrentIndex(index)
                return

    def update_items(self, items: Sequence[Tuple[str, str]]) -> None:
        self.set_items(items)


class SearchableListPanel(QWidget):
    """A small helper panel to host a searchable combo list."""

    def __init__(self, label: str, items: Sequence[Tuple[str, str]] | None = None, parent=None) -> None:
        super().__init__(parent)
        self.combo = SearchableComboBox(label, items, self)
        layout = QHBoxLayout(self)
        layout.addWidget(self.combo)
        layout.setContentsMargins(0, 0, 0, 0)
