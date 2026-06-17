from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable


def run_ffmpeg_command(command: Iterable[str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        list(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
    )


def monitor_process(process: subprocess.Popen[bytes]) -> Iterable[str]:
    assert process.stderr is not None
    while True:
        line = process.stderr.readline()
        if not line:
            break
        yield line.decode("utf-8", errors="replace").rstrip("\n")
