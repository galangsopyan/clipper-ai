from pathlib import Path
import subprocess
import json


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_DIR = BASE_DIR / "media" / "input"
OUTPUT_DIR = BASE_DIR / "media" / "output"


def find_video() -> Path:
    videos = list(INPUT_DIR.glob("*.mp4"))

    if not videos:
        raise FileNotFoundError(
            f"Tidak ada video MP4 di {INPUT_DIR}"
        )

    # Prioritaskan Podcast.mp4
    for video in videos:
        if video.name.lower() == "podcast.mp4":
            return video

    return videos[0]


def clean_output():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for file in OUTPUT_DIR.glob("clip_*.mp4"):
        file.unlink()


def format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)

    return f"{minutes:02d}:{secs:02d}"


def generate_clip(
    input_video: Path,
    output_video: Path,
    start: float,
    end: float,
):
    duration = end - start

    command = [
        "ffmpeg",
        "-y",
        "-ss",
        str(start),
        "-i",
        str(input_video),
        "-t",
        str(duration),
        "-map",
        "0:v:0",
        "-map",
        "0:a:0",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(output_video),
    ]

    subprocess.run(
        command,
        check=True,
    )


def save_metadata(candidates):
    metadata_file = OUTPUT_DIR / "clips.json"

    with metadata_file.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            candidates,
            f,
            ensure_ascii=False,
            indent=2,
        )

    return metadata_file