from pathlib import Path
import json

from app.services.clip_generator import find_video
from app.services.vertical_renderer import (
    get_segments,
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
        )

    # --------------------------------------------------------
    # SUPPORT:
    # [
    #   {...},
    #   {...}
    # ]
    #
    # atau:
    #
    # {
    #   "clips": [...]
    # }
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

    valid_clips.sort(
        key=lambda item: int(
            item.get(
                "rank",
                999,
            )
        )
    )

    return valid_clips[:MAX_CLIPS]


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "CLIPFORGE AI - 9:16 + SUBTITLE RENDERER"
    )
    print("=" * 70)

    # ========================================================
    # CHECK TRANSCRIPT
    # ========================================================

    if not TRANSCRIPT_FILE.exists():

        raise FileNotFoundError(
            "Transcript tidak ditemukan:\n"
            f"{TRANSCRIPT_FILE}"
        )

    # ========================================================
    # CHECK CLIPS.JSON
    # ========================================================

    top_clips = load_top_clips()

    print()
    print(
        f"[OK] {len(top_clips)} clip ditemukan "
        f"dari clips.json."
    )

    print()
    print("=" * 70)
    print("TOP CLIPS DARI clips.json")
    print("=" * 70)

    for clip in top_clips:

        print(
            f"#{clip.get('rank')} "
            f"| "
            f"{clip['start']:.2f}s → "
            f"{clip['end']:.2f}s "
            f"| "
            f"score={float(clip.get('score', 0)):.2f}"
        )

    # ========================================================
    # FIND VIDEO
    # ========================================================

    video = find_video()

    print()
    print(
        f"Video      : {video}"
    )

    print(
        f"Transcript : {TRANSCRIPT_FILE}"
    )

    print(
        f"Clips JSON : {CLIPS_FILE}"
    )

    # ========================================================
    # OUTPUT DIRECTORY
    # ========================================================

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

    # ========================================================
    # RENDER TOP 5
    # ========================================================

    print()
    print("=" * 70)
    print("RENDERING TOP 5")
    print("=" * 70)

    rendered = []

    for position, candidate in enumerate(
        top_clips,
        start=1,
    ):

        rank = int(
            candidate.get(
                "rank",
                position,
            )
        )

        start = float(
            candidate["start"]
        )

        end = float(
            candidate["end"]
        )

        score = float(
            candidate.get(
                "score",
                0,
            )
        )

        print()
        print("=" * 70)
        print(
            f"[{position}/{len(top_clips)}] "
            f"CLIP #{rank}"
        )
        print("=" * 70)

        print(
            f"Start : {start:.2f}s"
        )

        print(
            f"End   : {end:.2f}s"
        )

        print(
            f"Score : {score:.2f}"
        )

        # ====================================================
        # GET TRANSCRIPT SEGMENTS
        # ====================================================

        segments = get_segments(
            TRANSCRIPT_FILE,
            start,
            end,
        )

        print(
            f"Subtitle segments: "
            f"{len(segments)}"
        )

        # ====================================================
        # STRICT CHECK
        # ====================================================

        if not segments:

            raise RuntimeError(
                f"\n"
                f"❌ CLIP #{rank} TIDAK MEMILIKI TRANSCRIPT.\n\n"
                f"Time clip:\n"
                f"{start:.2f}s → {end:.2f}s\n\n"
                f"Artinya transcript JSON tidak memiliki "
                f"segment yang overlap dengan waktu tersebut.\n\n"
                f"Periksa:\n"
                f"- Podcast_transcript.json\n"
                f"- start/end clips.json\n"
            )

        # ====================================================
        # SUBTITLE FILE
        # ====================================================

        subtitle_file = (
            subtitle_dir
            / f"clip_{rank:02d}.ass"
        )

        # ====================================================
        # OUTPUT VIDEO
        # ====================================================

        output_file = (
            OUTPUT_DIR
            / f"clip_{rank:02d}_vertical.mp4"
        )

        # ====================================================
        # CREATE ASS
        # ====================================================

        create_ass_subtitle(
            segments,
            subtitle_file,
            start,
        )

        print(
            f"Subtitle created: "
            f"{subtitle_file.name}"
        )

        # ====================================================
        # RENDER
        # ====================================================

        render_vertical_clip(
            video,
            output_file,
            subtitle_file,
            start,
            end,
        )

        # ====================================================
        # VERIFY OUTPUT
        # ====================================================

        if not output_file.exists():

            raise RuntimeError(
                f"Video clip #{rank} "
                f"tidak berhasil dibuat."
            )

        size = output_file.stat().st_size

        if size <= 1000:

            raise RuntimeError(
                f"Video clip #{rank} "
                f"hasil render terlalu kecil."
            )

        print(
            f"✓ CREATED: "
            f"{output_file}"
        )

        rendered.append(rank)

    # ========================================================
    # FINAL
    # ========================================================

    print()
    print("=" * 70)
    print("🔥 9:16 + SUBTITLE SELESAI")
    print("=" * 70)

    print()
    print(
        f"Berhasil render: "
        f"{len(rendered)}/{len(top_clips)}"
    )

    print()
    print("Output:")

    for rank in rendered:

        file = (
            OUTPUT_DIR
            / f"clip_{rank:02d}_vertical.mp4"
        )

        print(
            f"✓ {file}"
        )

    print()
    print(
        "✓ SEMUA TOP CLIP BERHASIL DI-RENDER"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()