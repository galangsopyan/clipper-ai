from pathlib import Path
import json
import subprocess
import sys
import re
import os
import tempfile


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MEDIA_DIR = BASE_DIR / "media"
INPUT_DIR = MEDIA_DIR / "input"
OUTPUT_DIR = MEDIA_DIR / "output"
CACHE_DIR = MEDIA_DIR / "cache"

VIDEO_FILE = INPUT_DIR / "Podcast.mp4"
CLIPS_FILE = OUTPUT_DIR / "clips.json"
TRANSCRIPT_FILE = CACHE_DIR / "Podcast_transcript.json"

SUBTITLE_DIR = OUTPUT_DIR / "subtitles"

SUBTITLE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# WINDOWS UTF-8
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
# HELPERS
# ============================================================

def run_command(command):
    print()
    print("=" * 70)
    print("FFMPEG")
    print("=" * 70)
    print(" ".join(str(x) for x in command))

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

    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg gagal.\n"
            + result.stderr[-5000:]
        )

    return result


def safe_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default


def escape_ass_text(text):
    if text is None:
        return ""

    text = str(text)

    text = text.replace(
        "\\",
        "\\\\",
    )

    text = text.replace(
        "{",
        "\\{",
    )

    text = text.replace(
        "}",
        "\\}",
    )

    text = text.replace(
        "\n",
        " ",
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def format_ass_time(seconds):
    seconds = max(
        0,
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
        round(
            (seconds - int(seconds))
            * 100
        )
    )

    if centiseconds >= 100:
        centiseconds = 0
        secs += 1

    if secs >= 60:
        secs = 0
        minutes += 1

    if minutes >= 60:
        minutes = 0
        hours += 1

    return (
        f"{hours}:"
        f"{minutes:02d}:"
        f"{secs:02d}."
        f"{centiseconds:02d}"
    )


def split_subtitle(text, max_chars=42):
    text = escape_ass_text(text)

    if not text:
        return ""

    words = text.split()

    lines = []
    current = ""

    for word in words:
        candidate = (
            f"{current} {word}"
            if current
            else word
        )

        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)

            current = word

    if current:
        lines.append(current)

    if len(lines) <= 2:
        return "\\N".join(lines)

    # Batasi maksimal 2 baris
    first = " ".join(
        lines[: len(lines) // 2]
    )

    second = " ".join(
        lines[len(lines) // 2 :]
    )

    return (
        first[:max_chars]
        + "\\N"
        + second[:max_chars]
    )


# ============================================================
# LOAD CLIPS
# ============================================================

def load_clips():
    if not CLIPS_FILE.exists():
        raise RuntimeError(
            f"clips.json tidak ditemukan: {CLIPS_FILE}"
        )

    with CLIPS_FILE.open(
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)

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
        clips = []

    return clips


# ============================================================
# LOAD TRANSCRIPT
# ============================================================

def load_transcript():
    if not TRANSCRIPT_FILE.exists():
        print(
            "[WARNING] Transcript tidak ditemukan."
        )

        return []

    try:
        with TRANSCRIPT_FILE.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        if isinstance(data, dict):
            segments = data.get(
                "segments",
                [],
            )
        elif isinstance(data, list):
            segments = data
        else:
            segments = []

        if not isinstance(
            segments,
            list,
        ):
            return []

        return segments

    except Exception as e:
        print(
            "[WARNING] Gagal membaca transcript:",
            e,
        )

        return []


# ============================================================
# CREATE ASS SUBTITLE
# ============================================================

def create_ass(
    clip,
    transcript,
    output_file,
):
    start = safe_float(
        clip.get("start"),
        0,
    )

    end = safe_float(
        clip.get("end"),
        start + 60,
    )

    if end <= start:
        end = start + 60

    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, TertiaryColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,54,&H00FFFFFF,&H00FFFFFF,&H00000000,&H99000000,-1,0,1,3,1,2,70,70,180,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []

    for segment in transcript:

        seg_start = safe_float(
            segment.get("start"),
        )

        seg_end = safe_float(
            segment.get("end"),
        )

        text = segment.get(
            "text",
            "",
        )

        if (
            seg_start is None
            or seg_end is None
            or not text
        ):
            continue

        # Tidak berhubungan dengan clip
        if seg_end <= start:
            continue

        if seg_start >= end:
            continue

        relative_start = max(
            0,
            seg_start - start,
        )

        relative_end = min(
            end - start,
            seg_end - start,
        )

        if relative_end <= relative_start:
            continue

        subtitle = split_subtitle(
            text
        )

        if not subtitle:
            continue

        events.append(
            "Dialogue: 0,"
            f"{format_ass_time(relative_start)},"
            f"{format_ass_time(relative_end)},"
            "Default,,0,0,0,,"
            f"{subtitle}"
        )

    # Fallback apabila transcript tidak cocok
    if not events:

        text = (
            clip.get("text")
            or clip.get("transcript")
            or clip.get("title")
            or ""
        )

        if text:

            duration = max(
                1,
                end - start,
            )

            subtitle = split_subtitle(
                str(text)
            )

            events.append(
                "Dialogue: 0,"
                "0:00:00.00,"
                f"{format_ass_time(duration)},"
                "Default,,0,0,0,,"
                f"{subtitle}"
            )

    output_file.write_text(
        header
        + "\n".join(events)
        + "\n",
        encoding="utf-8",
    )


# ============================================================
# FIND SOURCE
# ============================================================

def find_source_clip(
    index,
):
    candidates = [
        OUTPUT_DIR
        / f"clip_{index:02d}.mp4",

        OUTPUT_DIR
        / f"clip_{index}.mp4",
    ]

    for path in candidates:
        if path.exists():
            if path.stat().st_size > 1000:
                return path

    return VIDEO_FILE


# ============================================================
# RENDER ONE CLIP
# ============================================================

def render_clip(
    index,
    clip,
    transcript,
):
    output_file = (
        OUTPUT_DIR
        / f"clip_{index:02d}_vertical.mp4"
    )

    subtitle_file = (
        SUBTITLE_DIR
        / f"clip_{index:02d}.ass"
    )

    start = safe_float(
        clip.get("start"),
        0,
    )

    end = safe_float(
        clip.get("end"),
        start + 60,
    )

    if end <= start:
        end = start + 60

    duration = end - start

    if duration <= 0:
        raise RuntimeError(
            f"Clip #{index} memiliki duration invalid."
        )

    create_ass(
        clip,
        transcript,
        subtitle_file,
    )

    source = find_source_clip(
        index
    )

    # ========================================================
    # SOURCE CLIP SUDAH DIPOTONG
    # ========================================================

    if source != VIDEO_FILE:

        input_args = [
            "-i",
            str(source),
        ]

        duration_args = []

    # ========================================================
    # SOURCE = PODCAST ORIGINAL
    # ========================================================

    else:

        input_args = [
            "-ss",
            str(start),
            "-i",
            str(VIDEO_FILE),
        ]

        duration_args = [
            "-t",
            str(duration),
        ]

    subtitle_path = str(
        subtitle_file
    ).replace(
        "\\",
        "/",
    )

    # Windows drive compatibility
    subtitle_path = subtitle_path.replace(
        ":",
        "\\:",
        1,
    )

    vf = (
        "scale=1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        f"subtitles='{subtitle_path}'"
    )

    temp_output = (
        OUTPUT_DIR
        / f".tmp_clip_{index:02d}_vertical.mp4"
    )

    if temp_output.exists():
        try:
            temp_output.unlink()
        except Exception:
            pass

    command = [
        "ffmpeg",
        "-y",
        *input_args,
        *duration_args,
        "-vf",
        vf,
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(temp_output),
    ]

    print()
    print(
        f"[RENDER] Clip #{index}"
    )
    print(
        f"Start    : {start:.2f}"
    )
    print(
        f"End      : {end:.2f}"
    )
    print(
        f"Duration : {duration:.2f}"
    )
    print(
        f"Title    : "
        f"{clip.get('title', '')}"
    )

    run_command(
        command
    )

    if not temp_output.exists():
        raise RuntimeError(
            f"Output temporary clip #{index} "
            "tidak dibuat."
        )

    if temp_output.stat().st_size <= 1000:
        raise RuntimeError(
            f"Output clip #{index} terlalu kecil."
        )

    # Atomic-ish replace
    if output_file.exists():
        try:
            output_file.unlink()
        except Exception:
            pass

    temp_output.replace(
        output_file
    )

    print(
        f"[OK] {output_file}"
    )

    return output_file


# ============================================================
# VERIFY
# ============================================================

def verify_outputs():
    missing = []

    valid = []

    for index in range(1, 6):

        path = (
            OUTPUT_DIR
            / f"clip_{index:02d}_vertical.mp4"
        )

        if not path.exists():
            missing.append(index)
            continue

        size = path.stat().st_size

        if size <= 1000:
            missing.append(index)
            continue

        valid.append(index)

    print()
    print("=" * 70)
    print("VERTICAL OUTPUT VERIFICATION")
    print("=" * 70)

    print(
        f"Valid : {len(valid)}/5"
    )

    if valid:
        print(
            "Available:",
            ", ".join(
                f"#{x}"
                for x in valid
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

    return valid, missing


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "CLIPFORGE AI - REPAIR VERTICAL RENDERER"
    )
    print("=" * 70)

    if not VIDEO_FILE.exists():
        raise RuntimeError(
            f"Podcast.mp4 tidak ditemukan:\n"
            f"{VIDEO_FILE}"
        )

    clips = load_clips()

    if len(clips) < 5:
        raise RuntimeError(
            "Viral/clip metadata hanya memiliki "
            f"{len(clips)} clip. "
            "Minimal harus tersedia 5 kandidat."
        )

    clips = clips[:5]

    transcript = load_transcript()

    print(
        f"[INFO] Kandidat : {len(clips)}"
    )

    print(
        f"[INFO] Transcript segments : "
        f"{len(transcript)}"
    )

    # ========================================================
    # RENDER ONLY MISSING
    # ========================================================

    valid, missing = verify_outputs()

    if not missing:
        print()
        print(
            "[OK] Semua Top 5 sudah tersedia."
        )

        return

    for index in missing:

        clip = clips[index - 1]

        render_clip(
            index,
            clip,
            transcript,
        )

    # ========================================================
    # FINAL VERIFY
    # ========================================================

    valid, missing = verify_outputs()

    if len(valid) != 5:

        raise RuntimeError(
            "Gagal menghasilkan seluruh Top 5. "
            f"Hasil: {len(valid)}/5. "
            f"Missing: {missing}"
        )

    print()
    print("=" * 70)
    print(
        "SUCCESS - TOP 5 VERTICAL CLIPS READY"
    )
    print("=" * 70)

    for index in range(1, 6):

        path = (
            OUTPUT_DIR
            / f"clip_{index:02d}_vertical.mp4"
        )

        print(
            f"[OK] #{index} "
            f"{path.stat().st_size:,} bytes"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print()
        print(
            "=" * 70
        )
        print(
            "RENDER FAILED"
        )
        print(
            "=" * 70
        )
        print(e)
        sys.exit(1)