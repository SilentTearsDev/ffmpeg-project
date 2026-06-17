from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from media_salvager.ui.main_window import MainWindow
from media_salvager.ffmpeg.probe import ffmpeg_available


def main() -> int:
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app.setApplicationName("Media Salvager")
    app.setOrganizationName("MediaSalvager")

    if not ffmpeg_available():
        QMessageBox.critical(
            None,
            "Missing FFmpeg",
            "FFmpeg and ffprobe must be installed and available on your PATH before running Media Salvager.",
        )
        return 1

    theme_path = Path(__file__).resolve().parent / "media_salvager" / "assets" / "theme.qss"
    if theme_path.exists():
        app.setStyleSheet(theme_path.read_text(encoding="utf-8"))

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
