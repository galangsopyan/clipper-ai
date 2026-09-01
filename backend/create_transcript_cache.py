from pathlib import Path
import hashlib
import json
import sys
import time


# ============================================================
# UTF-8 WINDOWS
# ============================================================

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="replace",
    )

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(
        encoding="utf-8",
        errors="replace",
    )


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MEDIA_DIR = BASE_DIR / "media"
INPUT_DIR = MEDIA_DIR / "input"
CACHE_DIR = MEDIA_DIR / "cache"

VIDEO_FILE = INPUT_DIR / "Podcast.mp4"

# File transcript yang digunakan oleh script lama
LEGACY_TRANSCRIPT_FILE = (
    CACHE_DIR / "Podcast_transcript.json"
)


# ============================================================
# DIRECTORY
# ============================================================

INPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# VIDEO HASH
# ============================================================

def calculate_video_hash(
    video_file: Path,
) -> str:
    """
    Membuat SHA256 berdasarkan isi file video.

    Video berbeda akan menghasilkan hash berbeda.
    """

    sha256 = hashlib.sha256()

    with video_file.open("rb") as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


# ============================================================
# CACHE FILE
# ============================================================

def get_cache_file(
    video_hash: str,
) -> Path:

    return (
        CACHE_DIR
        / f"transcript_{video_hash}.json"
    )


# ============================================================
# LOAD JSON
# ============================================================

def load_json(
    file_path: Path,
):

    if not file_path.exists():
        return None

    try:

        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    except Exception as e:

        print(
            f"[WARNING] Gagal membaca JSON: {file_path}"
        )

        print(
            f"[WARNING] {e}"
        )

        return None


# ============================================================
# SAVE JSON
# ============================================================

def save_json(
    file_path: Path,
    data: dict,
):
    """
    Simpan JSON secara aman menggunakan temporary file.

    Tujuannya menghindari file JSON setengah tertulis
    apabila proses terganggu.
    """

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_file = file_path.with_suffix(
        file_path.suffix + ".tmp"
    )

    with temp_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    # Replace file lama
    temp_file.replace(file_path)


# ============================================================
# FIND VALID CACHE
# ============================================================

def find_valid_cache(
    video_hash: str,
):
    """
    Cari transcript cache berdasarkan hash video.

    Cache hanya dianggap valid apabila:
    - file ada
    - JSON valid
    - video_hash cocok
    - segments tersedia
    """

    cache_file = get_cache_file(
        video_hash
    )

    if not cache_file.exists():

        return None

    data = load_json(
        cache_file
    )

    if not isinstance(
        data,
        dict,
    ):

        return None

    # Pastikan hash cocok
    if data.get(
        "video_hash"
    ) != video_hash:

        print(
            "[WARNING] Hash cache tidak cocok."
        )

        return None

    # Pastikan transcript memiliki segments
    segments = data.get(
        "segments"
    )

    if not isinstance(
        segments,
        list,
    ):

        return None

    if len(segments) == 0:

        return None

    return cache_file


# ============================================================
# TRANSCRIPTION
# ============================================================

def create_transcript(
    video_file: Path,
    cache_file: Path,
):
    """
    Menjalankan Faster-Whisper melalui
    app.services.transcription.transcribe_audio().
    """

    try:

        from app.services.transcription import (
            transcribe_audio,
        )

    except ImportError as e:

        raise RuntimeError(
            "Tidak dapat mengimport "
            "transcribe_audio dari "
            "app.services.transcription: "
            f"{e}"
        )

    print()
    print("=" * 70)
    print("WHISPER TRANSCRIPTION")
    print("=" * 70)

    print(
        f"Input : {video_file}"
    )

    print(
        f"Cache : {cache_file}"
    )

    print(
        "Memulai Faster-Whisper..."
    )

    start_time = time.perf_counter()

    # ========================================================
    # FORCE TRUE
    #
    # Karena function ini hanya dipanggil ketika hash cache
    # belum ditemukan, kita boleh memaksa transcription baru.
    # ========================================================

    result = transcribe_audio(
        audio_path=video_file,
        cache_path=cache_file,
        force=True,
    )

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print(
        f"Transcription selesai dalam "
        f"{elapsed:.2f} detik."
    )

    return result


# ============================================================
# NORMALIZE RESULT
# ============================================================

def normalize_transcript(
    result,
) -> dict:

    # --------------------------------------------------------
    # DICT
    # --------------------------------------------------------

    if isinstance(
        result,
        dict,
    ):

        transcript_data = dict(
            result
        )

    # --------------------------------------------------------
    # LIST
    # --------------------------------------------------------

    elif isinstance(
        result,
        list,
    ):

        transcript_data = {
            "segments": result
        }

    else:

        raise RuntimeError(
            "Format hasil transcription "
            "tidak dikenali. "
            f"Type: {type(result).__name__}"
        )

    # --------------------------------------------------------
    # SEGMENTS
    # --------------------------------------------------------

    segments = transcript_data.get(
        "segments",
        [],
    )

    if not isinstance(
        segments,
        list,
    ):

        raise RuntimeError(
            "Field 'segments' bukan list."
        )

    if len(segments) == 0:

        raise RuntimeError(
            "Whisper selesai tetapi "
            "tidak menghasilkan segments."
        )

    transcript_data[
        "segments"
    ] = segments

    return transcript_data


# ============================================================
# UPDATE METADATA
# ============================================================

def add_metadata(
    transcript_data: dict,
    video_hash: str,
):

    transcript_data[
        "video_hash"
    ] = video_hash

    transcript_data[
        "video_file"
    ] = VIDEO_FILE.name

    transcript_data[
        "segment_count"
    ] = len(
        transcript_data.get(
            "segments",
            [],
        )
    )

    transcript_data[
        "generated_at"
    ] = time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return transcript_data


# ============================================================
# UPDATE LEGACY TRANSCRIPT
# ============================================================

def update_legacy_transcript(
    cache_file: Path,
    video_hash: str,
):
    """
    Podcast_transcript.json selalu diarahkan ke transcript
    video yang sedang aktif.

    Ini penting karena beberapa script lama masih membaca:

        media/cache/Podcast_transcript.json
    """

    data = load_json(
        cache_file
    )

    if not isinstance(
        data,
        dict,
    ):

        raise RuntimeError(
            "Cache transcript tidak valid."
        )

    data["video_hash"] = (
        video_hash
    )

    data["video_file"] = (
        VIDEO_FILE.name
    )

    save_json(
        LEGACY_TRANSCRIPT_FILE,
        data,
    )

    print(
        "[OK] Legacy transcript diperbarui."
    )

    print(
        f"Legacy : {LEGACY_TRANSCRIPT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    start_time = time.perf_counter()

    print()
    print("=" * 70)
    print("CLIPFORGE AI - TRANSCRIPT CACHE")
    print("=" * 70)

    # ========================================================
    # CHECK VIDEO
    # ========================================================

    if not VIDEO_FILE.exists():

        print(
            "[ERROR] Video tidak ditemukan:"
        )

        print(
            VIDEO_FILE
        )

        sys.exit(1)

    # ========================================================
    # VIDEO INFO
    # ========================================================

    video_size = VIDEO_FILE.stat().st_size

    print()
    print(
        f"Video : {VIDEO_FILE}"
    )

    print(
        f"Size  : {video_size:,} bytes"
    )

    # ========================================================
    # HASH
    # ========================================================

    print()
    print(
        "Menghitung fingerprint video..."
    )

    hash_start = time.perf_counter()

    video_hash = calculate_video_hash(
        VIDEO_FILE
    )

    hash_elapsed = (
        time.perf_counter()
        - hash_start
    )

    print(
        f"Hash  : {video_hash}"
    )

    print(
        f"Hash time: {hash_elapsed:.2f} detik"
    )

    # ========================================================
    # CACHE PATH
    # ========================================================

    cache_file = get_cache_file(
        video_hash
    )

    print()
    print(
        f"Cache : {cache_file}"
    )

    # ========================================================
    # CACHE HIT
    # ========================================================

    existing_cache = find_valid_cache(
        video_hash
    )

    if existing_cache:

        print()
        print(
            "=" * 70
        )

        print(
            "CACHE HIT"
        )

        print(
            "=" * 70
        )

        print(
            "Transcript untuk video ini sudah tersedia."
        )

        print(
            f"Cache : {existing_cache}"
        )

        # Pastikan legacy transcript menunjuk
        # ke video yang sedang aktif.
        update_legacy_transcript(
            existing_cache,
            video_hash,
        )

        total_time = (
            time.perf_counter()
            - start_time
        )

        print()
        print(
            f"Selesai dalam {total_time:.2f} detik."
        )

        return

    # ========================================================
    # CACHE MISS
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "CACHE MISS - VIDEO BARU"
    )

    print(
        "=" * 70
    )

    print(
        "Transcript video lama tidak digunakan."
    )

    print(
        "Membuat transcript baru..."
    )

    # ========================================================
    # WHISPER
    # ========================================================

    result = create_transcript(
        VIDEO_FILE,
        cache_file,
    )

    # ========================================================
    # NORMALIZE
    # ========================================================

    transcript_data = normalize_transcript(
        result
    )

    # ========================================================
    # METADATA
    # ========================================================

    transcript_data = add_metadata(
        transcript_data,
        video_hash,
    )

    segments = transcript_data[
        "segments"
    ]

    # ========================================================
    # SAVE HASH CACHE
    # ========================================================

    print()
    print(
        "Menyimpan transcript hash cache..."
    )

    save_json(
        cache_file,
        transcript_data,
    )

    print(
        "[OK] Hash cache tersimpan."
    )

    # ========================================================
    # SAVE LEGACY CACHE
    # ========================================================

    print(
        "Menyimpan legacy transcript..."
    )

    save_json(
        LEGACY_TRANSCRIPT_FILE,
        transcript_data,
    )

    print(
        "[OK] Legacy transcript tersimpan."
    )

    # ========================================================
    # VERIFY HASH CACHE
    # ========================================================

    verified_data = load_json(
        cache_file
    )

    if not isinstance(
        verified_data,
        dict,
    ):

        raise RuntimeError(
            "Cache transcript gagal diverifikasi."
        )

    if verified_data.get(
        "video_hash"
    ) != video_hash:

        raise RuntimeError(
            "Verifikasi gagal: "
            "video_hash tidak cocok."
        )

    if not verified_data.get(
        "segments"
    ):

        raise RuntimeError(
            "Verifikasi gagal: "
            "segments kosong."
        )

    # ========================================================
    # VERIFY LEGACY
    # ========================================================

    if not LEGACY_TRANSCRIPT_FILE.exists():

        raise RuntimeError(
            "Legacy transcript gagal dibuat."
        )

    # ========================================================
    # SUCCESS
    # ========================================================

    total_time = (
        time.perf_counter()
        - start_time
    )

    print()
    print("=" * 70)
    print("TRANSCRIPTION BERHASIL")
    print("=" * 70)

    print(
        f"Segments : {len(segments)}"
    )

    print(
        f"Hash     : {video_hash}"
    )

    print(
        f"Cache    : {cache_file}"
    )

    print(
        f"Legacy   : {LEGACY_TRANSCRIPT_FILE}"
    )

    print(
        f"Total    : {total_time:.2f} detik"
    )

    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()