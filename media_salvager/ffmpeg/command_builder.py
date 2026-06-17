from __future__ import annotations

from pathlib import Path
from typing import Iterable


class FFmpegCommandBuilder:
    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        format_name: str,
        video_codec: str,
        audio_codec: str,
        subtitle_mode: str,
        stream_copy: bool,
        genpts: bool,
        recover: bool,
        preserve_metadata: bool,
        overwrite: bool,
        custom_args: str,
    ) -> None:
        self.input_path = input_path
        self.output_path = output_path
        self.format_name = format_name
        self.video_codec = video_codec
        self.audio_codec = audio_codec
        self.subtitle_mode = subtitle_mode
        self.stream_copy = stream_copy
        self.genpts = genpts
        self.recover = recover
        self.preserve_metadata = preserve_metadata
        self.overwrite = overwrite
        self.custom_args = custom_args

    def build(self) -> list[str]:
        command = ["ffmpeg"]
        if self.overwrite:
            command.append("-y")
        else:
            command.append("-n")

        if self.recover:
            command.extend(["-err_detect", "ignore_err", "-fflags", "+genpts"])

        if self.genpts:
            command.extend(["-fflags", "+genpts"])

        command.extend(["-i", str(self.input_path)])
        if self.stream_copy:
            command.extend(["-c", "copy"])
        else:
            if self.video_codec:
                command.extend(["-c:v", self.video_codec])
            if self.audio_codec:
                command.extend(["-c:a", self.audio_codec])
            if self.subtitle_mode == "copy":
                command.extend(["-c:s", "copy"])
            elif self.subtitle_mode == "drop":
                command.extend(["-sn"])

        if self.preserve_metadata:
            command.append("-map_metadata")
            command.append("0")

        if self.custom_args:
            command.extend(self.custom_args.split())

        command.extend(["-f", self.format_name, str(self.output_path)])
        return command
