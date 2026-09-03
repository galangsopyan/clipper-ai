from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path
from typing import Optional

import yt_dlp


# ============================================================
# CONFIG
# ============================================================

DOWNLOAD_DIR = Path(
    os.getenv(
        "DOWNLOAD_DIR",
        "/tmp/clips",
    )
)

DOWNLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# COOKIE HANDLING
# ============================================================

def create_cookie_file() -> Optional[str]:
    """
    Membuat cookies.txt temporary dari:

        YOUTUBE_COOKIES_B64

    Variable tersebut harus berisi isi cookies.txt
    yang sudah di-Base64.
    """

    cookies_b64 = os.getenv(
        "YOUTUBE_COOKIES_B64"
    )

    if not cookies_b64:
        print(
            "[WARNING] YOUTUBE_COOKIES_B64 belum tersedia."
        )
        return None

    try:
        cookie_data = base64.b64decode(
            cookies_b64,
            validate=True,
        )

    except Exception as e:
        raise RuntimeError(
            "YOUTUBE_COOKIES_B64 tidak valid. "
            f"Pastikan Value berisi Base64 dari cookies.txt. Error: {e}"
        ) from e

    if not cookie_data:
        raise RuntimeError(
            "YOUTUBE_COOKIES_B64 kosong."
        )

    # --------------------------------------------------------
    # Validasi sederhana format Netscape cookies
    # --------------------------------------------------------

    cookie_text = cookie_data.decode(
        "utf-8",
        errors="replace",
    )

    if (
        "# Netscape HTTP Cookie File"
        not in cookie_text
        and "# HTTP Cookie File"
        not in cookie_text
    ):
        print(
            "[WARNING] File cookie tidak terlihat seperti "
            "Netscape cookies.txt."
        )

    # --------------------------------------------------------
    # Temporary cookie file
    # --------------------------------------------------------

    temp_file = tempfile.NamedTemporaryFile(
        mode="wb",
        suffix=".txt",
        prefix="yt_cookies_",
        delete=False,
    )

    try:
        temp_file.write(cookie_data)
        temp_file.flush()

    finally:
        temp_file.close()

    print(
        "[OK] Temporary YouTube cookies dibuat."
    )

    return temp_file.name


# ============================================================
# DOWNLOAD
# ============================================================

def download_youtube_video(
    url: str,
    output_name: str = "Podcast",
) -> Path:
    """
    Download video YouTube menggunakan yt-dlp.

    Support:
    - Railway
    - YOUTUBE_COOKIES_B64
    - Deno
    - EJS
    - FFmpeg
    - MP4
    """

    if not url:
        raise ValueError(
            "URL YouTube kosong."
        )

    print()
    print("=" * 70)
    print("YOUTUBE DOWNLOADER")
    print("=" * 70)

    print(
        f"URL    : {url}"
    )

    print(
        f"Output : {DOWNLOAD_DIR}"
    )

    cookie_file = None

    try:

        # ====================================================
        # COOKIE
        # ====================================================

        cookie_file = create_cookie_file()

        if cookie_file:

            print(
                "[OK] YouTube cookies: AKTIF"
            )

        else:

            print(
                "[WARNING] YouTube cookies: TIDAK AKTIF"
            )

        # ====================================================
        # OUTPUT
        # ====================================================

        output_template = str(
            DOWNLOAD_DIR
            / f"{output_name}.%(ext)s"
        )

        # ====================================================
        # YT-DLP OPTIONS
        # ====================================================

        ydl_opts = {

            # ------------------------------------------------
            # FORMAT
            # ------------------------------------------------

            "format": (
                "bv*[ext=mp4]+ba[ext=m4a]/"
                "b[ext=mp4]/"
                "best"
            ),

            "merge_output_format": "mp4",

            # ------------------------------------------------
            # OUTPUT
            # ------------------------------------------------

            "outtmpl": output_template,

            # ------------------------------------------------
            # YOUTUBE
            # ------------------------------------------------

            "extractor_args": {
                "youtube": {
                    "player_client": [
                        "web",
                        "android",
                    ],
                }
            },

            # ------------------------------------------------
            # JAVASCRIPT / EJS
            # ------------------------------------------------

            "js_runtimes": {
                "deno": {},
            },

            "remote_components": [
                "ejs:npm",
            ],

            # ------------------------------------------------
            # NETWORK
            # ------------------------------------------------

            "retries": 5,

            "fragment_retries": 5,

            "socket_timeout": 30,

            # ------------------------------------------------
            # PLAYLIST
            # ------------------------------------------------

            "noplaylist": True,

            # ------------------------------------------------
            # SECURITY
            # ------------------------------------------------

            "nocheckcertificate": False,

            # ------------------------------------------------
            # LOGGING
            # ------------------------------------------------

            "quiet": False,

            "no_warnings": False,

            "progress": True,
        }

        # ====================================================
        # COOKIES
        # ====================================================

        if cookie_file:

            ydl_opts[
                "cookiefile"
            ] = cookie_file

        # ====================================================
        # DOWNLOAD
        # ====================================================

        print()
        print(
            "Memulai yt-dlp..."
        )

        print(
            "JavaScript runtime : Deno"
        )

        print(
            "Cookies            : "
            + (
                "AKTIF"
                if cookie_file
                else "TIDAK AKTIF"
            )
        )

        print()

        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            info = ydl.extract_info(
                url,
                download=True,
            )

        # ====================================================
        # FIND OUTPUT
        # ====================================================

        final_path: Optional[Path] = None

        # ----------------------------------------------------
        # Requested downloads
        # ----------------------------------------------------

        requested_downloads = info.get(
            "requested_downloads"
        )

        if requested_downloads:

            for item in requested_downloads:

                filepath = item.get(
                    "filepath"
                )

                if filepath:

                    candidate = Path(
                        filepath
                    )

                    if candidate.exists():

                        final_path = candidate

                        break

        # ----------------------------------------------------
        # Requested formats
        # ----------------------------------------------------

        if final_path is None:

            requested_formats = info.get(
                "requested_formats"
            )

            if requested_formats:

                for item in requested_formats:

                    filepath = item.get(
                        "filepath"
                    )

                    if filepath:

                        candidate = Path(
                            filepath
                        )

                        if candidate.exists():

                            final_path = candidate

                            break

        # ----------------------------------------------------
        # Direct filepath
        # ----------------------------------------------------

        if final_path is None:

            filepath = info.get(
                "_filename"
            )

            if filepath:

                candidate = Path(
                    filepath
                )

                if candidate.exists():

                    final_path = candidate

        # ----------------------------------------------------
        # Search directory
        # ----------------------------------------------------

        if final_path is None:

            candidates = [
                p
                for p in DOWNLOAD_DIR.glob(
                    f"{output_name}.*"
                )
                if p.is_file()
            ]

            if candidates:

                final_path = max(
                    candidates,
                    key=lambda p: p.stat().st_mtime,
                )

        # ====================================================
        # VALIDATION
        # ====================================================

        if (
            final_path is None
            or not final_path.exists()
        ):

            raise RuntimeError(
                "yt-dlp selesai tetapi file video "
                "tidak ditemukan."
            )

        file_size = final_path.stat().st_size

        if file_size <= 0:

            raise RuntimeError(
                "File video hasil download kosong."
            )

        # ====================================================
        # SUCCESS
        # ====================================================

        print()
        print("=" * 70)
        print("DOWNLOAD BERHASIL")
        print("=" * 70)

        print(
            f"File : {final_path}"
        )

        print(
            f"Size : {file_size:,} bytes"
        )

        print("=" * 70)

        return final_path

    # ========================================================
    # YT-DLP ERROR
    # ========================================================

    except yt_dlp.utils.DownloadError as e:

        error_message = str(e)

        print()
        print("=" * 70)
        print("DOWNLOAD YOUTUBE GAGAL")
        print("=" * 70)

        print(
            error_message
        )

        print("=" * 70)

        # ----------------------------------------------------
        # Authentication
        # ----------------------------------------------------

        authentication_error = (
            "Sign in to confirm"
            in error_message
            or "not a bot"
            in error_message
            or "cookies"
            in error_message.lower()
        )

        if authentication_error:

            raise RuntimeError(
                "YouTube meminta autentikasi. "
                "Pastikan YOUTUBE_COOKIES_B64 "
                "sudah tersedia di Railway Variables "
                "dan berasal dari cookies.txt yang valid."
            ) from e

        raise RuntimeError(
            "Gagal download video YouTube: "
            f"{error_message}"
        ) from e

    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as e:

        print()
        print(
            f"[ERROR] {e}"
        )

        raise

    # ========================================================
    # CLEANUP
    # ========================================================

    finally:

        if cookie_file:

            try:

                Path(
                    cookie_file
                ).unlink(
                    missing_ok=True
                )

                print(
                    "[OK] Temporary cookies dihapus."
                )

            except Exception as e:

                print(
                    "[WARNING] Gagal menghapus "
                    f"temporary cookies: {e}"
                )