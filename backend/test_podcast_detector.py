from pathlib import Path

from app.services.transcription import (
    transcribe_audio,
)

from app.services.audio_analyzer import (
    analyze_audio,
)

from app.services.podcast_detector import (
    detect_podcast_moments,
)


INPUT_DIR = Path("media/input")
AUDIO_DIR = Path("media/audio")


def find_video() -> Path:

    extensions = [
        ".mp4",
        ".mov",
        ".mkv",
        ".avi",
        ".webm",
    ]

    videos = [
        file
        for file in INPUT_DIR.iterdir()
        if file.is_file()
        and file.suffix.lower() in extensions
    ]

    if not videos:
        raise FileNotFoundError(
            "Tidak ada video di media/input"
        )

    # Ambil file terbaru
    videos.sort(
        key=lambda file: file.stat().st_mtime,
        reverse=True,
    )

    return videos[0]


def main():

    print("=" * 60)
    print("CLIPFORGE AI - PODCAST VIRAL DETECTOR")
    print("=" * 60)
    print()

    video_path = find_video()

    print(
        f"VIDEO : {video_path.name}"
    )

    print()

    print(
        "Video ditemukan."
    )

    print()

    print("=" * 60)
    print("STEP 1 - EXTRACT AUDIO")
    print("=" * 60)

    AUDIO_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    audio_path = (
        AUDIO_DIR
        / f"{video_path.stem}.wav"
    )

    import subprocess

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
        str(audio_path),
    ]

    subprocess.run(
        command,
        check=True,
    )

    print()
    print(
        f"✓ Audio created: {audio_path}"
    )

    print()

    print("=" * 60)
    print("STEP 2 - WHISPER TRANSCRIPTION")
    print("=" * 60)
    print()

    transcript = transcribe_audio(
        audio_path
    )

    print()
    print(
        "✓ Transcription complete."
    )

    print()

    print("=" * 60)
    print("STEP 3 - AUDIO ANALYSIS")
    print("=" * 60)
    print()

    audio = analyze_audio(
        audio_path,
        window_seconds=2.0,
    )

    print(
        "✓ Audio analysis complete."
    )

    print()

    print("=" * 60)
    print("STEP 4 - PODCAST VIRAL DETECTOR")
    print("=" * 60)
    print()

    moments = detect_podcast_moments(
        transcript=transcript,
        audio=audio,
        min_duration=15,
        max_duration=40,
        max_results=5,
    )

    print()

    print("=" * 60)
    print("🔥 TOP PODCAST MOMENTS")
    print("=" * 60)

    if not moments:

        print()
        print(
            "Tidak ditemukan kandidat podcast."
        )

        return

    for index, moment in enumerate(
        moments,
        start=1,
    ):

        print()

        print(
            f"#{index} {moment.category}"
        )

        print(
            f"🔥 VIRAL SCORE : "
            f"{moment.score}/100"
        )

        print(
            f"TIME          : "
            f"{moment.start:.2f}s "
            f"→ "
            f"{moment.end:.2f}s"
        )

        print(
            f"DURATION      : "
            f"{moment.duration:.2f}s"
        )

        print()

        print(
            f"Hook          : "
            f"{moment.hook_score:.2f}/100"
        )

        print(
            f"Insight       : "
            f"{moment.insight_score:.2f}/100"
        )

        print(
            f"Emotion       : "
            f"{moment.emotion_score:.2f}/100"
        )

        print(
            f"Story         : "
            f"{moment.story_score:.2f}/100"
        )

        print(
            f"Curiosity     : "
            f"{moment.curiosity_score:.2f}/100"
        )

        print(
            f"Audio         : "
            f"{moment.audio_score:.2f}/100"
        )

        print()

        print("TITLE:")
        print(
            moment.title
        )

        print()

        print("TRANSCRIPT:")
        print(
            moment.transcript
        )

        print()

        print("REASON:")
        print(
            moment.reason
        )

        print("-" * 60)

    print()

    print("=" * 60)
    print("🔥 PODCAST DETECTOR SELESAI")
    print("=" * 60)


if __name__ == "__main__":
    main()