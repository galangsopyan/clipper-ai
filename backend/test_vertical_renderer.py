from pathlib import Path
import json

from app.services.clip_generator import find_video
from app.services.vertical_renderer import (
    get_segments,
    get_words,
    create_ass_subtitle,
    render_vertical_clip,
)


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MEDIA_DIR = BASE_DIR / "media"

TRANSCRIPT_FILE = (
    MEDIA_DIR
    / "cache"
    / "Podcast_transcript.json"
)

OUTPUT_DIR = (
    MEDIA_DIR
    / "output"
)

CLIPS_FILE = (
    OUTPUT_DIR
    / "clips.json"
)

MAX_CLIPS = 5


# ============================================================
# LOAD CLIPS.JSON
# ============================================================

def load_top_clips():
    """
    Membaca clips.json dan mengambil maksimal 5 clip terbaik.
    Mendukung format:
    
    [
        {...},
        {...}
    ]

    atau:

    {
        "clips": [...]
    }

    atau:

    {
        "results": [...]
    }
    """

    if not CLIPS_FILE.exists():
        raise FileNotFoundError(
            f"clips.json tidak ditemukan:\n"
            f"{CLIPS_FILE}"
        )

    try:
        with CLIPS_FILE.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

    except Exception as e:
        raise RuntimeError(
            f"Gagal membaca clips.json:\n{e}"
        ) from e

    # --------------------------------------------------------
    # SUPPORT MULTIPLE FORMAT
    # --------------------------------------------------------

    if isinstance(data, list):

        clips = data

    elif isinstance(data, dict):

        clips = data.get(
            "clips",
            data.get(
                "results",
                [],
            ),
        )

    else:

        clips = []

    if not isinstance(clips, list):

        raise RuntimeError(
            "Format clips.json tidak valid."
        )

    # --------------------------------------------------------
    # VALIDATE CLIPS
    # --------------------------------------------------------

    valid_clips = []

    for clip in clips:

        if not isinstance(clip, dict):
            continue

        if (
            "start" not in clip
            or "end" not in clip
        ):
            continue

        try:

            start = float(
                clip["start"]
            )

            end = float(
                clip["end"]
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

        if end <= start:
            continue

        valid_clips.append(
            {
                **clip,
                "start": start,
                "end": end,
            }
        )

    if not valid_clips:

        raise RuntimeError(
            "Tidak ada clip valid di clips.json."
        )

    # --------------------------------------------------------
    # SORT BY RANK
    # --------------------------------------------------------

    def get_rank(item):

        try:
            return int(
                item.get(
                    "rank",
                    999,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            return 999

    valid_clips.sort(
        key=get_rank
    )

    return valid_clips[:MAX_CLIPS]


# ============================================================
# CHECK FILE
# ============================================================

def check_file(
    file_path: Path,
    label: str,
):
    """
    Validasi file.
    """

    if not file_path.exists():

        raise FileNotFoundError(
            f"{label} tidak ditemukan:\n"
            f"{file_path}"
        )

    if file_path.stat().st_size <= 0:

        raise RuntimeError(
            f"{label} kosong:\n"
            f"{file_path}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print(
        "CLIPFORGE AI"
    )
    print(
        "9:16 + WORD-BY-WORD SUBTITLE RENDERER"
    )
    print("=" * 70)

    # ========================================================
    # CHECK TRANSCRIPT
    # ========================================================

    print()
    print(
        "[1/6] Checking transcript..."
    )

    check_file(
        TRANSCRIPT_FILE,
        "Transcript",
    )

    print(
        f"✓ Transcript OK"
    )

    print(
        f"  {TRANSCRIPT_FILE}"
    )

    # ========================================================
    # CHECK CLIPS.JSON
    # ========================================================

    print()
    print(
        "[2/6] Loading clips.json..."
    )

    top_clips = load_top_clips()

    print(
        f"✓ {len(top_clips)} clip ditemukan."
    )

    # ========================================================
    # SHOW CLIPS
    # ========================================================

    print()
    print("=" * 70)
    print("TOP CLIPS")
    print("=" * 70)

    for position, clip in enumerate(
        top_clips,
        start=1,
    ):

        rank = clip.get(
            "rank",
            position,
        )

        start = clip["start"]
        end = clip["end"]

        duration = end - start

        score = float(
            clip.get(
                "score",
                0,
            )
        )

        print(
            f"#{rank:<3} "
            f"{start:>8.2f}s → "
            f"{end:>8.2f}s "
            f"| "
            f"{duration:>6.2f}s "
            f"| "
            f"score={score:.2f}"
        )

    # ========================================================
    # FIND VIDEO
    # ========================================================

    print()
    print(
        "[3/6] Finding input video..."
    )

    video = find_video()

    if not video:

        raise RuntimeError(
            "Video input tidak ditemukan."
        )

    video = Path(video)

    check_file(
        video,
        "Video input",
    )

    print(
        f"✓ Video ditemukan:"
    )

    print(
        f"  {video}"
    )

    # ========================================================
    # CREATE OUTPUT DIRECTORIES
    # ========================================================

    print()
    print(
        "[4/6] Preparing output directories..."
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    subtitle_dir = (
        OUTPUT_DIR
        / "subtitles"
    )

    subtitle_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        f"✓ Output directory:"
    )

    print(
        f"  {OUTPUT_DIR}"
    )

    print(
        f"✓ Subtitle directory:"
    )

    print(
        f"  {subtitle_dir}"
    )

    # ========================================================
    # RENDER
    # ========================================================

    print()
    print(
        "[5/6] Rendering clips..."
    )

    rendered = []

    for position, candidate in enumerate(
        top_clips,
        start=1,
    ):

        # ----------------------------------------------------
        # BASIC DATA
        # ----------------------------------------------------

        try:

            rank = int(
                candidate.get(
                    "rank",
                    position,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            rank = position

        start = float(
            candidate["start"]
        )

        end = float(
            candidate["end"]
        )

        duration = end - start

        score = float(
            candidate.get(
                "score",
                0,
            )
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        print()
        print("=" * 70)

        print(
            f"[{position}/{len(top_clips)}] "
            f"RENDER CLIP #{rank}"
        )

        print("=" * 70)

        print(
            f"Start    : {start:.2f}s"
        )

        print(
            f"End      : {end:.2f}s"
        )

        print(
            f"Duration : {duration:.2f}s"
        )

        print(
            f"Score    : {score:.2f}"
        )

        # ----------------------------------------------------
        # VALIDATE TIME
        # ----------------------------------------------------

        if duration <= 0:

            raise RuntimeError(
                f"Clip #{rank} memiliki duration invalid."
            )

        # ----------------------------------------------------
        # WORD TIMESTAMPS
        # ----------------------------------------------------

        print()
        print(
            "Checking word timestamps..."
        )

        words = get_words(
            TRANSCRIPT_FILE,
            start,
            end,
        )

        print(
            f"Word timestamps: "
            f"{len(words)}"
        )

        # ----------------------------------------------------
        # SEGMENT FALLBACK
        # ----------------------------------------------------

        segments = get_segments(
            TRANSCRIPT_FILE,
            start,
            end,
        )

        print(
            f"Transcript segments: "
            f"{len(segments)}"
        )

        # ----------------------------------------------------
        # STRICT TRANSCRIPT CHECK
        # ----------------------------------------------------

        if not words and not segments:

            raise RuntimeError(
                f"\n"
                f"CLIP #{rank} TIDAK MEMILIKI TRANSCRIPT.\n\n"
                f"Time:\n"
                f"{start:.2f}s → {end:.2f}s\n\n"
                f"Periksa:\n"
                f"- {TRANSCRIPT_FILE}\n"
                f"- {CLIPS_FILE}\n"
                f"- start/end clip\n"
            )

        # ----------------------------------------------------
        # WORD TIMESTAMP PREVIEW
        # ----------------------------------------------------

        if words:

            print()
            print(
                "✓ WORD-LEVEL TIMESTAMP AKTIF"
            )

            print(
                "Preview:"
            )

            for word in words[:8]:

                print(
                    f"  "
                    f"{word['start']:.2f}s → "
                    f"{word['end']:.2f}s "
                    f"| "
                    f"{word['word']}"
                )

        else:

            print()
            print(
                "⚠ WORD-LEVEL TIMESTAMP TIDAK TERSEDIA"
            )

            print(
                "  Menggunakan segment-level subtitle."
            )

        # ----------------------------------------------------
        # FILE PATHS
        # ----------------------------------------------------

        subtitle_file = (
            subtitle_dir
            / f"clip_{rank:02d}.ass"
        )

        output_file = (
            OUTPUT_DIR
            / f"clip_{rank:02d}_vertical.mp4"
        )

        # ----------------------------------------------------
        # REMOVE OLD FILES
        # ----------------------------------------------------

        if subtitle_file.exists():

            print()
            print(
                f"Removing old subtitle:"
            )

            print(
                f"  {subtitle_file.name}"
            )

            try:

                subtitle_file.unlink()

            except OSError as e:

                raise RuntimeError(
                    f"Gagal menghapus subtitle lama:\n"
                    f"{subtitle_file}\n"
                    f"{e}"
                ) from e

        if output_file.exists():

            print()
            print(
                f"Removing old video:"
            )

            print(
                f"  {output_file.name}"
            )

            try:

                output_file.unlink()

            except OSError as e:

                raise RuntimeError(
                    f"Gagal menghapus video lama:\n"
                    f"{output_file}\n"
                    f"{e}"
                ) from e

        # ----------------------------------------------------
        # CREATE ASS
        # ----------------------------------------------------

        print()
        print(
            "Creating ASS subtitle..."
        )

        create_ass_subtitle(
            TRANSCRIPT_FILE,
            subtitle_file,
            start,
            end,
        )

        # ----------------------------------------------------
        # VERIFY ASS
        # ----------------------------------------------------

        check_file(
            subtitle_file,
            "ASS subtitle",
        )

        subtitle_size = (
            subtitle_file.stat().st_size
        )

        print(
            f"✓ Subtitle created:"
        )

        print(
            f"  {subtitle_file}"
        )

        print(
            f"  Size: "
            f"{subtitle_size / 1024:.2f} KB"
        )

        # ----------------------------------------------------
        # RENDER VIDEO
        # ----------------------------------------------------

        print()
        print(
            "Rendering 1080x1920 video..."
        )

        render_vertical_clip(
            video,
            output_file,
            subtitle_file,
            start,
            end,
        )

        # ----------------------------------------------------
        # VERIFY VIDEO
        # ----------------------------------------------------

        check_file(
            output_file,
            "Rendered video",
        )

        output_size = (
            output_file.stat().st_size
        )

        if output_size <= 1000:

            raise RuntimeError(
                f"Video clip #{rank} "
                f"hasil render terlalu kecil."
            )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        print()
        print(
            "✓ CLIP BERHASIL"
        )

        print(
            f"  Video    : {output_file.name}"
        )

        print(
            f"  Subtitle : {subtitle_file.name}"
        )

        print(
            f"  Size     : "
            f"{output_size / (1024 * 1024):.2f} MB"
        )

        rendered.append(
            {
                "rank": rank,
                "start": start,
                "end": end,
                "duration": duration,
                "score": score,
                "video": output_file,
                "subtitle": subtitle_file,
            }
        )

    # ========================================================
    # FINAL
    # ========================================================

    print()
    print("=" * 70)
    print(
        "[6/6] FINAL RESULT"
    )
    print("=" * 70)

    print()

    print(
        f"Berhasil render: "
        f"{len(rendered)}/{len(top_clips)}"
    )

    print()

    if rendered:

        print(
            "VIDEO OUTPUT:"
        )

        for item in rendered:

            print(
                f"✓ Clip #{item['rank']}"
            )

            print(
                f"  {item['video']}"
            )

    print()

    if len(rendered) == len(top_clips):

        print("=" * 70)
        print(
            "🔥 SEMUA TOP CLIP BERHASIL DI-RENDER"
        )
        print("=" * 70)

    else:

        print("=" * 70)
        print(
            "⚠ ADA CLIP YANG GAGAL DI-RENDER"
        )
        print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()