from pathlib import Path

from app.services.transcription import (
    transcribe_audio,
)

from app.services.audio_analyzer import (
    analyze_audio,
)

from app.services.visual_analyzer import (
    analyze_visual,
)

from app.services.viral_engine import (
    detect_viral_candidates,
)


VIDEO_PATH = Path(
    "media/input/Tiba tiba cinta datang cover.mp4"
)

AUDIO_PATH = Path(
    "media/audio/analysis.wav"
)


def main():

    print("=" * 60)
    print("CLIPFORGE AI - VIRAL ENGINE V3")
    print("=" * 60)
    print()

    # --------------------------------------------------
    # WHISPER
    # --------------------------------------------------

    print("1/3 Transcribing audio...")
    print()

    transcript = transcribe_audio(
        AUDIO_PATH
    )

    print(
        "✓ Whisper transcription complete."
    )
    print()

    # --------------------------------------------------
    # AUDIO
    # --------------------------------------------------

    print("2/3 Analyzing audio...")

    audio = analyze_audio(
        AUDIO_PATH,
        window_seconds=2.0,
    )

    print(
        "✓ Audio analysis complete."
    )
    print()

    # --------------------------------------------------
    # VISUAL
    # --------------------------------------------------

    print("3/3 Analyzing visual...")

    visual = analyze_visual(
        VIDEO_PATH,
        interval=2.0,
    )

    print(
        "✓ Visual analysis complete."
    )
    print()

    # --------------------------------------------------
    # VIRAL ENGINE
    # --------------------------------------------------

    print(
        "Running Viral Engine V3..."
    )

    candidates = detect_viral_candidates(
        transcript=transcript,
        audio=audio,
        visual=visual,
        video_duration=116.82,
        min_duration=20,
        max_duration=45,
        max_results=5,
    )

    print()

    print("=" * 60)
    print("🔥 VIRAL CANDIDATES")
    print("=" * 60)

    if not candidates:

        print(
            "Tidak ditemukan kandidat viral."
        )

        return

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):

        print()

        print(
            f"#{index} 🔥 "
            f"VIRAL SCORE: "
            f"{candidate.score}/100"
        )

        print(
            f"Time: "
            f"{candidate.start:.2f}s"
            f" → "
            f"{candidate.end:.2f}s"
        )

        print(
            f"Duration: "
            f"{candidate.duration:.2f}s"
        )

        print()

        print(
            f"Audio      : "
            f"{candidate.audio_score:.2f}/100"
        )

        print(
            f"Visual     : "
            f"{candidate.visual_score:.2f}/100"
        )

        print(
            f"Transcript : "
            f"{candidate.transcript_score:.2f}/100"
        )

        print(
            f"Duration   : "
            f"{candidate.duration_score:.2f}/100"
        )

        print()

        print(
            f"Title: "
            f"{candidate.title}"
        )

        print()

        print(
            f"Transcript:"
        )

        if candidate.transcript:

            print(
                candidate.transcript
            )

        else:

            print(
                "(Tidak ada transcript)"
            )

        print()

        print(
            f"Reason: "
            f"{candidate.reason}"
        )

        print("-" * 60)

    print()
    print("=" * 60)
    print("🔥 VIRAL ENGINE V3 SELESAI")
    print("=" * 60)


if __name__ == "__main__":
    main()