from __future__ import annotations

import base64
import binascii
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

import yt_dlp


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

# Local:
#   %TEMP%\clips
#
# Railway:
#   bisa diarahkan ke /tmp/clips melalui DOWNLOAD_DIR
#
if os.getenv("DOWNLOAD_DIR"):
    DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR"))
else:
    DOWNLOAD_DIR = Path(tempfile.gettempdir()) / "clips"

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HELPERS
# ============================================================

def log(message: str) -> None:
    """Simple console logger."""
    print(f"[YouTube Downloader] {message}", flush=True)


def sanitize_filename(name: str) -> str:
    """
    Membuat nama file aman untuk Windows/Linux.
    """
    if not name:
        name = "video"

    invalid_chars = '<>:"/\\|?*'

    for char in invalid_chars:
        name = name.replace(char, "_")

    name = name.strip().rstrip(".")

    if not name:
        name = "video"

    # Hindari nama file Windows yang bermasalah
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    if name.upper() in reserved_names:
        name = f"video_{name}"

    # Batasi panjang filename
    return name[:180]


def find_existing_file(
    directory: Path,
    preferred_name: Optional[str] = None,
) -> Optional[Path]:
    """
    Mencari file hasil download yang benar-benar ada.
    """

    if preferred_name:
        preferred = Path(preferred_name)

        if preferred.exists() and preferred.is_file():
            return preferred

        candidate = directory / preferred.name

        if candidate.exists() and candidate.is_file():
            return candidate

    candidates = []

    for path in directory.iterdir():
        if not path.is_file():
            continue

        if path.suffix.lower() not in {
            ".mp4",
            ".mkv",
            ".webm",
            ".mov",
            ".avi",
        }:
            continue

        try:
            size = path.stat().st_size
        except OSError:
            continue

        if size <= 1000:
            continue

        candidates.append(path)

    if not candidates:
        return None

    candidates.sort(
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    return candidates[0]


def decode_cookies_to_file() -> Optional[Path]:
    """
    Decode YOUTUBE_COOKIES_B64 ke temporary Netscape cookies file.

    IMPORTANT:
    Jangan pernah print isi cookie ke log.
    """

    encoded = os.getenv("YOUTUBE_COOKIES_B64")

    if not encoded:
        log("YOUTUBE_COOKIES_B64 belum tersedia.")
        return None

    try:
        cookie_bytes = base64.b64decode(
            encoded,
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        log(f"Gagal decode YOUTUBE_COOKIES_B64: {exc}")
        return None

    if not cookie_bytes.strip():
        log("YOUTUBE_COOKIES_B64 kosong setelah decode.")
        return None

    cookie_file = Path(
        tempfile.gettempdir()
    ) / "clipforge_youtube_cookies.txt"

    try:
        cookie_file.write_bytes(cookie_bytes)
    except OSError as exc:
        log(f"Gagal membuat temporary cookie file: {exc}")
        return None

    log("YouTube cookies berhasil disiapkan.")

    return cookie_file


def check_binary(binary: str) -> Optional[str]:
    """
    Mengecek binary seperti ffmpeg / deno.
    """
    path = shutil.which(binary)

    if path:
        return path

    return None


# ============================================================
# YOUTUBE DOWNLOADER
# ============================================================

def download_youtube_video(
    url: str,
    title: str = "video",
) -> str:
    """
    Download video YouTube menggunakan yt-dlp.

    Target:
    - MP4
    - Maksimal 720p
    - Video + audio
    - FFmpeg merge
    - Deno JavaScript runtime
    - yt-dlp-ejs
    - Tidak menggunakan player_client override
    """

    if not url or not url.strip():
        raise ValueError("URL YouTube tidak boleh kosong.")

    url = url.strip()

    safe_title = sanitize_filename(title)

    # ========================================================
    # TEMP DIRECTORY PER DOWNLOAD
    # ========================================================

    job_dir = DOWNLOAD_DIR / safe_title

    job_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    log("=" * 60)
    log("YOUTUBE DOWNLOAD START")
    log("=" * 60)

    log(f"URL    : {url}")
    log(f"Title  : {safe_title}")
    log(f"Output : {job_dir}")

    # ========================================================
    # CHECK FFMPEG
    # ========================================================

    ffmpeg_path = check_binary("ffmpeg")

    if ffmpeg_path:
        log(f"FFmpeg : {ffmpeg_path}")
    else:
        log(
            "WARNING: FFmpeg tidak ditemukan. "
            "yt-dlp mungkin tidak bisa melakukan merge."
        )

    # ========================================================
    # CHECK DENO
    # ========================================================

    deno_path = check_binary("deno")

    if deno_path:
        log(f"Deno   : {deno_path}")
    else:
        log(
            "WARNING: Deno tidak ditemukan. "
            "YouTube extraction mungkin gagal."
        )

    # ========================================================
    # COOKIE SUPPORT
    # ========================================================

    cookie_file = decode_cookies_to_file()

    # ========================================================
    # OUTPUT TEMPLATE
    # ========================================================

    output_template = str(
        job_dir / f"{safe_title}.%(ext)s"
    )

    # ========================================================
    # YT-DLP OPTIONS
    # ========================================================
    #
    # PENTING:
    #
    # JANGAN tambahkan:
    #
    # "extractor_args": {
    #     "youtube": {
    #         "player_client": ["web"]
    #     }
    # }
    #
    # Karena konfigurasi tersebut sebelumnya menyebabkan:
    #
    # "Only images are available for download."
    #
    # CLI test berhasil ketika player_client override
    # tidak digunakan.
    #

    ydl_opts = {
        # ----------------------------------------------------
        # FORMAT
        # ----------------------------------------------------
        #
        # Prioritas:
        #
        # 1. Video MP4 <=720p + audio M4A
        # 2. Single MP4 <=720p
        #
        "format": (
            "bv*[height<=720][ext=mp4]+"
            "ba[ext=m4a]/"
            "b[height<=720][ext=mp4]"
        ),

        # ----------------------------------------------------
        # MERGE
        # ----------------------------------------------------

        "merge_output_format": "mp4",

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        "outtmpl": output_template,

        # ----------------------------------------------------
        # YOUTUBE
        # ----------------------------------------------------

        "noplaylist": True,

        # ----------------------------------------------------
        # RETRIES
        # ----------------------------------------------------

        "retries": 10,
        "fragment_retries": 10,

        # ----------------------------------------------------
        # NETWORK
        # ----------------------------------------------------

        "socket_timeout": 60,
        "continuedl": True,

        # ----------------------------------------------------
        # LOGGING
        # ----------------------------------------------------

        "quiet": False,
        "no_warnings": False,
        "progress": True,

        # ----------------------------------------------------
        # SSL
        # ----------------------------------------------------

        "nocheckcertificate": False,

        # ----------------------------------------------------
        # JAVASCRIPT RUNTIME
        # ----------------------------------------------------
        #
        # YouTube sekarang membutuhkan JS runtime
        # untuk beberapa extraction flow.
        #

        "js_runtimes": {
            "deno": {}
        },

        # ----------------------------------------------------
        # EJS
        # ----------------------------------------------------

        "remote_components": [
            "ejs:npm"
        ],

        # ----------------------------------------------------
        # POSTPROCESSOR
        # ----------------------------------------------------

        "postprocessors": [
            {
                "key": "FFmpegVideoRemuxer",
                "preferedformat": "mp4",
            }
        ],
    }

    # ========================================================
    # COOKIE
    # ========================================================

    if cookie_file:
        ydl_opts["cookiefile"] = str(cookie_file)

    # ========================================================
    # FFMPEG LOCATION
    # ========================================================

    if ffmpeg_path:
        ydl_opts["ffmpeg_location"] = ffmpeg_path

    # ========================================================
    # DENO LOCATION
    # ========================================================

    if deno_path:
        deno_parent = str(Path(deno_path).parent)

        # Tambahkan ke PATH agar subprocess yt-dlp
        # dapat menemukan Deno.
        current_path = os.environ.get("PATH", "")

        if deno_parent not in current_path:
            os.environ["PATH"] = (
                deno_parent
                + os.pathsep
                + current_path
            )

    # ========================================================
    # INFO
    # ========================================================

    log("-" * 60)
    log("Format : MP4 <= 720p")
    log("JavaScript runtime : Deno")
    log("EJS : ejs:npm")
    log("Player client override : NONE")
    log("-" * 60)

    # ========================================================
    # DOWNLOAD
    # ========================================================

    downloaded_info = None

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            downloaded_info = ydl.extract_info(
                url,
                download=True,
            )

    except yt_dlp.utils.DownloadError as exc:

        error_text = str(exc)

        log("=" * 60)
        log("YOUTUBE DOWNLOAD ERROR")
        log("=" * 60)
        log(error_text)

        lower_error = error_text.lower()

        # ----------------------------------------------------
        # FORMAT ERROR
        # ----------------------------------------------------

        if (
            "requested format is not available"
            in lower_error
        ):
            raise RuntimeError(
                "Format video YouTube yang dipilih "
                "tidak tersedia. "
                "Coba gunakan URL video lain."
            ) from exc

        # ----------------------------------------------------
        # AUTH ERROR
        # ----------------------------------------------------

        if (
            "401" in lower_error
            or "unauthorized" in lower_error
        ):
            raise RuntimeError(
                "YouTube menolak request download "
                "(HTTP 401). "
                "Jika video membutuhkan login, "
                "gunakan YOUTUBE_COOKIES_B64."
            ) from exc

        # ----------------------------------------------------
        # FORBIDDEN
        # ----------------------------------------------------

        if (
            "403" in lower_error
            or "forbidden" in lower_error
        ):
            raise RuntimeError(
                "YouTube menolak download "
                "(HTTP 403 Forbidden). "
                "Pastikan yt-dlp, Deno, dan EJS "
                "sudah terpasang."
            ) from exc

        # ----------------------------------------------------
        # EMPTY FILE
        # ----------------------------------------------------

        if "downloaded file is empty" in lower_error:
            raise RuntimeError(
                "YouTube mengembalikan file kosong. "
                "Extraction video gagal."
            ) from exc

        # ----------------------------------------------------
        # GENERIC
        # ----------------------------------------------------

        raise RuntimeError(
            f"Gagal download video dari YouTube: "
            f"{error_text}"
        ) from exc

    except Exception as exc:

        log(
            f"Unexpected downloader error: {exc}"
        )

        raise RuntimeError(
            f"Terjadi error saat download YouTube: {exc}"
        ) from exc

    finally:

        # Cookie temporary dihapus setelah proses.
        if cookie_file:

            try:

                if cookie_file.exists():
                    cookie_file.unlink()

                    log(
                        "Temporary cookie file dihapus."
                    )

            except OSError as exc:

                log(
                    f"WARNING: gagal menghapus cookie temporary: {exc}"
                )

    # ========================================================
    # FIND RESULT
    # ========================================================

    candidates = []

    # --------------------------------------------------------
    # Info filepath
    # --------------------------------------------------------

    if downloaded_info:

        filepath = downloaded_info.get("filepath")

        if filepath:
            candidates.append(
                Path(filepath)
            )

        requested_downloads = (
            downloaded_info.get(
                "requested_downloads"
            )
            or []
        )

        for item in requested_downloads:

            filepath = item.get("filepath")

            if filepath:
                candidates.append(
                    Path(filepath)
                )

    # --------------------------------------------------------
    # Expected merged MP4
    # --------------------------------------------------------

    expected_mp4 = (
        job_dir
        / f"{safe_title}.mp4"
    )

    candidates.insert(
        0,
        expected_mp4,
    )

    # --------------------------------------------------------
    # Check candidates
    # --------------------------------------------------------

    result_file = None

    for candidate in candidates:

        try:

            if (
                candidate.exists()
                and candidate.is_file()
                and candidate.stat().st_size > 1000
            ):
                result_file = candidate
                break

        except OSError:
            continue

    # --------------------------------------------------------
    # Fallback directory scan
    # --------------------------------------------------------

    if result_file is None:

        result_file = find_existing_file(
            job_dir
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    if result_file is None:

        log("=" * 60)
        log("DOWNLOAD SELESAI TAPI FILE TIDAK DITEMUKAN")
        log("=" * 60)

        try:

            files = list(job_dir.iterdir())

            for file in files:

                log(
                    f"Found: {file}"
                )

        except OSError:
            pass

        raise RuntimeError(
            "yt-dlp selesai tetapi file video "
            "hasil download tidak ditemukan."
        )

    # ========================================================
    # VALIDATE FILE SIZE
    # ========================================================

    try:
        file_size = result_file.stat().st_size
    except OSError as exc:
        raise RuntimeError(
            "Tidak dapat membaca ukuran file hasil download."
        ) from exc

    if file_size <= 1000:

        raise RuntimeError(
            "File video hasil download kosong "
            "atau terlalu kecil."
        )

    # ========================================================
    # RENAME TO MP4
    # ========================================================

    final_file = result_file

    if result_file.suffix.lower() != ".mp4":

        target = (
            job_dir
            / f"{safe_title}.mp4"
        )

        try:

            if target.exists():
                target.unlink()

            result_file.rename(target)

            final_file = target

        except OSError as exc:

            log(
                f"WARNING: gagal rename ke MP4: {exc}"
            )

    # ========================================================
    # FINAL LOG
    # ========================================================

    log("=" * 60)
    log("YOUTUBE DOWNLOAD SUCCESS")
    log("=" * 60)

    log(f"File : {final_file}")
    log(
        f"Size : "
        f"{final_file.stat().st_size / (1024 * 1024):.2f} MB"
    )

    log("=" * 60)

    return str(final_file)


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    test_url = os.getenv(
        "TEST_YOUTUBE_URL"
    )

    if not test_url:

        print(
            "Set TEST_YOUTUBE_URL terlebih dahulu."
        )

        print(
            "Contoh:"
        )

        print(
            'set TEST_YOUTUBE_URL=https://youtu.be/xxxxx'
        )

    else:

        result = download_youtube_video(
            test_url,
            "TestPodcast",
        )

        print()
        print("RESULT:")
        print(result)