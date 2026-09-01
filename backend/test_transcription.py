from pathlib import Path

from app.services.transcription import transcribe_audio


AUDIO_PATH = Path(
    "media/audio/tiba-tiba-cinta.wav"
)


def format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)

    return f"{minutes:02d}:{secs:02d}"


def main():
    print("=" * 60)
    print("CLIPFORGE AI - LOCAL WHISPER TEST")
    print("=" * 60)
    print()

    if not AUDIO_PATH.exists():
        print(
            f"ERROR: Audio tidak ditemukan:\n"
            f"{AUDIO_PATH}"
        )
        return

    print(f"Audio: {AUDIO_PATH}")
    print()
    print("Transkripsi menggunakan Local Whisper...")
    print("Pertama kali mungkin membutuhkan waktu karena")
    print("model Whisper akan di-download.")
    print()

    try:
        result = transcribe_audio(AUDIO_PATH)

        print()
        print("=" * 60)
        print("TRANSCRIPTION BERHASIL")
        print("=" * 60)
        print()

        print("Language:", result["language"])
        print(
            "Language probability:",
            f"{result['language_probability']:.2%}",
        )

        print()
        print("FULL TEXT:")
        print("-" * 60)
        print(result["text"])

        print()
        print("=" * 60)
        print("TIMESTAMP SEGMENTS")
        print("=" * 60)

        for segment in result["segments"]:
            start = format_time(segment["start"])
            end = format_time(segment["end"])

            print(
                f"[{start} - {end}] "
                f"{segment['text']}"
            )

    except Exception as error:
        print()
        print("=" * 60)
        print("TRANSCRIPTION ERROR")
        print("=" * 60)
        print()
        print(type(error).__name__)
        print(str(error))


if __name__ == "__main__":
    main()