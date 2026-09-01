from __future__ import annotations

import math
import subprocess
from pathlib import Path
from typing import Any


def extract_frame_signatures(
    video_path: Path,
    interval: float = 2.0,
) -> list[dict[str, Any]]:
    """
    Mengambil brightness dan perubahan visual sederhana
    dari frame video menggunakan FFmpeg.

    Tidak membutuhkan OpenCV.
    """

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video tidak ditemukan: {video_path}"
        )

    # Format gray 1x1.
    # Nilai pixel yang dihasilkan mewakili brightness
    # rata-rata frame yang di-sampling.
    vf = (
        f"fps=1/{interval},"
        "scale=1:1,"
        "format=gray"
    )

    command = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(video_path),
        "-vf",
        vf,
        "-f",
        "rawvideo",
        "-pix_fmt",
        "gray",
        "pipe:1",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        check=True,
    )

    raw = result.stdout

    frames: list[dict[str, Any]] = []

    for index, byte_value in enumerate(raw):
        timestamp = index * interval

        frames.append(
            {
                "time": round(timestamp, 2),
                "brightness": int(byte_value),
            }
        )

    return frames


def calculate_visual_changes(
    frames: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Menghitung perubahan brightness antar frame.

    Ini adalah pendekatan lightweight untuk mendeteksi
    perubahan visual. Nantinya dapat ditingkatkan menjadi
    scene detection berbasis computer vision.
    """

    if not frames:
        return []

    changes = []

    previous = None

    for frame in frames:
        brightness = float(
            frame["brightness"]
        )

        if previous is None:
            change = 0.0
        else:
            change = abs(
                brightness - previous
            )

        changes.append(
            {
                "time": frame["time"],
                "brightness": brightness,
                "change": round(
                    change,
                    2,
                ),
            }
        )

        previous = brightness

    max_change = max(
        item["change"]
        for item in changes
    )

    for item in changes:

        if max_change > 0:
            score = (
                item["change"]
                / max_change
            ) * 100
        else:
            score = 0

        item["visual_score"] = round(
            max(
                0,
                min(100, score),
            ),
            2,
        )

    return changes


def analyze_visual(
    video_path: Path,
    interval: float = 2.0,
) -> dict[str, Any]:
    """
    Pipeline visual analysis.
    """

    frames = extract_frame_signatures(
        video_path,
        interval=interval,
    )

    changes = calculate_visual_changes(
        frames
    )

    return {
        "interval": interval,
        "frame_count": len(frames),
        "changes": changes,
    }