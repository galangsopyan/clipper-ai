from pathlib import Path

from app.services.visual_analyzer import (
    analyze_visual,
)


VIDEO_PATH = Path(
    "media/input/Tiba tiba cinta datang cover.mp4"
)


def main():

    print("=" * 60)
    print("CLIPFORGE AI - VISUAL ANALYZER")
    print("=" * 60)
    print()

    try:

        print("Analyzing video frames...")
        print("Mohon tunggu...")
        print()

        result = analyze_visual(
            VIDEO_PATH,
            interval=2.0,
        )

        print("=" * 60)
        print("VISUAL ANALYSIS BERHASIL")
        print("=" * 60)
        print()

        print(
            f"Frame samples : "
            f"{result['frame_count']}"
        )

        print(
            f"Interval      : "
            f"{result['interval']} seconds"
        )

        print()
        print("TOP VISUAL CHANGES")
        print("-" * 60)

        top_changes = sorted(
            result["changes"],
            key=lambda item: item[
                "visual_score"
            ],
            reverse=True,
        )[:10]

        for index, item in enumerate(
            top_changes,
            start=1,
        ):

            print(
                f"#{index} "
                f"{item['time']:.2f}s "
                f"| Brightness: "
                f"{item['brightness']:.0f} "
                f"| Change: "
                f"{item['change']:.2f} "
                f"| Visual Score: "
                f"{item['visual_score']:.2f}/100"
            )

        print()
        print("=" * 60)
        print("VISUAL ANALYZER SELESAI")
        print("=" * 60)

    except Exception as error:

        print()
        print("=" * 60)
        print("VISUAL ANALYSIS ERROR")
        print("=" * 60)

        print(
            type(error).__name__,
            ":",
            error,
        )


if __name__ == "__main__":
    main()