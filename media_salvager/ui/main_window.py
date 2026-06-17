from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from media_salvager.ffmpeg.formats import parse_codecs, parse_formats, supported_hardware_encoders
from media_salvager.ffmpeg.probe import extract_stream_info
from media_salvager.ui.format_search import SearchableComboBox
from media_salvager.ui.log_panel import LogPanel
from media_salvager.ui.queue_widget import QueueWidget
from media_salvager.workers.conversion_worker import ConversionWorker


class MainWindow(QWidget):
    conversion_started = Signal()
    conversion_stopped = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Media Salvager")
        self.resize(1200, 800)
        self.setAcceptDrops(True)
        self.supported_formats = parse_formats()
        self.supported_codecs = parse_codecs()
        self.hardware_encoders = supported_hardware_encoders()
        self._build_ui()
        self._connect_signals()
        self.worker: ConversionWorker | None = None

    def _build_ui(self) -> None:
        self.queue_widget = QueueWidget(self)

        self.open_files_button = QPushButton("Add Files")
        self.open_folder_button = QPushButton("Add Folder")
        self.output_dir_button = QPushButton("Select Output Directory")
        self.output_dir_label = QLabel("No output directory selected")
        self.output_dir_label.setWordWrap(True)

        options_group = QGroupBox("Output Options")
        options_layout = QFormLayout()
        self.format_selector = SearchableComboBox("Format", self.supported_formats)
        self.video_selector = SearchableComboBox("Video Codec", self.supported_codecs)
        self.audio_selector = SearchableComboBox("Audio Codec", self.supported_codecs)
        self.subtitle_selector = QComboBox()
        self.subtitle_selector.addItems(["copy", "drop"])
        self.stream_copy_checkbox = QCheckBox("Stream copy")
        self.genpts_checkbox = QCheckBox("Generate timestamps")
        self.recover_checkbox = QCheckBox("Recover damaged files")
        self.preserve_metadata_checkbox = QCheckBox("Preserve metadata")
        self.overwrite_checkbox = QCheckBox("Overwrite existing files")
        self.delete_source_checkbox = QCheckBox("Delete source after success")
        self.custom_args_input = QLineEdit()
        self.custom_args_input.setPlaceholderText("Custom FFmpeg args")

        options_layout.addRow("Container:", self.format_selector)
        options_layout.addRow("Video:", self.video_selector)
        options_layout.addRow("Audio:", self.audio_selector)
        options_layout.addRow("Subtitles:", self.subtitle_selector)
        options_layout.addRow(self.stream_copy_checkbox)
        options_layout.addRow(self.genpts_checkbox)
        options_layout.addRow(self.recover_checkbox)
        options_layout.addRow(self.preserve_metadata_checkbox)
        options_layout.addRow(self.overwrite_checkbox)
        options_layout.addRow(self.delete_source_checkbox)
        options_layout.addRow("Custom args:", self.custom_args_input)
        options_group.setLayout(options_layout)

        self.start_button = QPushButton("Start Conversion")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.command_preview = QTextEdit()
        self.command_preview.setReadOnly(True)
        self.command_preview.setFixedHeight(120)

        self.file_progress = QProgressBar()
        self.overall_progress = QProgressBar()
        self.current_stats = QLabel("FPS: - | Bitrate: - | Speed: - | ETA: -")

        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        progress_layout.addWidget(self.file_progress)
        progress_layout.addWidget(self.overall_progress)
        progress_layout.addWidget(self.current_stats)
        progress_group.setLayout(progress_layout)

        self.log_panel = LogPanel(self)

        preset_group = QGroupBox("Presets")
        preset_layout = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "MP4 H264",
            "MP4 H265",
            "MKV Archive",
            "DVD Recovery",
            "WebM",
            "Audio MP3",
            "Audio FLAC",
        ])
        self.load_preset_button = QPushButton("Load Preset")
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addWidget(self.load_preset_button)
        preset_group.setLayout(preset_layout)

        button_row = QHBoxLayout()
        button_row.addWidget(self.open_files_button)
        button_row.addWidget(self.open_folder_button)
        button_row.addWidget(self.output_dir_button)
        button_row.addStretch(1)

        left_panel = QVBoxLayout()
        left_panel.addLayout(button_row)
        left_panel.addWidget(self.output_dir_label)
        left_panel.addWidget(self.queue_widget)
        left_panel.addWidget(progress_group)
        left_panel.addWidget(self.command_preview)
        left_panel.addWidget(self.log_panel)

        right_panel = QVBoxLayout()
        right_panel.addWidget(options_group)
        right_panel.addWidget(preset_group)
        right_panel.addWidget(self.start_button)
        right_panel.addWidget(self.stop_button)
        right_panel.addStretch(1)

        main_layout = QGridLayout(self)
        main_layout.addLayout(left_panel, 0, 0, 1, 2)
        main_layout.addLayout(right_panel, 0, 2)
        main_layout.setColumnStretch(0, 3)
        main_layout.setColumnStretch(1, 0)
        main_layout.setColumnStretch(2, 1)

    def _connect_signals(self) -> None:
        self.open_files_button.clicked.connect(self.on_add_files)
        self.open_folder_button.clicked.connect(self.on_add_folder)
        self.output_dir_button.clicked.connect(self.select_output_directory)
        self.start_button.clicked.connect(self.start_conversion)
        self.stop_button.clicked.connect(self.stop_conversion)
        self.load_preset_button.clicked.connect(self.load_preset)
        self.queue_widget.queue_changed.connect(self.on_queue_changed)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        paths = [Path(url.toLocalFile()) for url in urls]
        self.add_paths(paths)

    def on_add_files(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        files, _ = QFileDialog.getOpenFileNames(self, "Select Media Files")
        self.add_paths([Path(file) for file in files])

    def on_add_folder(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.add_paths([Path(folder)])

    def add_paths(self, paths: Iterable[Path]) -> None:
        files: list[Path] = []
        for path in paths:
            if path.is_dir():
                for child in path.rglob("*"):
                    if child.is_file():
                        files.append(child)
            elif path.is_file():
                files.append(path)
        self.queue_widget.add_items(files)
        for item in self.queue_widget.items:
            try:
                metadata = extract_stream_info(item.path)
                item.duration = metadata["duration"]
                item.resolution = metadata["resolution"]
                item.codec = metadata["codec"]
            except Exception:
                item.duration = "Unknown"
                item.resolution = "Unknown"
                item.codec = "Unknown"
        self.queue_widget._refresh_table()

    def select_output_directory(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.output_dir_label.setText(folder)

    def load_preset(self) -> None:
        preset = self.preset_combo.currentText()
        mapping = {
            "MP4 H264": ("mp4", "libx264", "aac", "copy"),
            "MP4 H265": ("mp4", "libx265", "aac", "copy"),
            "MKV Archive": ("matroska", "libx264", "flac", "copy"),
            "DVD Recovery": ("mpeg", "mpeg2video", "mp2", "copy"),
            "WebM": ("webm", "libvpx-vp9", "libopus", "copy"),
            "Audio MP3": ("mp3", "libmp3lame", "copy", "drop"),
            "Audio FLAC": ("flac", "flac", "copy", "drop"),
        }
        if preset in mapping:
            format_name, video_codec, audio_codec, subtitle_mode = mapping[preset]
            self.format_selector.set_selected_key(format_name)
            self.video_selector.set_selected_key(video_codec)
            self.audio_selector.set_selected_key(audio_codec)
            self.subtitle_selector.setCurrentText(subtitle_mode)

    def on_queue_changed(self) -> None:
        self.overall_progress.setValue(0)
        self.file_progress.setValue(0)

    def _format_options(self) -> dict[str, str]:
        return {
            "format": self.format_selector.selected_key or self.format_selector.selected_text,
            "video_codec": self.video_selector.selected_key or self.video_selector.selected_text,
            "audio_codec": self.audio_selector.selected_key or self.audio_selector.selected_text,
            "subtitle_mode": self.subtitle_selector.currentText(),
            "stream_copy": "true" if self.stream_copy_checkbox.isChecked() else "false",
            "genpts": "true" if self.genpts_checkbox.isChecked() else "false",
            "recover": "true" if self.recover_checkbox.isChecked() else "false",
            "preserve_metadata": "true" if self.preserve_metadata_checkbox.isChecked() else "false",
            "overwrite": "true" if self.overwrite_checkbox.isChecked() else "false",
            "custom_args": self.custom_args_input.text().strip(),
        }

    def start_conversion(self) -> None:
        if not self.queue_widget.items:
            return
        output_dir = Path(self.output_dir_label.text())
        if not output_dir.exists():
            output_dir = Path.home() / "MediaSalvagerOutput"
            output_dir.mkdir(parents=True, exist_ok=True)
            self.output_dir_label.setText(str(output_dir))

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.worker = ConversionWorker(
            [item.path for item in self.queue_widget.items],
            output_dir,
            self._format_options(),
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.log_output.connect(self.log_panel.append)
        self.worker.finished.connect(self.on_finished)
        self.worker.command_preview.connect(self.command_preview.setPlainText)
        self.worker.start()

    def stop_conversion(self) -> None:
        if self.worker:
            self.worker.stop()
            self.stop_button.setEnabled(False)
            self.start_button.setEnabled(True)

    def on_progress(self, filename: str, message: str) -> None:
        self.log_panel.append(f"{filename}: {message}")
        self.current_stats.setText(self._extract_stats(message))
        self.file_progress.setValue(min(100, self.file_progress.value() + 1))

    def _extract_stats(self, message: str) -> str:
        if "speed=" in message or "bitrate=" in message:
            fps = "-"
            bitrate = "-"
            speed = "-"
            eta = "-"
            tokens = message.split()
            for token in tokens:
                if token.startswith("fps="):
                    fps = token.replace("fps=", "")
                elif token.startswith("bitrate="):
                    bitrate = token.replace("bitrate=", "")
                elif token.startswith("speed="):
                    speed = token.replace("speed=", "")
                elif token.startswith("time="):
                    eta = token.replace("time=", "")
            return f"FPS: {fps} | Bitrate: {bitrate} | Speed: {speed} | ETA: {eta}"
        return self.current_stats.text()

    def on_finished(self, path: Path, success: bool) -> None:
        self.queue_widget.update_status(path, "Completed" if success else "Failed")
        self.file_progress.setValue(100)
        self.overall_progress.setValue(min(100, self.overall_progress.value() + int(100 / max(1, len(self.queue_widget.items)))))
        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)

