from __future__ import annotations

import subprocess
import wave
from pathlib import Path
from typing import Any


def extract_analysis_audio(
    video_path: Path,
    output_path: Path,
) -> Path:

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video tidak ditemukan: {video_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    return output_path


def calculate_rms(
    samples: list[int],
) -> float:

    if not samples:
        return 0.0

    total = sum(
        sample * sample
        for sample in samples
    )

    mean = total / len(samples)

    return mean ** 0.5


def analyze_audio(
    audio_path: Path,
    window_seconds: float = 2.0,
) -> dict[str, Any]:

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio tidak ditemukan: {audio_path}"
        )

    with wave.open(
        str(audio_path),
        "rb",
    ) as wav:

        sample_rate = wav.getframerate()
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        total_frames = wav.getnframes()

        duration = (
            total_frames / sample_rate
            if sample_rate
            else 0
        )

        samples_per_window = int(
            sample_rate * window_seconds
        )

        windows = []

        current_time = 0.0

        while current_time < duration:

            frame_count = min(
                samples_per_window,
                total_frames
                - int(
                    current_time
                    * sample_rate
                ),
            )

            if frame_count <= 0:
                break

            raw_data = wav.readframes(
                frame_count
            )

            if sample_width == 2:
                import struct

                samples = struct.unpack(
                    f"<{len(raw_data) // 2}h",
                    raw_data,
                )

            else:
                samples = []

            rms = calculate_rms(
                list(samples)
            )

            windows.append(
                {
                    "start": current_time,
                    "end": min(
                        current_time
                        + window_seconds,
                        duration,
                    ),
                    "rms": rms,
                }
            )

            current_time += (
                window_seconds
            )

    if not windows:
        return {
            "duration": duration,
            "windows": [],
        }

    max_rms = max(
        window["rms"]
        for window in windows
    )

    min_rms = min(
        window["rms"]
        for window in windows
    )

    range_rms = (
        max_rms - min_rms
    )

    for window in windows:

        if range_rms > 0:
            normalized = (
                (
                    window["rms"]
                    - min_rms
                )
                / range_rms
            ) * 100

        else:
            normalized = 50

        window["energy_score"] = round(
            max(
                0,
                min(
                    100,
                    normalized,
                ),
            ),
            2,
        )

    return {
        "duration": duration,
        "sample_rate": sample_rate,
        "channels": channels,
        "windows": windows,
    }
