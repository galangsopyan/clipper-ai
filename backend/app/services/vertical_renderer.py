from pathlib import Path
import json
import subprocess


# ============================================================
# COLORS - ASS FORMAT
# ============================================================

WHITE = "&H00FFFFFF&"
YELLOW = "&H0000FFFF&"
DARK = "&H00101010&"
TRANSPARENT_DARK = "&HCC101010&"


# ============================================================
# LOAD TRANSCRIPT
# ============================================================

def load_transcript(transcript_file):
    """
    Load transcript JSON.

    Expected structure:

    {
        "segments": [
            {
                "start": 123.45,
                "end": 125.67,
                "text": "...",
                "words": [
                    {
                        "start": 123.45,
                        "end": 123.80,
                        "word": "Halo",
                        "probability": 0.98
                    }
                ]
            }
        ]
    }
    """

    transcript_file = Path(transcript_file)

    if not transcript_file.exists():
        raise FileNotFoundError(
            f"Transcript tidak ditemukan: {transcript_file}"
        )

    try:
        data = json.loads(
            transcript_file.read_text(
                encoding="utf-8-sig"
            )
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Transcript JSON tidak valid: {transcript_file}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            "Format transcript harus berupa object/dict."
        )

    segments = data.get("segments")

    if not isinstance(segments, list):
        raise ValueError(
            "Transcript tidak memiliki 'segments' yang valid."
        )

    if not segments:
        raise ValueError(
            "Transcript tidak memiliki segment."
        )

    return data


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_word(word):
    """
    Membersihkan word timestamp Whisper.
    """

    if word is None:
        return ""

    text = str(word).strip()

    # Hilangkan whitespace berlebih
    text = " ".join(text.split())

    return text


def escape_ass_text(text):
    """
    Escape karakter khusus ASS.
    """

    if text is None:
        return ""

    text = str(text)

    # ASS menggunakan \N sebagai newline.
    # Backslash lain perlu dihindari agar tidak dianggap override tag.
    text = text.replace("\\", r"\\")

    # Jangan sampai koma diubah karena koma valid di dialogue field.
    return text


# ============================================================
# ASS TIME
# ============================================================

def ass_time(seconds):
    """
    Convert seconds -> H:MM:SS.cc

    Contoh:
        0.0    -> 0:00:00.00
        1.25   -> 0:00:01.25
        65.50  -> 0:01:05.50
    """

    try:
        seconds = float(seconds)
    except (TypeError, ValueError):
        seconds = 0.0

    if seconds < 0:
        seconds = 0.0

    # ASS memakai centisecond
    total_cs = int(round(seconds * 100))

    hours = total_cs // 360000
    remaining = total_cs % 360000

    minutes = remaining // 6000
    remaining %= 6000

    secs = remaining // 100
    centis = remaining % 100

    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


# ============================================================
# GET WORDS
# ============================================================

def get_words(
    transcript_file,
    clip_start,
    clip_end,
):
    """
    Mengambil word-level timestamp yang berada di dalam clip.

    IMPORTANT:
    Timestamp yang dikembalikan tetap menggunakan waktu ABSOLUT
    video asli.

    Konversi ke waktu relatif dilakukan saat membuat ASS.
    """

    transcript = load_transcript(
        transcript_file
    )

    words = []

    clip_start = float(clip_start)
    clip_end = float(clip_end)

    for segment in transcript["segments"]:

        try:
            segment_start = float(
                segment.get("start", 0.0)
            )

            segment_end = float(
                segment.get("end", 0.0)
            )
        except (TypeError, ValueError):
            continue

        # Segment tidak overlap dengan clip
        if segment_end <= clip_start:
            continue

        if segment_start >= clip_end:
            continue

        segment_words = segment.get("words", [])

        if not isinstance(segment_words, list):
            continue

        for word_data in segment_words:

            if not isinstance(word_data, dict):
                continue

            try:
                start = float(
                    word_data.get("start")
                )

                end = float(
                    word_data.get("end")
                )
            except (TypeError, ValueError):
                continue

            text = clean_word(
                word_data.get("word", "")
            )

            if not text:
                continue

            # Word tidak overlap clip
            if end <= clip_start:
                continue

            if start >= clip_end:
                continue

            # Clamp ke batas clip
            start = max(
                start,
                clip_start,
            )

            end = min(
                end,
                clip_end,
            )

            if end <= start:
                continue

            try:
                probability = float(
                    word_data.get(
                        "probability",
                        1.0,
                    )
                )
            except (TypeError, ValueError):
                probability = 1.0

            words.append(
                {
                    "start": start,
                    "end": end,
                    "word": text,
                    "probability": probability,
                }
            )

    words.sort(
        key=lambda item: (
            item["start"],
            item["end"],
        )
    )

    return words


# ============================================================
# SEGMENT FALLBACK
# ============================================================

def get_segments_fallback(
    transcript_file,
    clip_start,
    clip_end,
):
    """
    Fallback apabila word-level timestamp tidak tersedia.
    """

    transcript = load_transcript(
        transcript_file
    )

    clip_start = float(clip_start)
    clip_end = float(clip_end)

    segments = []

    for segment in transcript["segments"]:

        try:
            start = float(
                segment.get("start", 0.0)
            )

            end = float(
                segment.get("end", 0.0)
            )
        except (TypeError, ValueError):
            continue

        if end <= clip_start:
            continue

        if start >= clip_end:
            continue

        text = str(
            segment.get("text", "")
        ).strip()

        if not text:
            continue

        start = max(
            start,
            clip_start,
        )

        end = min(
            end,
            clip_end,
        )

        if end <= start:
            continue

        segments.append(
            {
                "start": start,
                "end": end,
                "text": text,
            }
        )

    segments.sort(
        key=lambda item: item["start"]
    )

    return segments


# ============================================================
# COMPATIBILITY WRAPPER
# ============================================================

def get_segments(
    transcript_file,
    start=0.0,
    end=float("inf"),
):
    """
    Compatibility wrapper.
    """

    return get_segments_fallback(
        transcript_file,
        start,
        end,
    )


# ============================================================
# CAPTION GROUPING
# ============================================================

def build_caption_groups(
    words,
    max_words=7,
    max_chars=34,
):
    """
    Menggabungkan word menjadi group subtitle.

    Contoh:

    Saya ingin pergi
    ke sana sekarang

    bukan:

    Saya
    ingin
    pergi
    ...
    """

    groups = []
    current = []
    current_chars = 0

    for word in words:

        text = clean_word(
            word.get("word", "")
        )

        if not text:
            continue

        added_chars = len(text)

        if current:
            added_chars += 1

        should_split = (
            current
            and (
                len(current) >= max_words
                or current_chars + added_chars > max_chars
            )
        )

        if should_split:
            groups.append(current)

            current = []
            current_chars = 0

        current.append(word)

        current_chars += (
            len(text)
            + (1 if len(current) > 1 else 0)
        )

    if current:
        groups.append(current)

    return groups


# ============================================================
# TWO LINE SPLITTER
# ============================================================

def split_two_lines(words):
    """
    Membagi group menjadi maksimal 2 baris
    berdasarkan jumlah karakter.

    Return:
        first_line_indices
        second_line_indices
    """

    if not words:
        return [], []

    if len(words) == 1:
        return [0], []

    total_chars = sum(
        len(
            clean_word(
                word.get("word", "")
            )
        )
        for word in words
    )

    total_spaces = max(
        0,
        len(words) - 1,
    )

    total_length = (
        total_chars
        + total_spaces
    )

    target = total_length / 2

    best_index = 1
    best_difference = float("inf")

    current_length = 0

    for i in range(
        1,
        len(words),
    ):

        text = clean_word(
            words[i - 1].get(
                "word",
                "",
            )
        )

        current_length += len(text)

        if i > 1:
            current_length += 1

        difference = abs(
            current_length - target
        )

        if difference < best_difference:
            best_difference = difference
            best_index = i

    first = list(
        range(
            0,
            best_index,
        )
    )

    second = list(
        range(
            best_index,
            len(words),
        )
    )

    return first, second


# ============================================================
# BUILD LINE TEXT
# ============================================================

def build_line_text(
    words,
    active_index=None,
):
    """
    Membuat teks ASS.

    Active word:
        Kuning + sedikit scale

    Word biasa:
        Putih
    """

    if not words:
        return ""

    first_indices, second_indices = (
        split_two_lines(words)
    )

    def render_indices(indices):
        rendered = []

        for index in indices:

            word = clean_word(
                words[index].get(
                    "word",
                    "",
                )
            )

            if not word:
                continue

            word = escape_ass_text(
                word
            )

            if index == active_index:

                rendered.append(
                    r"{\c&H0000FFFF&\3c&H00101010&\bord3\shad2\fscx108\fscy108}"
                    + word
                    + r"{\rPremium}"
                )

            else:
                rendered.append(word)

        return " ".join(rendered)

    first_line = render_indices(
        first_indices
    )

    second_line = render_indices(
        second_indices
    )

    if second_line:
        return (
            first_line
            + r"\N"
            + second_line
        )

    return first_line


# ============================================================
# BUILD TWO LINE ASS
# ============================================================

def build_two_line_ass(
    words,
    active_index=None,
):
    """
    Compatibility helper.
    """

    return build_line_text(
        words,
        active_index,
    )


# ============================================================
# CREATE ASS SUBTITLE
# ============================================================

def create_ass_subtitle(
    transcript_file,
    output_file,
    clip_start,
    clip_end,
):
    """
    Membuat file ASS subtitle untuk clip.

    ============================================================
    IMPORTANT FIX
    ============================================================

    Transcript menggunakan absolute timestamp:

        20:01.32
        20:02.42

    Sedangkan video clip dimulai dari:

        00:00.00

    Maka:

        relative_time = absolute_time - clip_start

    Ini adalah perbaikan utama dari bug subtitle sebelumnya.
    """

    transcript_file = Path(
        transcript_file
    )

    output_file = Path(
        output_file
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    clip_start = float(
        clip_start
    )

    clip_end = float(
        clip_end
    )

    clip_duration = max(
        0.0,
        clip_end - clip_start,
    )

    # ========================================================
    # GET WORDS
    # ========================================================

    words = get_words(
        transcript_file,
        clip_start,
        clip_end,
    )

    lines = []

    # ========================================================
    # ASS HEADER
    # ========================================================

    lines.extend(
        [
            "[Script Info]",
            "ScriptType: v4.00+",
            "PlayResX: 1080",
            "PlayResY: 1920",
            "ScaledBorderAndShadow: yes",
            "WrapStyle: 2",
            "YCbCr Matrix: TV.709",
            "",
            "[V4+ Styles]",
            (
                "Format: Name, Fontname, Fontsize, "
                "PrimaryColour, SecondaryColour, "
                "OutlineColour, BackColour, Bold, Italic, "
                "Underline, StrikeOut, ScaleX, ScaleY, "
                "Spacing, Angle, BorderStyle, Outline, Shadow, "
                "Alignment, MarginL, MarginR, MarginV, Encoding"
            ),
            (
                "Style: Premium,Arial,76,"
                "&H00FFFFFF&,"
                "&H00FFFFFF&,"
                "&H00101010&,"
                "&HCC101010&,"
                "1,0,0,0,"
                "100,100,1,0,1,3,2,2,"
                "80,80,300,1"
            ),
            "",
            "[Events]",
            (
                "Format: Layer, Start, End, Style, Name, "
                "MarginL, MarginR, MarginV, Effect, Text"
            ),
        ]
    )

    # ========================================================
    # WORD LEVEL SUBTITLE
    # ========================================================

    if words:

        groups = build_caption_groups(
            words,
            max_words=7,
            max_chars=34,
        )

        for group in groups:

            if not group:
                continue

            # ------------------------------------------------
            # ABSOLUTE TIME
            # ------------------------------------------------

            absolute_start = float(
                group[0]["start"]
            )

            absolute_end = float(
                group[-1]["end"]
            )

            # ------------------------------------------------
            # RELATIVE TIME
            #
            # THIS IS THE IMPORTANT FIX
            # ------------------------------------------------

            relative_start = (
                absolute_start
                - clip_start
            )

            relative_end = (
                absolute_end
                - clip_start
            )

            # Clamp
            relative_start = max(
                0.0,
                relative_start,
            )

            relative_end = min(
                clip_duration,
                relative_end,
            )

            if relative_end <= relative_start:
                continue

            # ------------------------------------------------
            # BASE CAPTION
            # ------------------------------------------------

            base_text = build_line_text(
                group,
                active_index=None,
            )

            if base_text:

                lines.append(
                    "Dialogue: 0,"
                    f"{ass_time(relative_start)},"
                    f"{ass_time(relative_end)},"
                    "Premium,,80,80,300,,"
                    f"{base_text}"
                )

            # ------------------------------------------------
            # ACTIVE WORD LAYER
            # ------------------------------------------------

            for index, word in enumerate(group):

                try:
                    word_absolute_start = float(
                        word["start"]
                    )

                    word_absolute_end = float(
                        word["end"]
                    )
                except (
                    TypeError,
                    ValueError,
                    KeyError,
                ):
                    continue

                # Convert absolute -> relative
                word_relative_start = (
                    word_absolute_start
                    - clip_start
                )

                word_relative_end = (
                    word_absolute_end
                    - clip_start
                )

                # Clamp
                word_relative_start = max(
                    0.0,
                    word_relative_start,
                )

                word_relative_end = min(
                    clip_duration,
                    word_relative_end,
                )

                if (
                    word_relative_end
                    <= word_relative_start
                ):
                    continue

                active_text = build_line_text(
                    group,
                    active_index=index,
                )

                if not active_text:
                    continue

                lines.append(
                    "Dialogue: 1,"
                    f"{ass_time(word_relative_start)},"
                    f"{ass_time(word_relative_end)},"
                    "Premium,,80,80,300,,"
                    f"{active_text}"
                )

    # ========================================================
    # FALLBACK SEGMENT SUBTITLE
    # ========================================================

    else:

        segments = get_segments_fallback(
            transcript_file,
            clip_start,
            clip_end,
        )

        for segment in segments:

            absolute_start = float(
                segment["start"]
            )

            absolute_end = float(
                segment["end"]
            )

            # IMPORTANT:
            # Absolute -> relative
            relative_start = (
                absolute_start
                - clip_start
            )

            relative_end = (
                absolute_end
                - clip_start
            )

            relative_start = max(
                0.0,
                relative_start,
            )

            relative_end = min(
                clip_duration,
                relative_end,
            )

            if relative_end <= relative_start:
                continue

            text = escape_ass_text(
                segment.get(
                    "text",
                    "",
                ).strip()
            )

            if not text:
                continue

            lines.append(
                "Dialogue: 0,"
                f"{ass_time(relative_start)},"
                f"{ass_time(relative_end)},"
                "Premium,,80,80,300,,"
                f"{text}"
            )

    # ========================================================
    # WRITE ASS FILE
    # ========================================================

    output_file.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8-sig",
    )

    return output_file


# ============================================================
# ESCAPE FFMPEG SUBTITLE PATH
# ============================================================

def escape_ffmpeg_subtitle_path(
    subtitle_file
):
    """
    Escape path agar aman digunakan
    pada FFmpeg subtitles filter.
    """

    path = str(
        Path(subtitle_file).resolve()
    )

    # FFmpeg filter memakai :
    # sebagai separator sehingga Windows drive
    # harus di-escape.

    path = path.replace("\\", "/")

    path = path.replace(
        ":",
        r"\:"
    )

    path = path.replace(
        "'",
        r"\'"
    )

    return path


# ============================================================
# GET VIDEO DURATION
# ============================================================

def get_video_duration(
    input_file
):
    """
    Ambil duration video menggunakan ffprobe.
    """

    input_file = Path(
        input_file
    )

    if not input_file.exists():
        raise FileNotFoundError(
            f"Video tidak ditemukan: {input_file}"
        )

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(input_file),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Gagal membaca durasi video.\n"
            + result.stderr
        )

    try:
        return float(
            result.stdout.strip()
        )
    except ValueError as exc:
        raise RuntimeError(
            "Durasi video tidak valid."
        ) from exc


# ============================================================
# RENDER VERTICAL CLIP
# ============================================================

def render_vertical_clip(
    input_file,
    output_file,
    subtitle_file,
    clip_start,
    clip_end,
):
    """
    Render video:

        Original video
             ↓
        Crop / scale
             ↓
        1080x1920
             ↓
        Burn subtitle
             ↓
        MP4 H.264
    """

    input_file = Path(
        input_file
    )

    output_file = Path(
        output_file
    )

    subtitle_file = Path(
        subtitle_file
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input video tidak ditemukan: {input_file}"
        )

    if not subtitle_file.exists():
        raise FileNotFoundError(
            f"Subtitle ASS tidak ditemukan: {subtitle_file}"
        )

    try:
        clip_start = float(
            clip_start
        )

        clip_end = float(
            clip_end
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "clip_start dan clip_end harus berupa angka."
        ) from exc

    if clip_start < 0:
        clip_start = 0.0

    if clip_end <= clip_start:
        raise ValueError(
            f"Durasi clip tidak valid: "
            f"{clip_start} -> {clip_end}"
        )

    video_duration = get_video_duration(
        input_file
    )

    if clip_start >= video_duration:
        raise ValueError(
            f"clip_start {clip_start:.2f}s "
            f"melebihi durasi video "
            f"{video_duration:.2f}s"
        )

    clip_end = min(
        clip_end,
        video_duration,
    )

    clip_duration = (
        clip_end
        - clip_start
    )

    if clip_duration <= 0:
        raise ValueError(
            "Clip duration <= 0."
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
    # VIDEO FILTER
    # ========================================================

    video_filter = (
        "scale=608:1080:"
        "force_original_aspect_ratio=increase,"
        "crop=608:1080:"
        "(iw-608)/2:"
        "(ih-1080)/2,"
        "scale=1080:1920,"
        "setsar=1,"
        f"subtitles='{subtitle_path}'"
    )

    # ========================================================
    # FFMPEG COMMAND
    # ========================================================

    command = [
        "ffmpeg",

        "-y",

        # Seek input
        "-ss",
        f"{clip_start:.3f}",

        "-i",
        str(input_file),

        # Duration
        "-t",
        f"{clip_duration:.3f}",

        # Video
        "-map",
        "0:v:0",

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

        # Audio
        "-map",
        "0:a:0?",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        # Streaming-friendly
        "-movflags",
        "+faststart",

        "-avoid_negative_ts",
        "make_zero",

        str(output_file),
    ]

    print()
    print("=" * 70)
    print("🎬 RENDER VERTICAL CLIP")
    print("=" * 70)
    print(f"Input     : {input_file}")
    print(f"Output    : {output_file}")
    print(f"Subtitle  : {subtitle_file}")
    print(f"Start     : {clip_start:.2f}s")
    print(f"End       : {clip_end:.2f}s")
    print(f"Duration  : {clip_duration:.2f}s")
    print("Resolution: 1080x1920")
    print("Subtitle  : WORD LEVEL")
    print("=" * 70)

    # ========================================================
    # RUN FFMPEG
    # ========================================================

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # ========================================================
    # ERROR
    # ========================================================

    if result.returncode != 0:

        print()
        print("❌ FFMPEG ERROR")
        print(result.stderr)

        raise RuntimeError(
            "FFmpeg gagal melakukan render."
        )

    # ========================================================
    # VALIDATE OUTPUT
    # ========================================================

    if not output_file.exists():
        raise RuntimeError(
            "FFmpeg selesai tetapi file output "
            "tidak ditemukan."
        )

    output_size = (
        output_file.stat().st_size
    )

    if output_size <= 0:
        raise RuntimeError(
            "File output kosong."
        )

    print()
    print("✅ RENDER BERHASIL")
    print(f"Output : {output_file}")
    print(
        f"Size   : "
        f"{output_size / (1024 * 1024):.2f} MB"
    )
    print()

    return output_file