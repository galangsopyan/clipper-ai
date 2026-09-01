from pathlib import Path

from app.services.video_analyzer import (
    analyze_video,
)


VIDEO_PATH = Path(
    "media/input/Tiba tiba cinta datang cover.mp4"
)


def main():
    print("=" * 60)
    print("CLIPFORGE AI - VIDEO ANALYZER")
    print("=" * 60)
    print()

    try:
        result = analyze_video(
            VIDEO_PATH
        )

        print("VIDEO INFORMATION")
        print("-" * 60)

        print(
            f"Filename     : "
            f"{result['filename']}"
        )

        print(
            f"Duration     : "
            f"{result['duration']:.2f} seconds"
        )

        print(
            f"Resolution   : "
            f"{result['width']}x"
            f"{result['height']}"
        )

        print(
            f"FPS          : "
            f"{result['fps']:.2f}"
        )

        print(
            f"Video Codec  : "
            f"{result['video_codec']}"
        )

        print(
            f"Audio Codec  : "
            f"{result['audio_codec']}"
        )

        print(
            f"Has Audio    : "
            f"{result['has_audio']}"
        )

        print(
            f"Format       : "
            f"{result['format']}"
        )

        print()
        print("=" * 60)
        print("VIDEO ANALYSIS BERHASIL")
        print("=" * 60)

    except Exception as error:
        print()
        print("=" * 60)
        print("ERROR")
        print("=" * 60)
        print(
            type(error).__name__,
            ":",
            error,
        )


if __name__ == "__main__":
    main()