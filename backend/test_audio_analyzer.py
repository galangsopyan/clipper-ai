from pathlib import Path

from app.services.audio_analyzer import (
    extract_analysis_audio,
    analyze_audio,
)


VIDEO_PATH = Path(
    "media/input/Tiba tiba cinta datang cover.mp4"
)

AUDIO_PATH = Path(
    "media/audio/analysis.wav"
)


def main():

    print("=" * 60)
    print("CLIPFORGE AI - AUDIO ANALYZER")
    print("=" * 60)
    print()

    try:

        print("Extracting audio...")

        extract_analysis_audio(
            VIDEO_PATH,
            AUDIO_PATH,
        )

        print(
            f"Audio created: {AUDIO_PATH}"
        )

        print()
        print("Analyzing audio energy...")

        result = analyze_audio(
            AUDIO_PATH,
            window_seconds=2.0,
        )

        print()
        print("=" * 60)
        print("AUDIO ANALYSIS BERHASIL")
        print("=" * 60)

        print()

        print(
            f"Duration: "
            f"{result['duration']:.2f}s"
        )

        print(
            f"Sample rate: "
            f"{result['sample_rate']} Hz"
        )

        print(
            f"Channels: "
            f"{result['channels']}"
        )

        print()
        print("TOP AUDIO ENERGY")
        print("-" * 60)

        top_windows = sorted(
            result["windows"],
            key=lambda item: item[
                "energy_score"
            ],
            reverse=True,
        )[:10]

        for index, window in enumerate(
            top_windows,
            start=1,
        ):

            print(
                f"#{index} "
                f"{window['start']:.2f}s → "
                f"{window['end']:.2f}s "
                f"| Energy: "
                f"{window['energy_score']:.2f}/100"
            )

        print()
        print("=" * 60)

    except Exception as error:

        print()
        print("=" * 60)
        print("AUDIO ANALYSIS ERROR")
        print("=" * 60)

        print(
            type(error).__name__,
            ":",
            error,
        )


if __name__ == "__main__":
    main()