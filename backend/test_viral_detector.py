from pathlib import Path

from app.services.transcription import (
    transcribe_audio,
)

from app.services.viral_detector import (
    detect_viral_moments,
)


AUDIO_PATH = Path(
    "media/audio/tiba-tiba-cinta.wav"
)


def main():
    print("=" * 60)
    print("CLIPFORGE AI - VIRAL DETECTOR")
    print("=" * 60)
    print()

    print("Transcribing audio...")

    transcript = transcribe_audio(
        AUDIO_PATH
    )

    print("Transcription complete.")
    print()

    moments = detect_viral_moments(
        transcript
    )

    if not moments:
        print(
            "Belum ditemukan viral moment."
        )
        return

    print("=" * 60)
    print("🔥 VIRAL MOMENTS")
    print("=" * 60)

    for index, moment in enumerate(
        moments,
        start=1,
    ):
        print()

        print(
            f"#{index} "
            f"Score: {moment.score}/100"
        )

        print(
            f"Time: "
            f"{moment.start:.2f}s → "
            f"{moment.end:.2f}s"
        )

        print(
            f"Title: {moment.title}"
        )

        print(
            f"Reason: {moment.reason}"
        )


if __name__ == "__main__":
    main()