from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def analyze_video(video_path: Path) -> dict[str, Any]:
    """
    Menganalisis metadata dasar video menggunakan FFprobe.
    """

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video tidak ditemukan: {video_path}"
        )

    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)

    video_stream = None
    audio_stream = None

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            video_stream = stream

        elif stream.get("codec_type") == "audio":
            audio_stream = stream

    if video_stream is None:
        raise RuntimeError(
            "Video stream tidak ditemukan."
        )

    duration = float(
        data.get("format", {}).get(
            "duration",
            0,
        )
    )

    width = int(
        video_stream.get("width", 0)
    )

    height = int(
        video_stream.get("height", 0)
    )

    fps_raw = video_stream.get(
        "r_frame_rate",
        "0/1",
    )

    try:
        numerator, denominator = fps_raw.split("/")
        fps = float(numerator) / float(denominator)

    except (ValueError, ZeroDivisionError):
        fps = 0.0

    return {
        "path": str(video_path),
        "filename": video_path.name,
        "duration": duration,
        "width": width,
        "height": height,
        "fps": fps,
        "has_audio": audio_stream is not None,
        "video_codec": video_stream.get(
            "codec_name"
        ),
        "audio_codec": (
            audio_stream.get("codec_name")
            if audio_stream
            else None
        ),
        "format": data.get("format", {}).get(
            "format_name"
        ),
    }