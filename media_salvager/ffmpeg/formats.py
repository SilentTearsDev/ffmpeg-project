from __future__ import annotations

import subprocess
from typing import Sequence, Tuple


def _run_ffmpeg_list(args: list[str]) -> str:
    process = subprocess.run(["ffmpeg", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return process.stdout + process.stderr


def parse_formats() -> list[Tuple[str, str]]:
    output = _run_ffmpeg_list(["-formats"])
    formats: list[Tuple[str, str]] = []
    for line in output.splitlines():
        if line.startswith(" ") and not line.startswith("  "):
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                code, name = parts
                formats.append((code, name))
    return formats


def parse_codecs() -> list[Tuple[str, str]]:
    output = _run_ffmpeg_list(["-codecs"])
    codecs: list[Tuple[str, str]] = []
    for line in output.splitlines():
        if line.startswith(" D") or line.startswith(" E") or line.startswith(" EV") or line.startswith(" DE"):
            code = line[2:7].strip()
            description = line[7:].strip()
            codecs.append((code, description))
    return codecs


def supported_hardware_encoders() -> list[str]:
    encoders = ["h264_nvenc", "hevc_nvenc", "h264_vaapi", "hevc_vaapi", "h264_qsv", "hevc_qsv", "h264_amf", "hevc_amf"]
    available = []
    output = _run_ffmpeg_list(["-encoders"])
    for encoder in encoders:
        if encoder in output:
            available.append(encoder)
    return available
