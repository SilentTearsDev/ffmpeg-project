from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PySide6.QtCore import QThread, Signal

from media_salvager.ffmpeg.command_builder import FFmpegCommandBuilder
from media_salvager.ffmpeg.converter import monitor_process, run_ffmpeg_command
from media_salvager.ffmpeg.probe import extract_stream_info


@dataclass
class ConversionProgress:
    path: Path
    message: str


class ConversionWorker(QThread):
    progress = Signal(str, str)
    finished = Signal(Path, bool)
    log_output = Signal(str)
    command_preview = Signal(str)

    def __init__(self, inputs: list[Path], output_dir: Path, options: dict[str, str], parent=None) -> None:
        super().__init__(parent)
        self.inputs = inputs
        self.output_dir = output_dir
        self.options = options
        self._stop_requested = False

    def run(self) -> None:
        for path in self.inputs:
            if self._stop_requested:
                self.log_output.emit(f"Conversion cancelled for {path.name}")
                self.finished.emit(path, False)
                return
            try:
                output_path = self.output_dir / f"{path.stem}.{self.options['format']}"
                builder = FFmpegCommandBuilder(
                    input_path=path,
                    output_path=output_path,
                    format_name=self.options["format"],
                    video_codec=self.options["video_codec"],
                    audio_codec=self.options["audio_codec"],
                    subtitle_mode=self.options["subtitle_mode"],
                    stream_copy=self.options["stream_copy"] == "true",
                    genpts=self.options["genpts"] == "true",
                    recover=self.options["recover"] == "true",
                    preserve_metadata=self.options["preserve_metadata"] == "true",
                    overwrite=self.options["overwrite"] == "true",
                    custom_args=self.options["custom_args"],
                )
                command = builder.build()
                self.command_preview.emit(" ".join(command))
                self.log_output.emit(f"Executing: {' '.join(command)}")
                process = run_ffmpeg_command(command)
                for line in monitor_process(process):
                    self.log_output.emit(line)
                    self.progress.emit(path.name, line)
                process.wait()
                success = process.returncode == 0
                if success and self.options.get("delete_source") == "true":
                    try:
                        path.unlink()
                        self.log_output.emit(f"Deleted source file: {path}")
                    except OSError as err:
                        self.log_output.emit(f"Failed to delete source {path}: {err}")
                self.finished.emit(path, success)
            except Exception as exc:
                self.log_output.emit(f"Error: {exc}")
                self.finished.emit(path, False)

    def stop(self) -> None:
        self._stop_requested = True
