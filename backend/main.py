from pathlib import Path
from typing import Any, Dict, List
import json
import shutil
import subprocess
import sys
import threading
import uuid
import time
import re
import os

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MEDIA_DIR = BASE_DIR / "media"
INPUT_DIR = MEDIA_DIR / "input"
OUTPUT_DIR = MEDIA_DIR / "output"
CACHE_DIR = MEDIA_DIR / "cache"
TEMP_DIR = INPUT_DIR / "temp"

VIDEO_FILE = INPUT_DIR / "Podcast.mp4"
TRANSCRIPT_FILE = CACHE_DIR / "Podcast_transcript.json"
CLIPS_FILE = OUTPUT_DIR / "clips.json"
SOURCE_METADATA_FILE = CACHE_DIR / "source_metadata.json"

MAX_CLIPS = 5

MIN_VIDEO_SIZE = 1000
MAX_UPLOAD_SIZE = 3 * 1024 * 1024 * 1024  # 3 GB


# ============================================================
# CREATE DIRECTORIES
# ============================================================

for directory in [
    INPUT_DIR,
    OUTPUT_DIR,
    CACHE_DIR,
    TEMP_DIR,
]:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="ClipForge AI API",
    version="5.5.0",
)


# ============================================================
# CORS
# ============================================================

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:3000",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STATIC MEDIA
# ============================================================

app.mount(
    "/media",
    StaticFiles(directory=str(MEDIA_DIR)),
    name="media",
)


# ============================================================
# JOB STORAGE
# ============================================================

jobs: Dict[str, Dict[str, Any]] = {}

job_lock = threading.Lock()


# ============================================================
# URL PAYLOAD
# ============================================================

class VideoURLRequest(BaseModel):
    url: str


# ============================================================
# FILE LOCK
# ============================================================

def is_file_locked(path: Path) -> bool:
    """
    Windows compatible file lock check.
    """

    if not path.exists():
        return False

    try:
        with path.open("a+b"):
            pass

        return False

    except PermissionError:
        return True

    except OSError:
        return True


# ============================================================
# WAIT FILE AVAILABLE
# ============================================================

def wait_until_file_available(
    path: Path,
    retries: int = 30,
    delay: float = 0.5,
) -> bool:

    for _ in range(retries):

        if not path.exists():
            return True

        if not is_file_locked(path):
            return True

        time.sleep(delay)

    return False


# ============================================================
# SAFE DELETE
# ============================================================

def safe_delete(path: Path) -> bool:

    if not path.exists():
        return True

    try:

        if is_file_locked(path):

            print(
                f"[WARNING] File sedang digunakan: {path}"
            )

            return False

        path.unlink()

        print(f"[DELETE] {path}")

        return True

    except Exception as e:

        print(
            f"[WARNING] Gagal menghapus {path}: {e}"
        )

        return False


# ============================================================
# RESET TRANSCRIPT CACHE
# ============================================================

def reset_transcript_cache():

    print()
    print("=" * 70)
    print("RESET TRANSCRIPT CACHE")
    print("=" * 70)

    deleted = 0

    # HANYA transcript/audio cache.
    # Jangan hapus source_metadata.json.
    patterns = [
        "*_transcript.json",
        "*_audio.json",
    ]

    for pattern in patterns:

        for file in CACHE_DIR.glob(pattern):

            if safe_delete(file):
                deleted += 1

    print(
        f"[OK] {deleted} transcript/audio cache dihapus."
    )


# ============================================================
# RESET SOURCE METADATA
# ============================================================

def reset_source_metadata():

    if SOURCE_METADATA_FILE.exists():

        safe_delete(
            SOURCE_METADATA_FILE
        )


# ============================================================
# RESET OUTPUT
# ============================================================

def clean_old_output():

    print()
    print("=" * 70)
    print("CLEAN OLD OUTPUT")
    print("=" * 70)

    # MP4
    for file in OUTPUT_DIR.glob("clip_*.mp4"):
        safe_delete(file)

    # ASS
    for file in OUTPUT_DIR.glob("clip_*.ass"):
        safe_delete(file)

    # JSON
    if CLIPS_FILE.exists():
        safe_delete(CLIPS_FILE)

    # Subtitle directory
    subtitles_dir = OUTPUT_DIR / "subtitles"

    if subtitles_dir.exists():

        for file in subtitles_dir.glob("*.ass"):
            safe_delete(file)

    print("[OK] Output lama sudah dibersihkan.")


# ============================================================
# RESET EVERYTHING FOR NEW VIDEO
# ============================================================

def reset_for_new_video(
    reset_source: bool = True,
):

    print()
    print("=" * 70)
    print("RESET DATA UNTUK VIDEO BARU")
    print("=" * 70)

    reset_transcript_cache()

    clean_old_output()

    if reset_source:
        reset_source_metadata()

    print(
        "[OK] Data video lama sudah direset."
    )


# ============================================================
# UPDATE JOB
# ============================================================

def update_job(
    job_id: str,
    **updates,
):

    with job_lock:

        if job_id in jobs:
            jobs[job_id].update(updates)


# ============================================================
# COMMAND RUNNER
# ============================================================

def run_command(
    script_name: str,
    job_id: str,
):

    script = BASE_DIR / script_name

    if not script.exists():

        raise FileNotFoundError(
            f"Script tidak ditemukan: {script}"
        )

    update_job(
        job_id,
        message=f"Menjalankan {script_name}...",
    )

    print()
    print("=" * 70)
    print(f"RUNNING: {script_name}")
    print("=" * 70)

    result = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(script),
        ],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:

        raise RuntimeError(
            f"{script_name} gagal.\n"
            f"{result.stderr[-5000:]}"
        )

    return result


# ============================================================
# LOAD CLIPS
# ============================================================

def load_clips() -> List[Dict[str, Any]]:

    if not CLIPS_FILE.exists():
        return []

    try:

        with CLIPS_FILE.open(
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        if isinstance(data, list):

            return [
                item
                for item in data
                if isinstance(item, dict)
            ]

        if isinstance(data, dict):

            clips = data.get(
                "clips",
                data.get(
                    "results",
                    [],
                ),
            )

            if isinstance(clips, list):

                return [
                    item
                    for item in clips
                    if isinstance(item, dict)
                ]

    except Exception as e:

        print(
            f"[ERROR] Gagal membaca clips.json: {e}"
        )

    return []


# ============================================================
# SAVE SOURCE METADATA
# ============================================================

def save_source_metadata(
    metadata: Dict[str, Any],
):

    try:

        with SOURCE_METADATA_FILE.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                metadata,
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(
            f"[OK] Source metadata disimpan: "
            f"{SOURCE_METADATA_FILE}"
        )

    except Exception as e:

        print(
            f"[WARNING] Gagal menyimpan metadata: {e}"
        )


# ============================================================
# LOAD SOURCE METADATA
# ============================================================

def load_source_metadata() -> Dict[str, Any]:

    if not SOURCE_METADATA_FILE.exists():
        return {}

    try:

        with SOURCE_METADATA_FILE.open(
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        if isinstance(data, dict):
            return data

    except Exception as e:

        print(
            f"[WARNING] Gagal membaca source metadata: {e}"
        )

    return {}


# ============================================================
# VALID VIDEO FILE
# ============================================================

def valid_video_file(
    path: Path,
) -> bool:

    return (
        path.exists()
        and path.is_file()
        and path.stat().st_size > MIN_VIDEO_SIZE
    )


# ============================================================
# GET CLIP FILE
# ============================================================

def get_clip_file(
    index: int,
):

    vertical_file = (
        OUTPUT_DIR
        / f"clip_{index:02d}_vertical.mp4"
    )

    normal_file = (
        OUTPUT_DIR
        / f"clip_{index:02d}.mp4"
    )

    # PRIORITAS:
    # 1. Vertical
    # 2. Normal

    if valid_video_file(vertical_file):

        return {
            "file": vertical_file,
            "url": (
                f"/media/output/"
                f"clip_{index:02d}_vertical.mp4"
            ),
            "format": "9:16",
            "subtitle": True,
        }

    if valid_video_file(normal_file):

        return {
            "file": normal_file,
            "url": (
                f"/media/output/"
                f"clip_{index:02d}.mp4"
            ),
            "format": "16:9",
            "subtitle": False,
        }

    return None


# ============================================================
# GET GENERATED CLIPS
# ============================================================

def get_generated_clips():

    generated_vertical = []
    generated_normal = []

    missing = []

    for index in range(
        1,
        MAX_CLIPS + 1,
    ):

        vertical_file = (
            OUTPUT_DIR
            / f"clip_{index:02d}_vertical.mp4"
        )

        normal_file = (
            OUTPUT_DIR
            / f"clip_{index:02d}.mp4"
        )

        if valid_video_file(vertical_file):

            generated_vertical.append(index)

        elif valid_video_file(normal_file):

            generated_normal.append(index)

        else:

            missing.append(index)

    return (
        generated_vertical,
        generated_normal,
        missing,
    )


# ============================================================
# PROCESS JOB
# ============================================================

def process_job(
    job_id: str,
):

    try:

        # ====================================================
        # START
        # ====================================================

        update_job(
            job_id,
            status="processing",
            step="transcription",
            message=(
                "Membuat transcript baru dengan Whisper..."
            ),
        )

        # ====================================================
        # EXTRA SAFETY
        # ====================================================

        if TRANSCRIPT_FILE.exists():

            print(
                "[INFO] Menghapus transcript lama..."
            )

            safe_delete(
                TRANSCRIPT_FILE
            )

        # ====================================================
        # 1. TRANSCRIPTION
        # ====================================================

        run_command(
            "create_transcript_cache.py",
            job_id,
        )

        if not TRANSCRIPT_FILE.exists():

            raise RuntimeError(
                "Transcription selesai tetapi "
                "Podcast_transcript.json tidak ditemukan."
            )

        print(
            "[OK] Transcript baru berhasil dibuat."
        )

        # ====================================================
        # 2. VIRAL ENGINE
        # ====================================================

        update_job(
            job_id,
            step="viral_engine",
            message="Menganalisis viral moments...",
        )

        run_command(
            "test_viral_engine_v4.py",
            job_id,
        )

        # ====================================================
        # 3. CLIP GENERATION
        # ====================================================

        update_job(
            job_id,
            step="clip_generation",
            message="Membuat Top 5 clips...",
        )

        run_command(
            "test_clip_generator.py",
            job_id,
        )

        # ====================================================
        # VERIFY CLIPS JSON
        # ====================================================

        if not CLIPS_FILE.exists():

            raise RuntimeError(
                "Clip generator selesai tetapi "
                "clips.json tidak ditemukan."
            )

        clips = load_clips()

        if not clips:

            raise RuntimeError(
                "clips.json ditemukan tetapi "
                "tidak berisi clip."
            )

        print(
            f"[OK] clips.json berisi {len(clips)} clip."
        )

        # ====================================================
        # 4. VERTICAL RENDERER
        # ====================================================

        update_job(
            job_id,
            step="vertical_renderer",
            message=(
                "Rendering Top 5 dalam format "
                "9:16 + subtitle..."
            ),
        )

        run_command(
            "test_vertical_renderer.py",
            job_id,
        )

        # ====================================================
        # 5. CHECK OUTPUT
        # ====================================================

        update_job(
            job_id,
            step="verification",
            message=(
                "Memastikan seluruh Top 5 video "
                "berhasil dibuat..."
            ),
        )

        (
            generated_vertical,
            generated_normal,
            missing,
        ) = get_generated_clips()

        print()
        print("=" * 70)
        print("VIDEO OUTPUT CHECK")
        print("=" * 70)

        print(
            f"Vertical : "
            f"{len(generated_vertical)}/{MAX_CLIPS}"
        )

        print(
            f"Normal   : "
            f"{len(generated_normal)}/{MAX_CLIPS}"
        )

        if generated_vertical:

            print(
                "Vertical ready:",
                ", ".join(
                    f"#{x}"
                    for x in generated_vertical
                ),
            )

        if generated_normal:

            print(
                "Normal ready:",
                ", ".join(
                    f"#{x}"
                    for x in generated_normal
                ),
            )

        if missing:

            print(
                "Missing:",
                ", ".join(
                    f"#{x}"
                    for x in missing
                ),
            )

        # ====================================================
        # 6. REPAIR
        # ====================================================

        if missing:

            update_job(
                job_id,
                step="repair",
                message=(
                    f"Memperbaiki {len(missing)} "
                    "clip yang belum berhasil..."
                ),
            )

            repair_script = (
                BASE_DIR / "repair_renderer.py"
            )

            if repair_script.exists():

                print()
                print(
                    "[REPAIR] Menjalankan "
                    "repair_renderer.py..."
                )

                run_command(
                    "repair_renderer.py",
                    job_id,
                )

            else:

                print(
                    "[WARNING] repair_renderer.py "
                    "tidak ditemukan."
                )

        # ====================================================
        # 7. FINAL VERIFY
        # ====================================================

        (
            generated_vertical,
            generated_normal,
            missing,
        ) = get_generated_clips()

        print()
        print("=" * 70)
        print("FINAL TOP 5 VERIFICATION")
        print("=" * 70)

        print(
            f"Vertical : "
            f"{len(generated_vertical)}/{MAX_CLIPS}"
        )

        print(
            f"Normal   : "
            f"{len(generated_normal)}/{MAX_CLIPS}"
        )

        print(
            f"Missing  : "
            f"{len(missing)}/{MAX_CLIPS}"
        )

        # ====================================================
        # STRICT TOP 5
        # ====================================================

        total_available = (
            len(generated_vertical)
            + len(generated_normal)
        )

        if total_available != MAX_CLIPS:

            missing_text = ", ".join(
                f"clip_{x:02d}"
                for x in missing
            )

            raise RuntimeError(
                "Top 5 belum lengkap.\n"
                f"Vertical : "
                f"{len(generated_vertical)}/{MAX_CLIPS}\n"
                f"Normal   : "
                f"{len(generated_normal)}/{MAX_CLIPS}\n"
                f"Missing  : {missing_text}"
            )

        # ====================================================
        # COMPLETE
        # ====================================================

        final_clips = load_clips()

        update_job(
            job_id,
            step="completed",
            status="completed",
            message=(
                "Top 5 clips berhasil dibuat "
                "dan diverifikasi."
            ),
            clips_count=min(
                len(final_clips),
                MAX_CLIPS,
            ),
        )

        print()
        print("=" * 70)
        print("SUCCESS: 5/5 CLIPS GENERATED")
        print("=" * 70)

    except Exception as e:

        print()
        print("=" * 70)
        print("JOB FAILED")
        print("=" * 70)
        print(str(e))

        update_job(
            job_id,
            status="failed",
            step="error",
            message=str(e),
            error=str(e),
        )


# ============================================================
# URL VALIDATION
# ============================================================

def validate_video_url(
    url: str,
) -> bool:

    url = url.strip()

    if not url:
        return False

    pattern = re.compile(
        r"^https?://"
        r"(www\.)?"
        r"(youtube\.com|youtu\.be|m\.youtube\.com)"
        r"/.+",
        re.IGNORECASE,
    )

    return bool(
        pattern.match(url)
    )


# ============================================================
# DOWNLOAD VIDEO FROM URL
# ============================================================

def download_video_from_url(
    url: str,
    output_file: Path,
):

    if not validate_video_url(url):

        raise ValueError(
            "URL tidak valid. "
            "Gunakan URL YouTube."
        )

    print()
    print("=" * 70)
    print("DOWNLOAD VIDEO FROM URL")
    print("=" * 70)

    print(f"URL    : {url}")
    print(f"Output : {output_file}")

    download_id = uuid.uuid4().hex

    prefix = f"url_{download_id}"

    output_template = (
        TEMP_DIR
        / f"{prefix}.%(ext)s"
    )

    command = [
        sys.executable,
        "-m",
        "yt_dlp",

        "--no-playlist",

        "-f",
        "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",

        "--merge-output-format",
        "mp4",

        "--write-info-json",

        "-o",
        str(output_template),

        url,
    ]

    print()
    print(
        "[INFO] Mengunduh video dari URL..."
    )

    result = subprocess.run(
        command,
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.stdout:
        print(result.stdout)

    if result.returncode != 0:

        if result.stderr:
            print(result.stderr)

        raise RuntimeError(
            "Gagal download video dari URL.\n"
            f"{result.stderr[-5000:]}"
        )

    # ========================================================
    # FIND VIDEO
    # ========================================================

    downloaded_files = [
        file
        for file in TEMP_DIR.glob(
            f"{prefix}.*"
        )
        if (
            file.is_file()
            and file.suffix.lower()
            not in {
                ".part",
                ".ytdl",
                ".json",
            }
        )
    ]

    if not downloaded_files:

        raise RuntimeError(
            "Download selesai tetapi "
            "file video tidak ditemukan."
        )

    mp4_files = [
        file
        for file in downloaded_files
        if file.suffix.lower() == ".mp4"
    ]

    if mp4_files:

        downloaded_file = mp4_files[0]

    else:

        downloaded_file = downloaded_files[0]

    # ========================================================
    # READ METADATA
    # ========================================================

    metadata_files = list(
        TEMP_DIR.glob(
            f"{prefix}.*.info.json"
        )
    )

    metadata = {}

    if metadata_files:

        try:

            with metadata_files[0].open(
                "r",
                encoding="utf-8",
            ) as f:

                metadata = json.load(f)

        except Exception as e:

            print(
                f"[WARNING] Metadata gagal dibaca: {e}"
            )

    # ========================================================
    # SIZE
    # ========================================================

    size = downloaded_file.stat().st_size

    if size <= 0:

        safe_delete(
            downloaded_file
        )

        raise RuntimeError(
            "Video hasil download kosong."
        )

    print(
        f"[OK] Download selesai: {downloaded_file}"
    )

    print(
        f"[OK] Size: {size:,} bytes"
    )

    # ========================================================
    # DELETE OLD VIDEO
    # ========================================================

    if output_file.exists():

        available = wait_until_file_available(
            output_file,
            retries=30,
            delay=0.5,
        )

        if not available:

            raise RuntimeError(
                "Podcast.mp4 sedang digunakan "
                "oleh proses lain."
            )

        if not safe_delete(output_file):

            raise RuntimeError(
                "Podcast.mp4 lama tidak dapat dihapus."
            )

    # ========================================================
    # MOVE
    # ========================================================

    downloaded_file.replace(
        output_file
    )

    # ========================================================
    # VERIFY
    # ========================================================

    if not output_file.exists():

        raise RuntimeError(
            "Video gagal dipindahkan "
            "ke Podcast.mp4."
        )

    final_size = output_file.stat().st_size

    if final_size <= 0:

        raise RuntimeError(
            "Podcast.mp4 hasil download kosong."
        )

    # ========================================================
    # METADATA
    # ========================================================

    source_metadata = {
        "source": "youtube",
        "url": url,
        "title": metadata.get(
            "title",
            "Untitled Video",
        ),
        "description": metadata.get(
            "description",
            "",
        ),
        "channel": metadata.get(
            "channel",
            metadata.get(
                "uploader",
                "",
            ),
        ),
        "uploader": metadata.get(
            "uploader",
            "",
        ),
        "duration": metadata.get(
            "duration",
            0,
        ),
        "thumbnail": metadata.get(
            "thumbnail",
            None,
        ),
        "video_id": metadata.get(
            "id",
            "",
        ),
        "downloaded_at": time.time(),
    }

    print()
    print(
        "[SOURCE TITLE]"
    )

    print(
        source_metadata["title"]
    )

    print()
    print(
        f"[OK] Video tersimpan: {output_file}"
    )

    print(
        f"[OK] Final size: {final_size:,} bytes"
    )

    # ========================================================
    # CLEAN TEMP METADATA
    # ========================================================

    for metadata_file in metadata_files:
        safe_delete(metadata_file)

    return {
        "path": str(output_file),
        "size": final_size,
        "metadata": source_metadata,
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "name": "ClipForge AI",
        "version": "5.5.0",
        "status": "online",
        "max_clips": MAX_CLIPS,

        "features": [
            "file_upload",
            "youtube_url",
            "source_metadata",
            "whisper_transcription",
            "viral_engine",
            "clip_generation",
            "vertical_renderer",
            "automatic_repair",
            "top_5_verification",
        ],
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():

    active_jobs = [
        job
        for job in jobs.values()
        if job.get("status") in [
            "queued",
            "processing",
        ]
    ]

    (
        generated_vertical,
        generated_normal,
        missing,
    ) = get_generated_clips()

    return {
        "status": "ok",

        "video": VIDEO_FILE.exists(),

        "video_size": (
            VIDEO_FILE.stat().st_size
            if VIDEO_FILE.exists()
            else 0
        ),

        "whisper_cache": (
            TRANSCRIPT_FILE.exists()
        ),

        "clips_json": (
            CLIPS_FILE.exists()
        ),

        "clips_count": len(
            load_clips()
        ),

        "vertical_count": len(
            generated_vertical
        ),

        "normal_count": len(
            generated_normal
        ),

        "missing_clips": missing,

        "active_jobs": len(
            active_jobs
        ),

        "source": load_source_metadata(),
    }


# ============================================================
# UPLOAD VIDEO FILE
# ============================================================

@app.post("/api/upload")
async def upload_video(
    file: UploadFile = File(...),
):

    if not file.filename:

        await file.close()

        raise HTTPException(
            status_code=400,
            detail="Nama file tidak valid.",
        )

    # ========================================================
    # ACTIVE JOB
    # ========================================================

    active_jobs = [
        job
        for job in jobs.values()
        if job.get("status") in [
            "queued",
            "processing",
        ]
    ]

    if active_jobs:

        await file.close()

        raise HTTPException(
            status_code=409,
            detail=(
                "Video sedang diproses. "
                "Tunggu sampai proses selesai."
            ),
        )

    # ========================================================
    # EXTENSION
    # ========================================================

    allowed = {
        ".mp4",
        ".mov",
        ".mkv",
        ".webm",
        ".avi",
    }

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in allowed:

        await file.close()

        raise HTTPException(
            status_code=400,
            detail=(
                "Format video tidak didukung. "
                "Gunakan MP4, MOV, MKV, WEBM, atau AVI."
            ),
        )

    temp_file = (
        TEMP_DIR
        / f"upload_{uuid.uuid4().hex}{extension}"
    )

    try:

        print()
        print("=" * 70)
        print("NEW VIDEO UPLOAD")
        print("=" * 70)

        print(
            f"Filename : {file.filename}"
        )

        # ====================================================
        # SAVE TEMP
        # ====================================================

        with temp_file.open("wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

        await file.close()

        if not temp_file.exists():

            raise RuntimeError(
                "Temporary video gagal dibuat."
            )

        temp_size = temp_file.stat().st_size

        if temp_size <= 0:

            raise RuntimeError(
                "Video yang diupload kosong."
            )

        # ====================================================
        # RESET OLD DATA
        # ====================================================

        reset_for_new_video(
            reset_source=True
        )

        # ====================================================
        # DELETE OLD VIDEO
        # ====================================================

        if VIDEO_FILE.exists():

            available = wait_until_file_available(
                VIDEO_FILE
            )

            if not available:

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Podcast.mp4 sedang digunakan."
                    ),
                )

            if not safe_delete(VIDEO_FILE):

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Podcast.mp4 lama "
                        "tidak dapat dihapus."
                    ),
                )

        # ====================================================
        # MOVE
        # ====================================================

        temp_file.replace(
            VIDEO_FILE
        )

        if not VIDEO_FILE.exists():

            raise RuntimeError(
                "Video gagal dipindahkan."
            )

        final_size = VIDEO_FILE.stat().st_size

        # ====================================================
        # SAVE SOURCE METADATA
        # ====================================================

        save_source_metadata(
            {
                "source": "file",
                "url": None,
                "title": Path(
                    file.filename
                ).stem,
                "filename": file.filename,
                "downloaded_at": time.time(),
            }
        )

        return {
            "success": True,
            "source": "file",
            "filename": file.filename,
            "saved_as": "Podcast.mp4",
            "size": final_size,

            "transcript_cache_reset": True,
            "old_clips_reset": True,

            "message": (
                "Video berhasil diupload. "
                "Data video lama sudah dibersihkan."
            ),
        }

    except HTTPException:
        raise

    except Exception as e:

        print(
            f"[ERROR] Upload gagal: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Gagal menyimpan video: {e}",
        )

    finally:

        try:

            if temp_file.exists():
                temp_file.unlink()

        except Exception:
            pass


# ============================================================
# UPLOAD VIDEO FROM URL
# ============================================================

@app.post("/api/upload-url")
async def upload_video_url(
    payload: VideoURLRequest,
):

    url = payload.url.strip()

    if not url:

        raise HTTPException(
            status_code=400,
            detail="URL video tidak boleh kosong.",
        )

    if not validate_video_url(url):

        raise HTTPException(
            status_code=400,
            detail=(
                "URL tidak didukung. "
                "Gunakan URL YouTube yang valid."
            ),
        )

    # ========================================================
    # ACTIVE JOB
    # ========================================================

    active_jobs = [
        job
        for job in jobs.values()
        if job.get("status") in [
            "queued",
            "processing",
        ]
    ]

    if active_jobs:

        raise HTTPException(
            status_code=409,
            detail=(
                "Video sedang diproses. "
                "Tunggu sampai proses selesai."
            ),
        )

    try:

        print()
        print("=" * 70)
        print("NEW VIDEO URL")
        print("=" * 70)

        print(
            f"URL: {url}"
        )

        # ====================================================
        # RESET DATA LAMA
        # ====================================================

        reset_for_new_video(
            reset_source=True
        )

        # ====================================================
        # DOWNLOAD
        # ====================================================

        download_result = download_video_from_url(
            url,
            VIDEO_FILE,
        )

        # ====================================================
        # SAVE METADATA SETELAH RESET
        # ====================================================

        metadata = download_result.get(
            "metadata",
            {},
        )

        save_source_metadata(
            metadata
        )

        return {
            "success": True,

            "source": "url",

            "url": url,

            "filename": "Podcast.mp4",

            "saved_as": "Podcast.mp4",

            "size": download_result["size"],

            "title": metadata.get(
                "title",
                "Untitled Video",
            ),

            "channel": metadata.get(
                "channel",
                "",
            ),

            "duration": metadata.get(
                "duration",
                0,
            ),

            "thumbnail": metadata.get(
                "thumbnail",
                None,
            ),

            "transcript_cache_reset": True,

            "old_clips_reset": True,

            "message": (
                "Video berhasil diambil dari URL. "
                "Metadata video terbaru sudah disimpan. "
                "Video siap diproses."
            ),
        }

    except HTTPException:
        raise

    except Exception as e:

        print(
            f"[ERROR] URL download gagal: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ============================================================
# GENERATE
# ============================================================

@app.post("/api/generate")
def generate():

    # ========================================================
    # VIDEO CHECK
    # ========================================================

    if not VIDEO_FILE.exists():

        raise HTTPException(
            status_code=400,
            detail="Upload video terlebih dahulu.",
        )

    if VIDEO_FILE.stat().st_size <= 0:

        raise HTTPException(
            status_code=400,
            detail="File video kosong.",
        )

    if is_file_locked(VIDEO_FILE):

        raise HTTPException(
            status_code=409,
            detail=(
                "Video sedang digunakan proses lain."
            ),
        )

    # ========================================================
    # ACTIVE JOB
    # ========================================================

    active_jobs = [
        job
        for job in jobs.values()
        if job.get("status") in [
            "queued",
            "processing",
        ]
    ]

    if active_jobs:

        raise HTTPException(
            status_code=409,
            detail=(
                "Masih ada proses generate yang berjalan."
            ),
        )

    # ========================================================
    # CLEAN OUTPUT
    # ========================================================

    clean_old_output()

    # ========================================================
    # CREATE JOB
    # ========================================================

    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "id": job_id,
        "status": "queued",
        "step": "queued",
        "message": "Menunggu proses...",
        "clips_count": 0,
        "source": load_source_metadata(),
    }

    # ========================================================
    # THREAD
    # ========================================================

    thread = threading.Thread(
        target=process_job,
        args=(job_id,),
        daemon=True,
    )

    thread.start()

    return {
        "success": True,
        "job_id": job_id,
        "message": "Proses generate dimulai.",
    }


# ============================================================
# JOB STATUS
# ============================================================

@app.get("/api/jobs/{job_id}")
def get_job(
    job_id: str,
):

    job = jobs.get(job_id)

    if not job:

        raise HTTPException(
            status_code=404,
            detail="Job tidak ditemukan.",
        )

    return job


# ============================================================
# GET ALL CLIPS
# ============================================================

@app.get("/api/clips")
def get_clips():

    clips = load_clips()

    source_metadata = load_source_metadata()

    result = []

    # ========================================================
    # ALWAYS RETURN MAX 5
    # ========================================================

    for index in range(
        1,
        MAX_CLIPS + 1,
    ):

        # ====================================================
        # METADATA
        # ====================================================

        if index <= len(clips):

            item = dict(
                clips[index - 1]
            )

        else:

            item = {}

        # ====================================================
        # RANK
        # ====================================================

        item["rank"] = index

        # ====================================================
        # VIDEO FILE
        # ====================================================

        video_info = get_clip_file(
            index
        )

        if video_info:

            video_file = video_info["file"]

            item["video"] = (
                video_info["url"]
                + f"?v={video_file.stat().st_mtime_ns}"
            )

            item["format"] = (
                video_info["format"]
            )

            item["subtitle"] = (
                video_info["subtitle"]
            )

            item["exists"] = True

            item["size"] = (
                video_file.stat().st_size
            )

        else:

            item["video"] = None

            item["format"] = None

            item["subtitle"] = False

            item["exists"] = False

            item["size"] = 0

        # ====================================================
        # SOURCE INFO
        # ====================================================

        item["source_title"] = (
            source_metadata.get(
                "title",
                "",
            )
        )

        item["source_channel"] = (
            source_metadata.get(
                "channel",
                "",
            )
        )

        item["source_url"] = (
            source_metadata.get(
                "url",
                None,
            )
        )

        # ====================================================
        # TITLE FALLBACK
        # ====================================================

        if not item.get("title"):

            item["title"] = (
                f"Viral Clip #{index}"
            )

        result.append(item)

    # ========================================================
    # COUNTS
    # ========================================================

    available = [
        item
        for item in result
        if item["exists"]
    ]

    missing = [
        item["rank"]
        for item in result
        if not item["exists"]
    ]

    return {
        "count": len(result),

        "available_count": len(
            available
        ),

        "missing": missing,

        "clips": result,

        "source": source_metadata,
    }


# ============================================================
# GET SINGLE CLIP
# ============================================================

@app.get("/api/clips/{index}")
def get_clip(
    index: int,
):

    if index < 1 or index > MAX_CLIPS:

        raise HTTPException(
            status_code=404,
            detail="Clip tidak ditemukan.",
        )

    video_info = get_clip_file(
        index
    )

    if not video_info:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Video clip #{index} "
                "belum tersedia."
            ),
        )

    video_file = video_info["file"]

    return {
        "rank": index,

        "video": (
            video_info["url"]
            + f"?v={video_file.stat().st_mtime_ns}"
        ),

        "format": video_info["format"],

        "subtitle": video_info["subtitle"],

        "exists": True,

        "size": video_file.stat().st_size,
    }


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    import os
    import uvicorn

    port = int(
        os.getenv("PORT", "8000")
    )

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
