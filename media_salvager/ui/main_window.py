from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
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
        self.resize(1200, 840)
        self.setAcceptDrops(True)
        self.supported_formats = parse_formats()
        self.supported_codecs = parse_codecs()
        self.hardware_encoders = supported_hardware_encoders()
        self._build_ui()
        self._connect_signals()
        self.worker: ConversionWorker | None = None

    def _build_ui(self) -> None:
        self.queue_widget = QueueWidget(self)

        self.drag_drop_label = QLabel("Drag and drop files or folders here")
        self.drag_drop_label.setAlignment(Qt.AlignCenter)
        self.drag_drop_label.setFixedHeight(140)
        self.drag_drop_label.setStyleSheet(
            "background-color: #1e1e1e; border: 2px dashed #3c3c3c; color: #e0e0e0; font-size: 14pt;"
        )

        self.open_files_button = QPushButton("Add Files")
        self.open_folder_button = QPushButton("Add Folder")
        self.output_dir_button = QPushButton("Select Output Folder")
        self.output_dir_label = QLabel("No output directory selected")
        self.output_dir_label.setWordWrap(True)

        options_group = QGroupBox("Conversion Settings")
        options_layout = QFormLayout()
        self.format_selector = SearchableComboBox("Output Format", self._common_formats())
        self.profile_selector = QComboBox()
        self.profile_selector.addItems(["Fast", "Balanced", "High Quality", "Archive"])
        self.hardware_selector = QComboBox()
        self.hardware_selector.addItems(["Auto", "CPU Only"])

        options_layout.addRow("Format:", self.format_selector)
        options_layout.addRow("Quality:", self.profile_selector)
        options_layout.addRow("Hardware:", self.hardware_selector)
        options_layout.addRow("Output folder:", self.output_dir_button)
        options_layout.addRow(self.output_dir_label)
        options_group.setLayout(options_layout)

        self.advanced_panel = QGroupBox("Advanced Options")
        self.advanced_panel.setCheckable(True)
        self.advanced_panel.setChecked(False)
        self.advanced_widget = QWidget()
        self.advanced_widget.setVisible(False)

        self.manual_codec_checkbox = QCheckBox("Enable manual codec selection")
        self.manual_video_selector = SearchableComboBox("Video Codec", self.supported_codecs)
        self.manual_audio_selector = SearchableComboBox("Audio Codec", self.supported_codecs)
        self.manual_video_selector.setEnabled(False)
        self.manual_audio_selector.setEnabled(False)

        self.stream_copy_checkbox = QCheckBox("Stream copy")
        self.crf_input = QLineEdit()
        self.crf_input.setPlaceholderText("CRF value (0-51)")
        self.bitrate_input = QLineEdit()
        self.bitrate_input.setPlaceholderText("Bitrate (e.g. 2500k)")
        self.subtitle_selector = QComboBox()
        self.subtitle_selector.addItems(["copy", "drop", "none"])
        self.preserve_metadata_checkbox = QCheckBox("Preserve metadata")
        self.delete_source_checkbox = QCheckBox("Delete source after success")
        self.custom_args_input = QLineEdit()
        self.custom_args_input.setPlaceholderText("Custom FFmpeg arguments")

        advanced_layout = QFormLayout(self.advanced_widget)
        advanced_layout.addRow(self.manual_codec_checkbox)
        advanced_layout.addRow("Video codec:", self.manual_video_selector)
        advanced_layout.addRow("Audio codec:", self.manual_audio_selector)
        advanced_layout.addRow(self.stream_copy_checkbox)
        advanced_layout.addRow("CRF:", self.crf_input)
        advanced_layout.addRow("Bitrate:", self.bitrate_input)
        advanced_layout.addRow("Subtitle:", self.subtitle_selector)
        advanced_layout.addRow(self.preserve_metadata_checkbox)
        advanced_layout.addRow(self.delete_source_checkbox)
        advanced_layout.addRow("Extra args:", self.custom_args_input)

        panel_layout = QVBoxLayout(self.advanced_panel)
        panel_layout.addWidget(self.advanced_widget)
        panel_layout.setContentsMargins(8, 24, 8, 8)

        self.start_button = QPushButton("Convert")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.command_preview = QTextEdit()
        self.command_preview.setReadOnly(True)
        self.command_preview.setFixedHeight(110)

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

        button_row = QHBoxLayout()
        button_row.addWidget(self.open_files_button)
        button_row.addWidget(self.open_folder_button)
        button_row.addStretch(1)

        left_panel = QVBoxLayout()
        left_panel.addWidget(self.drag_drop_label)
        left_panel.addLayout(button_row)
        left_panel.addWidget(self.queue_widget)
        left_panel.addWidget(progress_group)
        left_panel.addWidget(self.command_preview)
        left_panel.addWidget(self.log_panel)

        right_panel = QVBoxLayout()
        right_panel.addWidget(options_group)
        right_panel.addWidget(self.advanced_panel)
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
        self.queue_widget.queue_changed.connect(self.on_queue_changed)
        self.advanced_panel.toggled.connect(self.advanced_widget.setVisible)
        self.manual_codec_checkbox.toggled.connect(self._toggle_manual_codec_selection)

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

        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_dir_label.setText(folder)

    def _common_formats(self) -> list[tuple[str, str]]:
        common = {
            "mp4": "MP4",
            "matroska": "MKV",
            "webm": "WebM",
            "mp3": "MP3",
            "flac": "FLAC",
        }
        available = [item for item in self.supported_formats if item[0] in common]
        if available:
            return [(code, common[code]) for code, _ in available]
        return [(key, label) for key, label in common.items()]

    def _toggle_manual_codec_selection(self, checked: bool) -> None:
        self.manual_video_selector.setEnabled(checked)
        self.manual_audio_selector.setEnabled(checked)

    def _format_extension(self, format_name: str) -> str:
        extension_map = {
            "matroska": "mkv",
            "mp4": "mp4",
            "webm": "webm",
            "mp3": "mp3",
            "flac": "flac",
        }
        return extension_map.get(format_name, format_name)

    def _select_encoders(self, format_name: str, profile: str, hardware: str) -> tuple[str, str, bool]:
        video_codec = ""
        audio_codec = "aac"
        audio_only = False
        use_cpu = hardware == "CPU Only"
        auto_hw = hardware == "Auto" and not use_cpu

        def choose_video_cpu(preferred: str, fallback: str) -> str:
            if auto_hw:
                if preferred in self.hardware_encoders:
                    return preferred
                if fallback in self.hardware_encoders:
                    return fallback
            return fallback

        container = format_name.lower()
        if container == "mp4":
            video_codec = choose_video_cpu("h264_nvenc", "libx264")
            if profile == "High Quality":
                video_codec = choose_video_cpu("hevc_nvenc", "libx265")
            audio_codec = "aac"
        elif container == "matroska":
            if profile == "Balanced":
                video_codec = choose_video_cpu("hevc_nvenc", "libx265")
                audio_codec = "aac"
            elif profile == "High Quality":
                video_codec = choose_video_cpu("av1_nvenc", "libaom-av1")
                audio_codec = "libopus"
            else:
                video_codec = "ffv1"
                audio_codec = "flac"
        elif container == "webm":
            if profile == "High Quality":
                video_codec = choose_video_cpu("av1_nvenc", "libaom-av1")
            else:
                video_codec = choose_video_cpu("vp9_nvenc", "libvpx-vp9")
            audio_codec = "libopus"
        elif container == "mp3":
            audio_codec = "libmp3lame"
            audio_only = True
        elif container == "flac":
            audio_codec = "flac"
            audio_only = True
        else:
            video_codec = choose_video_cpu("h264_nvenc", "libx264")
            audio_codec = "aac"

        if container in {"mp3", "flac"}:
            video_codec = ""

        if self.manual_codec_checkbox.isChecked():
            manual_video = self.manual_video_selector.selected_key or self.manual_video_selector.selected_text
            manual_audio = self.manual_audio_selector.selected_key or self.manual_audio_selector.selected_text
            return manual_video, manual_audio, audio_only

        return video_codec, audio_codec, audio_only

    def _format_options(self) -> dict[str, str]:
        format_choice = self.format_selector.selected_key or self.format_selector.selected_text
        profile_choice = self.profile_selector.currentText()
        hardware_choice = self.hardware_selector.currentText()
        video_codec, audio_codec, audio_only = self._select_encoders(format_choice, profile_choice, hardware_choice)
        return {
            "format": format_choice,
            "quality_profile": profile_choice,
            "hardware": hardware_choice,
            "video_codec": video_codec,
            "audio_codec": audio_codec,
            "subtitle_mode": self.subtitle_selector.currentText(),
            "stream_copy": "true" if self.stream_copy_checkbox.isChecked() else "false",
            "genpts": "true" if self.advanced_panel.isChecked() and self.stream_copy_checkbox.isChecked() else "false",
            "recover": "true" if self.advanced_panel.isChecked() and self.preserve_metadata_checkbox.isChecked() else "false",
            "preserve_metadata": "true" if self.preserve_metadata_checkbox.isChecked() else "false",
            "overwrite": "true",
            "delete_source": "true" if self.delete_source_checkbox.isChecked() else "false",
            "custom_args": self.custom_args_input.text().strip(),
            "audio_only": "true" if audio_only else "false",
            "bitrate": self.bitrate_input.text().strip(),
            "crf": self.crf_input.text().strip(),
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
        options = self._format_options()
        self.worker = ConversionWorker(
            [item.path for item in self.queue_widget.items],
            output_dir,
            options,
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

