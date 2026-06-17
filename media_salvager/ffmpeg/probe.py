from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _run_ffprobe(args: list[str]) -> tuple[int, str, str]:
    process = subprocess.run(["ffprobe", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return process.returncode, process.stdout.strip(), process.stderr.strip()


def ffmpeg_available() -> bool:
    try:
        process = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        probe = subprocess.run(["ffprobe", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return process.returncode == 0 and probe.returncode == 0
    except FileNotFoundError:
        return False


def probe_media(path: Path) -> dict[str, Any]:
    returncode, stdout, stderr = _run_ffprobe(["-v", "error", "-show_format", "-show_streams", "-print_format", "json", str(path)])
    if returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {stderr}")
    import json

    return json.loads(stdout)


def extract_stream_info(path: Path) -> dict[str, str]:
    info = probe_media(path)
    duration = info.get("format", {}).get("duration")
    video_streams = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    audio_streams = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    first_video = video_streams[0] if video_streams else {}
    width = first_video.get("width")
    height = first_video.get("height")
    codec = first_video.get("codec_name") or audio_streams[0].get("codec_name") if audio_streams else "unknown"
    return {
        "duration": f"{float(duration):.1f}s" if duration else "Unknown",
        "resolution": f"{width}x{height}" if width and height else "Unknown",
        "codec": codec or "Unknown",
    }
