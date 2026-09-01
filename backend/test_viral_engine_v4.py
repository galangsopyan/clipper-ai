from pathlib import Path
import json
import sys

# ============================================================
# WINDOWS UTF-8 OUTPUT
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from app.services.viral_engine_v4 import analyze_podcast_v4


# ============================================================
# PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CACHE_DIR = BASE_DIR / "media" / "cache"

TRANSCRIPT_FILE = CACHE_DIR / "Podcast_transcript.json"

AUDIO_FILE = CACHE_DIR / "Podcast_audio.json"

VIRAL_RESULTS_FILE = CACHE_DIR / "viral_candidates.json"


# ============================================================
# FIND TRANSCRIPT
# ============================================================

def find_transcript():
    """
    Prioritaskan Podcast_transcript.json.
    Jika tidak ada, cari transcript terbaru.
    """

    if TRANSCRIPT_FILE.exists():
        return TRANSCRIPT_FILE

    files = list(
        CACHE_DIR.glob("*_transcript.json")
    )

    if not files:
        raise FileNotFoundError(
            "Transcript cache tidak ditemukan."
        )

    files.sort(
        key=lambda file: file.stat().st_mtime,
        reverse=True,
    )

    return files[0]


# ============================================================
# FIND AUDIO
# ============================================================

def find_audio():

    if AUDIO_FILE.exists():
        return AUDIO_FILE

    files = list(
        CACHE_DIR.glob("*_audio.json")
    )

    if not files:
        return None

    files.sort(
        key=lambda file: file.stat().st_mtime,
        reverse=True,
    )

    return files[0]


# ============================================================
# CONVERT CANDIDATE TO JSON
# ============================================================

def candidate_to_dict(candidate, rank):
    """
    Mengubah object candidate dari Viral Engine
    menjadi dictionary JSON yang stabil.
    """

    return {
        "rank": rank,

        "score": float(
            getattr(candidate, "score", 0)
        ),

        "start": float(
            getattr(candidate, "start", 0)
        ),

        "end": float(
            getattr(candidate, "end", 0)
        ),

        "duration": float(
            getattr(candidate, "duration", 0)
        ),

        "title": str(
            getattr(candidate, "title", "")
        ).strip(),

        "category": str(
            getattr(candidate, "category", "VIRAL")
        ).strip(),

        "hook_score": float(
            getattr(candidate, "hook_score", 0)
        ),

        "insight_score": float(
            getattr(candidate, "insight_score", 0)
        ),

        "emotion_score": float(
            getattr(candidate, "emotion_score", 0)
        ),

        "story_score": float(
            getattr(candidate, "story_score", 0)
        ),

        "curiosity_score": float(
            getattr(candidate, "curiosity_score", 0)
        ),

        "controversy_score": float(
            getattr(candidate, "controversy_score", 0)
        ),

        "punchline_score": float(
            getattr(candidate, "punchline_score", 0)
        ),

        "audio_score": float(
            getattr(candidate, "audio_score", 0)
        ),

        "duration_score": float(
            getattr(candidate, "duration_score", 0)
        ),

        "completeness_score": float(
            getattr(candidate, "completeness_score", 0)
        ),

        "transcript": str(
            getattr(candidate, "transcript", "")
        ).strip(),

        "reason": str(
            getattr(candidate, "reason", "")
        ).strip(),
    }


# ============================================================
# SAVE VIRAL RESULTS
# ============================================================

def save_viral_results(candidates):

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "count": len(candidates),

        "source": "viral_engine_v4",

        "top_5": candidates[:5],

        "candidates": candidates,
    }

    with VIRAL_RESULTS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(
        f"[OK] Viral results saved:"
    )

    print(
        VIRAL_RESULTS_FILE
    )

    return VIRAL_RESULTS_FILE


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)

    print(
        "CLIPFORGE AI - PODCAST VIRAL ENGINE V4"
    )

    print("=" * 70)

    print()

    # ========================================================
    # TRANSCRIPT
    # ========================================================

    transcript_file = find_transcript()

    print(
        f"Transcript: {transcript_file}"
    )

    with transcript_file.open(
        "r",
        encoding="utf-8",
    ) as file:

        transcript = json.load(file)

    # ========================================================
    # AUDIO
    # ========================================================

    audio = None

    audio_file = find_audio()

    if audio_file:

        print(
            f"Audio cache: {audio_file}"
        )

        with audio_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            audio = json.load(file)

    else:

        print(
            "Audio cache: tidak ditemukan"
        )

    # ========================================================
    # VIRAL ENGINE
    # ========================================================

    print()

    print(
        "Running Viral Engine V4..."
    )

    candidates = analyze_podcast_v4(
        transcript=transcript,
        audio=audio,
        min_duration=15,
        max_duration=60,
        max_results=20,
    )

    if not candidates:

        raise RuntimeError(
            "Viral Engine tidak menghasilkan kandidat clip."
        )

    # ========================================================
    # NORMALIZE RESULTS
    # ========================================================

    normalized = []

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):

        item = candidate_to_dict(
            candidate,
            index,
        )

        normalized.append(item)

    # ========================================================
    # SORT BY SCORE
    # ========================================================

    normalized.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # ========================================================
    # RE-RANK
    # ========================================================

    for index, item in enumerate(
        normalized,
        start=1,
    ):

        item["rank"] = index

    # ========================================================
    # PRINT TOP 20
    # ========================================================

    print()

    print("=" * 70)

    print(
        "🔥 TOP 20 PODCAST VIRAL MOMENTS - V4"
    )

    print("=" * 70)

    for candidate in normalized:

        print()

        print(
            f"#{candidate['rank']} "
            f"{candidate['category']}"
        )

        print(
            f"🔥 VIRAL SCORE : "
            f"{candidate['score']:.2f}/100"
        )

        print(
            f"TIME          : "
            f"{candidate['start']:.2f}s "
            f"→ "
            f"{candidate['end']:.2f}s"
        )

        print(
            f"DURATION      : "
            f"{candidate['duration']:.2f}s"
        )

        print()

        print(
            "TITLE:"
        )

        print(
            candidate["title"]
        )

        print()

        print(
            "TRANSCRIPT:"
        )

        print(
            candidate["transcript"]
        )

        print()

        print(
            "REASON:"
        )

        print(
            candidate["reason"]
        )

        print("-" * 70)

    # ========================================================
    # SAVE
    # ========================================================

    save_viral_results(
        normalized
    )

    # ========================================================
    # FINAL
    # ========================================================

    print()

    print("=" * 70)

    print(
        f"✓ {len(normalized)} kandidat ditemukan"
    )

    print(
        "✓ Hasil Viral Engine tersimpan."
    )

    print(
        "✓ Clip Generator siap mengambil TOP 5."
    )

    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()