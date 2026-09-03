from __future__ import annotations

import base64
import os
import tempfile
import traceback
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
    Membuat cookies.txt sementara dari environment variable:

        YOUTUBE_COOKIES_B64

    YOUTUBE_COOKIES_B64 harus berisi cookies.txt
    dalam format Base64.
    """

    cookies_b64 = os.getenv(
        "YOUTUBE_COOKIES_B64"
    )

    if not cookies_b64:
        print(
            "[WARNING] YOUTUBE_COOKIES_B64 belum tersedia."
        )
        return None

    # --------------------------------------------------------
    # Bersihkan whitespace
    # --------------------------------------------------------

    cookies_b64 = "".join(
        cookies_b64.split()
    )

    if not cookies_b64:
        raise RuntimeError(
            "YOUTUBE_COOKIES_B64 kosong."
        )

    # --------------------------------------------------------
    # Decode Base64
    # --------------------------------------------------------

    try:

        cookie_data = base64.b64decode(
            cookies_b64,
            validate=True,
        )

    except Exception as e:

        raise RuntimeError(
            "YOUTUBE_COOKIES_B64 tidak valid. "
            "Pastikan Value berisi Base64 dari cookies.txt. "
            f"Error: {e}"
        ) from e

    if not cookie_data:

        raise RuntimeError(
            "YOUTUBE_COOKIES_B64 menghasilkan data kosong."
        )

    # --------------------------------------------------------
    # Decode untuk validasi
    # --------------------------------------------------------

    cookie_text = cookie_data.decode(
        "utf-8",
        errors="replace",
    )

    # --------------------------------------------------------
    # Validasi Netscape cookie
    # --------------------------------------------------------

    if (
        "# Netscape HTTP Cookie File"
        not in cookie_text
        and "# HTTP Cookie File"
        not in cookie_text
    ):

        print(
            "[WARNING] Cookie tidak memiliki header "
            "Netscape yang umum."
        )

        print(
            "[WARNING] Pastikan cookies yang diekspor "
            "berformat Netscape cookies.txt."
        )

    # --------------------------------------------------------
    # Temporary file
    # --------------------------------------------------------

    temp_file = tempfile.NamedTemporaryFile(
        mode="wb",
        suffix=".txt",
        prefix="yt_cookies_",
        delete=False,
    )

    try:

        temp_file.write(
            cookie_data
        )

        temp_file.flush()

    finally:

        temp_file.close()

    print(
        "[OK] Temporary YouTube cookies dibuat."
    )

    print(
        f"[OK] Cookie size: {len(cookie_data):,} bytes"
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
    - Cookie authentication
    """

    # ========================================================
    # VALIDATE URL
    # ========================================================

    if not url or not url.strip():

        raise ValueError(
            "URL YouTube kosong."
        )

    url = url.strip()

    # ========================================================
    # HEADER
    # ========================================================

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

    print("=" * 70)

    cookie_file: Optional[str] = None

    try:

        # ====================================================
        # CREATE COOKIE
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
            # PLAYLIST
            # ------------------------------------------------

            "noplaylist": True,

            # ------------------------------------------------
            # NETWORK
            # ------------------------------------------------

            "retries": 5,

            "fragment_retries": 5,

            "socket_timeout": 30,

            # ------------------------------------------------
            # LOGGING
            # ------------------------------------------------

            "quiet": False,

            "no_warnings": False,

            "progress": True,

            # ------------------------------------------------
            # SECURITY
            # ------------------------------------------------

            "nocheckcertificate": False,

            # ------------------------------------------------
            # YOUTUBE CLIENT
            # ------------------------------------------------

            "extractor_args": {

                "youtube": {

                    "player_client": [
                        "web",
                        "android",
                    ],

                },

            },

            # ------------------------------------------------
            # JAVASCRIPT RUNTIME
            # ------------------------------------------------

            "js_runtimes": {

                "deno": {},

            },

            # ------------------------------------------------
            # EJS
            # ------------------------------------------------

            "remote_components": [
                "ejs:npm",
            ],

        }

        # ====================================================
        # COOKIE FILE
        # ====================================================

        if cookie_file:

            ydl_opts[
                "cookiefile"
            ] = cookie_file

        # ====================================================
        # PRINT CONFIG
        # ====================================================

        print()
        print(
            "=" * 70
        )

        print(
            "YT-DLP CONFIGURATION"
        )

        print(
            "=" * 70
        )

        print(
            "JavaScript runtime : Deno"
        )

        print(
            "EJS                : ejs:npm"
        )

        print(
            "Cookies             : "
            + (
                "AKTIF"
                if cookie_file
                else "TIDAK AKTIF"
            )
        )

        print(
            "Playlist            : DISABLED"
        )

        print(
            "Output format       : MP4"
        )

        print(
            "=" * 70
        )

        # ====================================================
        # DOWNLOAD
        # ====================================================

        print()
        print(
            "Memulai yt-dlp..."
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
        # VALIDATE INFO
        # ====================================================

        if not info:

            raise RuntimeError(
                "yt-dlp tidak mengembalikan informasi video."
            )

        # ====================================================
        # FIND OUTPUT
        # ====================================================

        final_path: Optional[Path] = None

        # ----------------------------------------------------
        # 1. Requested downloads
        # ----------------------------------------------------

        requested_downloads = info.get(
            "requested_downloads"
        )

        if requested_downloads:

            for item in requested_downloads:

                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                filepath = item.get(
                    "filepath"
                )

                if not filepath:
                    continue

                candidate = Path(
                    filepath
                )

                if candidate.exists():

                    final_path = candidate

                    break

        # ----------------------------------------------------
        # 2. Requested formats
        # ----------------------------------------------------

        if final_path is None:

            requested_formats = info.get(
                "requested_formats"
            )

            if requested_formats:

                for item in requested_formats:

                    if not isinstance(
                        item,
                        dict,
                    ):
                        continue

                    filepath = item.get(
                        "filepath"
                    )

                    if not filepath:
                        continue

                    candidate = Path(
                        filepath
                    )

                    if candidate.exists():

                        final_path = candidate

                        break

        # ----------------------------------------------------
        # 3. _filename
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
        # 4. Prepare filename
        # ----------------------------------------------------

        if final_path is None:

            filepath = info.get(
                "filename"
            )

            if filepath:

                candidate = Path(
                    filepath
                )

                if candidate.exists():

                    final_path = candidate

        # ----------------------------------------------------
        # 5. Search output directory
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
        # VALIDATE FINAL FILE
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
                "Pastikan YOUTUBE_COOKIES_B64 di Railway "
                "berisi Base64 dari cookies.txt yang valid "
                "dan cookie belum expired."
            ) from e

        # ----------------------------------------------------
        # Generic yt-dlp error
        # ----------------------------------------------------

        raise RuntimeError(
            "Gagal download video YouTube: "
            f"{error_message}"
        ) from e

    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as e:

        print()
        print("=" * 70)
        print("YOUTUBE DOWNLOADER ERROR")
        print("=" * 70)

        print(
            f"Error type : {type(e).__name__}"
        )

        print(
            f"Error      : {e}"
        )

        print()

        traceback.print_exc()

        print("=" * 70)

        raise

    # ========================================================
    # CLEANUP
    # ========================================================

    finally:

        if cookie_file:

            try:

                cookie_path = Path(
                    cookie_file
                )

                if cookie_path.exists():

                    cookie_path.unlink()

                    print(
                        "[OK] Temporary cookies dihapus."
                    )

            except Exception as e:

                print(
                    "[WARNING] Gagal menghapus "
                    f"temporary cookies: {e}"
                )