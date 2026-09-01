from pathlib import Path
import json
import sys

# ============================================================
# WINDOWS UTF-8
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


from app.services.clip_generator import (
    find_video,
    clean_output,
    generate_clip,
    save_metadata,
)


# ============================================================
# PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CACHE_DIR = (
    BASE_DIR
    / "media"
    / "cache"
)

TRANSCRIPT_FILE = (
    CACHE_DIR
    / "Podcast_transcript.json"
)

VIRAL_RESULTS_FILE = (
    CACHE_DIR
    / "viral_candidates.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "media"
    / "output"
)

CLIPS_FILE = (
    OUTPUT_DIR
    / "clips.json"
)


# ============================================================
# CONFIG
# ============================================================

TOP_CLIPS = 5


# ============================================================
# FORMAT TIME
# ============================================================

def format_time(seconds: float) -> str:

    minutes = int(
        seconds // 60
    )

    secs = int(
        seconds % 60
    )

    return (
        f"{minutes:02d}:{secs:02d}"
    )


# ============================================================
# LOAD VIRAL RESULTS
# ============================================================

def load_viral_results():

    if not VIRAL_RESULTS_FILE.exists():

        raise FileNotFoundError(
            "Hasil Viral Engine tidak ditemukan:\n"
            f"{VIRAL_RESULTS_FILE}\n\n"
            "Pastikan test_viral_engine_v4.py "
            "dijalankan terlebih dahulu."
        )

    with VIRAL_RESULTS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    # --------------------------------------------------------
    # Format object
    # --------------------------------------------------------

    if isinstance(data, dict):

        candidates = data.get(
            "candidates",
            data.get(
                "top_5",
                [],
            ),
        )

    # --------------------------------------------------------
    # Format array
    # --------------------------------------------------------

    elif isinstance(data, list):

        candidates = data

    else:

        candidates = []

    if not isinstance(
        candidates,
        list,
    ):

        candidates = []

    # --------------------------------------------------------
    # Filter valid candidates
    # --------------------------------------------------------

    valid = []

    for candidate in candidates:

        if not isinstance(
            candidate,
            dict,
        ):
            continue

        try:

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

        except (
            KeyError,
            TypeError,
            ValueError,
        ):

            continue

        if end <= start:
            continue

        title = str(
            candidate.get(
                "title",
                "",
            )
        ).strip()

        if not title:

            title = (
                "Podcast Viral Moment"
            )

        item = dict(
            candidate
        )

        item["start"] = start
        item["end"] = end
        item["score"] = score
        item["duration"] = end - start
        item["title"] = title

        valid.append(item)

    # --------------------------------------------------------
    # Sort score
    # --------------------------------------------------------

    valid.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # --------------------------------------------------------
    # Select TOP 5
    # --------------------------------------------------------

    top_5 = valid[
        :TOP_CLIPS
    ]

    if len(top_5) < TOP_CLIPS:

        raise RuntimeError(
            "Viral Engine hanya menghasilkan "
            f"{len(top_5)} kandidat valid. "
            f"Dibutuhkan minimal {TOP_CLIPS}."
        )

    # --------------------------------------------------------
    # Re-rank
    # --------------------------------------------------------

    for index, candidate in enumerate(
        top_5,
        start=1,
    ):

        candidate["rank"] = index

    return top_5


# ============================================================
# SAVE CLIPS JSON
# ============================================================

def save_clips_json(generated):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "count": len(generated),

        "clips": generated,
    }

    with CLIPS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return CLIPS_FILE


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)

    print(
        "CLIPFORGE AI - TOP 5 CLIP GENERATOR"
    )

    print("=" * 70)

    # ========================================================
    # TRANSCRIPT CHECK
    # ========================================================

    if not TRANSCRIPT_FILE.exists():

        raise FileNotFoundError(
            "Transcript tidak ditemukan:\n"
            f"{TRANSCRIPT_FILE}"
        )

    print()

    print(
        "Transcript cache ditemukan."
    )

    print(
        TRANSCRIPT_FILE
    )

    # ========================================================
    # LOAD VIRAL ENGINE RESULTS
    # ========================================================

    print()

    print("=" * 70)

    print(
        "MEMBACA HASIL VIRAL ENGINE"
    )

    print("=" * 70)

    top_5 = load_viral_results()

    print()

    print(
        f"✓ {len(top_5)} kandidat TOP ditemukan."
    )

    # ========================================================
    # SHOW TOP 5
    # ========================================================

    for candidate in top_5:

        print()

        print(
            f"#{candidate['rank']}"
        )

        print(
            f"Score    : "
            f"{candidate['score']:.2f}"
        )

        print(
            f"Time     : "
            f"{format_time(candidate['start'])}"
            f" → "
            f"{format_time(candidate['end'])}"
        )

        print(
            f"Duration : "
            f"{candidate['duration']:.2f}s"
        )

        print(
            f"Category : "
            f"{candidate.get('category', 'VIRAL')}"
        )

        print(
            f"TITLE    : "
            f"{candidate['title']}"
        )

    # ========================================================
    # FIND VIDEO
    # ========================================================

    print()

    video = find_video()

    if not video.exists():

        raise FileNotFoundError(
            f"Video tidak ditemukan: {video}"
        )

    print(
        f"Video : {video.name}"
    )

    print(
        f"Output: {OUTPUT_DIR}"
    )

    # ========================================================
    # CLEAN OLD OUTPUT
    # ========================================================

    print()

    print("=" * 70)

    print(
        "Membersihkan output lama..."
    )

    print("=" * 70)

    clean_output()

    # ========================================================
    # GENERATE
    # ========================================================

    generated = []

    print()

    print("=" * 70)

    print(
        "GENERATING TOP 5 CLIPS"
    )

    print("=" * 70)

    for candidate in top_5:

        rank = candidate["rank"]

        start = candidate["start"]

        end = candidate["end"]

        duration = end - start

        output_file = (
            OUTPUT_DIR
            / f"clip_{rank:02d}.mp4"
        )

        print()

        print(
            f"[{rank}/5] Generating clip..."
        )

        print(
            f"Time     : "
            f"{format_time(start)} → "
            f"{format_time(end)}"
        )

        print(
            f"Duration : "
            f"{duration:.2f}s"
        )

        print(
            f"Score    : "
            f"{candidate['score']:.2f}"
        )

        print(
            f"Category : "
            f"{candidate.get('category', 'VIRAL')}"
        )

        print(
            f"TITLE    : "
            f"{candidate['title']}"
        )

        # ====================================================
        # GENERATE VIDEO
        # ====================================================

        generate_clip(
            video,
            output_file,
            start,
            end,
        )

        # ====================================================
        # VERIFY
        # ====================================================

        if not output_file.exists():

            raise RuntimeError(
                f"Clip #{rank} gagal dibuat:\n"
                f"{output_file}"
            )

        if output_file.stat().st_size <= 1000:

            raise RuntimeError(
                f"Clip #{rank} kosong/rusak:\n"
                f"{output_file}"
            )

        print(
            f"✓ CREATED: {output_file}"
        )

        # ====================================================
        # METADATA
        # ====================================================

        generated.append(
            {
                **candidate,

                "rank": rank,

                "duration": duration,

                "file": str(
                    output_file
                ),

                "filename": (
                    output_file.name
                ),

                "video": (
                    f"/media/output/"
                    f"clip_{rank:02d}.mp4"
                ),

                "exists": True,
            }
        )

    # ========================================================
    # SAVE METADATA THROUGH SERVICE
    # ========================================================

    try:

        metadata = save_metadata(
            generated
        )

        print()

        print(
            f"Metadata service: {metadata}"
        )

    except Exception as e:

        print(
            f"[WARNING] save_metadata gagal: {e}"
        )

    # ========================================================
    # FORCE SAVE clips.json
    # ========================================================

    clips_json = save_clips_json(
        generated
    )

    print()

    print(
        f"[OK] clips.json: {clips_json}"
    )

    # ========================================================
    # VERIFY 5
    # ========================================================

    if len(generated) != 5:

        raise RuntimeError(
            f"Hanya {len(generated)}/5 clip berhasil."
        )

    print()

    print("=" * 70)

    print(
        "🔥 TOP 5 CLIPS BERHASIL"
    )

    print("=" * 70)

    for item in generated:

        print()

        print(
            f"#{item['rank']} "
            f"| Score {item['score']:.2f}"
        )

        print(
            f"   {format_time(item['start'])}"
            f" → "
            f"{format_time(item['end'])}"
        )

        print(
            f"   TITLE: "
            f"{item['title']}"
        )

        print(
            f"   FILE: "
            f"{item['file']}"
        )

    print()

    print(
        f"✓ {len(generated)}/5 CLIPS GENERATED"
    )

    print(
        f"✓ Metadata: {clips_json}"
    )

    print()

    print(
        "✓ SELESAI"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()