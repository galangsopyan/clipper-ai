from pathlib import Path
import subprocess
import json


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]


# ============================================================
# GET TRANSCRIPT SEGMENTS
# ============================================================

def get_segments(
    transcript_file: Path,
    start: float,
    end: float,
):

    with transcript_file.open(
        "r",
        encoding="utf-8",
    ) as f:

        data = json.load(f)

    segments = data.get(
        "segments",
        [],
    )

    result = []

    for segment in segments:

        try:

            seg_start = float(
                segment["start"]
            )

            seg_end = float(
                segment["end"]
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):

            continue

        # Tidak overlap
        if seg_end <= start:
            continue

        if seg_start >= end:
            continue

        text = str(
            segment.get(
                "text",
                "",
            )
        ).strip()

        if not text:
            continue

        result.append(
            {
                "start": max(
                    seg_start,
                    start,
                ),
                "end": min(
                    seg_end,
                    end,
                ),
                "text": text,
            }
        )

    return result


# ============================================================
# ASS TIME
# ============================================================

def ass_time(
    seconds: float,
) -> str:

    seconds = max(
        0.0,
        float(seconds),
    )

    hours = int(
        seconds // 3600
    )

    minutes = int(
        (seconds % 3600) // 60
    )

    secs = int(
        seconds % 60
    )

    centiseconds = int(
        (seconds - int(seconds)) * 100
    )

    return (
        f"{hours}:"
        f"{minutes:02d}:"
        f"{secs:02d}."
        f"{centiseconds:02d}"
    )


# ============================================================
# ESCAPE ASS TEXT
# ============================================================

def escape_ass_text(
    text: str,
) -> str:

    text = str(text)

    # ASS override block harus di-escape
    text = text.replace(
        "\\",
        r"\\",
    )

    text = text.replace(
        "{",
        r"\{",
    )

    text = text.replace(
        "}",
        r"\}",
    )

    return text


# ============================================================
# CREATE ASS SUBTITLE
# ============================================================

def create_ass_subtitle(
    segments,
    output_file: Path,
    clip_start: float,
):

    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding

Style: Default,Arial,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&HCC000000,1,0,0,0,100,100,0,0,1,5,3,2,90,90,300,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = [
        header
    ]

    for segment in segments:

        start = max(
            0.0,
            float(segment["start"])
            - clip_start,
        )

        end = max(
            start + 0.2,
            float(segment["end"])
            - clip_start,
        )

        text = escape_ass_text(
            segment["text"]
        )

        # ----------------------------------------------------
        # Batasi panjang subtitle
        # ----------------------------------------------------

        words = text.split()

        if len(words) > 12:

            chunks = []

            for i in range(
                0,
                len(words),
                6,
            ):

                chunks.append(
                    " ".join(
                        words[
                            i:i + 6
                        ]
                    )
                )

            text = (
                r"\N"
            ).join(
                chunks
            )

        lines.append(
            f"Dialogue: 0,"
            f"{ass_time(start)},"
            f"{ass_time(end)},"
            f"Default,,0,0,0,,"
            f"{text}"
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ============================================================
# ESCAPE FFMPEG SUBTITLE PATH
# ============================================================

def escape_ffmpeg_subtitle_path(
    path: Path,
) -> str:

    value = (
        path.resolve()
        .as_posix()
    )

    # Windows drive:
    # D:/clipper-ai/...
    #
    # FFmpeg subtitles filter:
    # D\:/clipper-ai/...

    value = value.replace(
        ":",
        r"\:",
    )

    value = value.replace(
        "'",
        r"\'",
    )

    return value


# ============================================================
# RENDER VERTICAL CLIP
# ============================================================

def render_vertical_clip(
    input_video: Path,
    output_video: Path,
    subtitle_file: Path,
    start: float,
    end: float,
):

    duration = (
        float(end)
        - float(start)
    )

    if duration <= 0:

        raise ValueError(
            "Duration clip harus lebih dari 0."
        )

    output_video.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # CHECK INPUTS
    # ========================================================

    if not input_video.exists():

        raise FileNotFoundError(
            f"Input video tidak ditemukan:\n"
            f"{input_video}"
        )

    if not subtitle_file.exists():

        raise FileNotFoundError(
            f"Subtitle tidak ditemukan:\n"
            f"{subtitle_file}"
        )

    # ========================================================
    # SUBTITLE PATH
    # ========================================================

    subtitle_path = (
        escape_ffmpeg_subtitle_path(
            subtitle_file
        )
    )

    # ========================================================
    # VERTICAL VIDEO
    # ========================================================

    video_filter = (
        "scale=1920:1080,"
        "crop=608:1080:"
        "(iw-608)/2:0,"
        "scale=1080:1920,"
        f"subtitles='{subtitle_path}'"
    )

    # ========================================================
    # FFMPEG
    # ========================================================

    command = [
        "ffmpeg",

        "-y",

        "-ss",
        str(start),

        "-i",
        str(input_video),

        "-t",
        str(duration),

        "-vf",
        video_filter,

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "20",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-movflags",
        "+faststart",

        str(output_video),
    ]

    print()
    print(
        "FFmpeg rendering..."
    )

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
        "Format   : 1080x1920 (9:16)"
    )

    print(
        f"Subtitle : {subtitle_file.name}"
    )

    print(
        f"Output   : {output_video}"
    )

    # ========================================================
    # RUN
    # ========================================================

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # ========================================================
    # OUTPUT LOG
    # ========================================================

    if result.stdout:
        print(result.stdout)

    if result.returncode != 0:

        if result.stderr:
            print(result.stderr)

        raise RuntimeError(
            "FFmpeg gagal merender video.\n"
            f"{result.stderr[-5000:]}"
        )

    # ========================================================
    # VERIFY
    # ========================================================

    if not output_video.exists():

        raise RuntimeError(
            "Video output tidak berhasil dibuat."
        )

    size = output_video.stat().st_size

    if size <= 1000:

        raise RuntimeError(
            "Video output terlalu kecil."
        )

    print(
        f"✓ Render selesai: "
        f"{output_video.name}"
    )

    print(
        f"✓ Size: {size:,} bytes"
    )