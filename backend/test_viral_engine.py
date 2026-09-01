from pathlib import Path

from app.services.transcription import (
    transcribe_audio,
)

from app.services.audio_analyzer import (
    analyze_audio,
)

from app.services.viral_engine import (
    detect_candidates,
)


AUDIO_PATH = Path(
    "media/audio/analysis.wav"
)


def main():

    print("=" * 60)
    print("CLIPFORGE AI - VIRAL ENGINE V2")
    print("=" * 60)
    print()

    print("Loading Whisper transcription...")

    transcript = transcribe_audio(
        AUDIO_PATH
    )

    print("Transcription ready.")
    print()

    print("Loading audio analysis...")

    audio = analyze_audio(
        AUDIO_PATH,
        window_seconds=2.0,
    )

    print("Audio analysis ready.")
    print()

    print("Running Viral Engine...")

    candidates = detect_candidates(
        transcript,
        audio,
    )

    print()

    print("=" * 60)
    print("🔥 VIRAL CANDIDATES")
    print("=" * 60)

    if not candidates:
        print(
            "Tidak ditemukan kandidat."
        )
        return

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):

        print()
        print(
            f"#{index} "
            f"🔥 VIRAL SCORE: "
            f"{candidate.score}/100"
        )

        print(
            f"Time: "
            f"{candidate.start:.2f}s "
            f"→ "
            f"{candidate.end:.2f}s"
        )

        print(
            f"Duration: "
            f"{candidate.duration:.2f}s"
        )

        print()

        print(
            f"Audio Energy : "
            f"{candidate.audio_score:.2f}"
        )

        print(
            f"Transcript   : "
            f"{candidate.transcript_score:.2f}"
        )

        print(
            f"Duration     : "
            f"{candidate.duration_score:.2f}"
        )

        print()

        print(
            f"Title: "
            f"{candidate.title}"
        )

        print(
            f"Reason: "
            f"{candidate.reason}"
        )

    print()
    print("=" * 60)
    print("VIRAL ENGINE SELESAI")
    print("=" * 60)


if __name__ == "__main__":
    main()
