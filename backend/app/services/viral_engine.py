from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ViralCandidate:
    start: float
    end: float
    duration: float

    score: int

    audio_score: float
    visual_score: float
    transcript_score: float
    duration_score: float

    title: str
    transcript: str
    reason: str


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:

    return max(
        minimum,
        min(maximum, value),
    )


def calculate_duration_score(
    duration: float,
) -> float:

    if 25 <= duration <= 40:
        return 100

    if 20 <= duration < 25:
        return 92

    if 40 < duration <= 45:
        return 90

    if 15 <= duration < 20:
        return 78

    return 55


def calculate_transcript_score(
    text: str,
) -> float:

    if not text:
        return 20

    words = text.split()

    score = 35

    if len(words) >= 5:
        score += 10

    if len(words) >= 10:
        score += 10

    if len(words) >= 20:
        score += 10

    hook_words = [
        "ternyata",
        "akhirnya",
        "tiba-tiba",
        "jangan",
        "kenapa",
        "serius",
        "gila",
        "wow",
        "rahasia",
        "salah",
        "benar",
        "percaya",
        "ingat",
        "cinta",
        "sayang",
        "rindu",
        "bahagia",
        "sedih",
        "menangis",
        "terbaik",
        "pertama",
        "terakhir",
    ]

    lower = text.lower()

    hits = sum(
        1
        for word in hook_words
        if word in lower
    )

    score += min(
        hits * 5,
        25,
    )

    if "?" in text:
        score += 5

    if "!" in text:
        score += 5

    return clamp(score)


def collect_transcript(
    segments: list[dict[str, Any]],
    start: float,
    end: float,
) -> str:

    texts = []

    for segment in segments:

        segment_start = float(
            segment.get("start", 0)
        )

        segment_end = float(
            segment.get("end", 0)
        )

        if (
            segment_end > start
            and segment_start < end
        ):

            text = str(
                segment.get(
                    "text",
                    "",
                )
            ).strip()

            if text:
                texts.append(text)

    return " ".join(texts)


def average_audio_score(
    windows: list[dict[str, Any]],
    start: float,
    end: float,
) -> float:

    values = []

    for window in windows:

        ws = float(
            window.get("start", 0)
        )

        we = float(
            window.get("end", 0)
        )

        if (
            we > start
            and ws < end
        ):

            values.append(
                float(
                    window.get(
                        "energy_score",
                        0,
                    )
                )
            )

    if not values:
        return 0

    return sum(values) / len(values)


def peak_audio_score(
    windows: list[dict[str, Any]],
    start: float,
    end: float,
) -> float:

    values = []

    for window in windows:

        ws = float(
            window.get("start", 0)
        )

        we = float(
            window.get("end", 0)
        )

        if (
            we > start
            and ws < end
        ):

            values.append(
                float(
                    window.get(
                        "energy_score",
                        0,
                    )
                )
            )

    if not values:
        return 0

    return max(values)


def calculate_audio_score(
    windows: list[dict[str, Any]],
    start: float,
    end: float,
) -> float:

    average = average_audio_score(
        windows,
        start,
        end,
    )

    peak = peak_audio_score(
        windows,
        start,
        end,
    )

    return clamp(
        average * 0.65
        + peak * 0.35
    )


def calculate_visual_score(
    changes: list[dict[str, Any]],
    start: float,
    end: float,
) -> float:

    values = []

    for change in changes:

        timestamp = float(
            change.get("time", 0)
        )

        if (
            start <= timestamp <= end
        ):

            values.append(
                float(
                    change.get(
                        "visual_score",
                        0,
                    )
                )
            )

    if not values:
        return 0

    average = sum(values) / len(values)
    peak = max(values)

    return clamp(
        average * 0.60
        + peak * 0.40
    )


def generate_title(
    text: str,
    index: int,
) -> str:

    text = " ".join(
        text.split()
    )

    if not text:
        return (
            f"Viral Moment #{index}"
        )

    if len(text) <= 80:
        return text

    return (
        text[:77].rstrip()
        + "..."
    )


def generate_reason(
    audio: float,
    visual: float,
    transcript: float,
    duration: float,
) -> str:

    reasons = []

    if audio >= 80:
        reasons.append(
            "peak audio sangat kuat"
        )

    elif audio >= 60:
        reasons.append(
            "energi audio kuat"
        )

    if visual >= 80:
        reasons.append(
            "perubahan visual sangat kuat"
        )

    elif visual >= 60:
        reasons.append(
            "perubahan visual terdeteksi"
        )

    if transcript >= 65:
        reasons.append(
            "transcript memiliki sinyal hook"
        )

    if duration >= 90:
        reasons.append(
            "durasi optimal short-form"
        )

    if not reasons:
        reasons.append(
            "terdapat kombinasi sinyal viral"
        )

    return ", ".join(reasons)


def build_candidate(
    transcript: dict[str, Any],
    audio: dict[str, Any],
    visual: dict[str, Any],
    start: float,
    end: float,
    index: int,
) -> ViralCandidate:

    segments = transcript.get(
        "segments",
        [],
    )

    audio_windows = audio.get(
        "windows",
        [],
    )

    visual_changes = visual.get(
        "changes",
        [],
    )

    duration = end - start

    audio_score = calculate_audio_score(
        audio_windows,
        start,
        end,
    )

    visual_score = calculate_visual_score(
        visual_changes,
        start,
        end,
    )

    text = collect_transcript(
        segments,
        start,
        end,
    )

    transcript_points = calculate_transcript_score(
        text
    )

    duration_points = calculate_duration_score(
        duration
    )

    # Bobot V4
    #
    # Audio       40%
    # Visual      30%
    # Transcript  20%
    # Duration    10%

    score = (
        audio_score * 0.40
        + visual_score * 0.30
        + transcript_points * 0.20
        + duration_points * 0.10
    )

    return ViralCandidate(
        start=round(start, 2),
        end=round(end, 2),
        duration=round(duration, 2),
        score=int(
            round(
                clamp(score)
            )
        ),
        audio_score=round(
            audio_score,
            2,
        ),
        visual_score=round(
            visual_score,
            2,
        ),
        transcript_score=round(
            transcript_points,
            2,
        ),
        duration_score=round(
            duration_points,
            2,
        ),
        title=generate_title(
            text,
            index,
        ),
        transcript=text,
        reason=generate_reason(
            audio_score,
            visual_score,
            transcript_points,
            duration_points,
        ),
    )


def detect_viral_candidates(
    transcript: dict[str, Any],
    audio: dict[str, Any],
    visual: dict[str, Any],
    video_duration: float | None = None,
    min_duration: float = 15,
    max_duration: float = 40,
    max_results: int = 5,
) -> list[ViralCandidate]:

    audio_windows = audio.get(
        "windows",
        [],
    )

    visual_changes = visual.get(
        "changes",
        [],
    )

    if video_duration is None:

        video_duration = float(
            audio.get(
                "duration",
                0,
            )
        )

    if not audio_windows:
        return []

    # ------------------------------------------------
    # Cari peak audio
    # ------------------------------------------------

    audio_peaks = sorted(
        audio_windows,
        key=lambda item: float(
            item.get(
                "energy_score",
                0,
            )
        ),
        reverse=True,
    )

    # ------------------------------------------------
    # Cari peak visual
    # ------------------------------------------------

    visual_peaks = sorted(
        visual_changes,
        key=lambda item: float(
            item.get(
                "visual_score",
                0,
            )
        ),
        reverse=True,
    )

    anchors = []

    # Ambil 8 peak audio
    for item in audio_peaks[:8]:

        anchors.append(
            float(
                item["start"]
            )
        )

    # Ambil 8 peak visual
    for item in visual_peaks[:8]:

        anchors.append(
            float(
                item["time"]
            )
        )

    anchors.sort()

    # ------------------------------------------------
    # Buat kandidat di sekitar anchor
    # ------------------------------------------------

    raw_candidates = []

    durations = [
        20,
        30,
        40,
    ]

    for anchor in anchors:

        for clip_duration in durations:

            if clip_duration < min_duration:
                continue

            if clip_duration > max_duration:
                continue

            # Anchor berada kira-kira 40%
            # dari awal clip.
            start = (
                anchor
                - clip_duration * 0.40
            )

            start = max(
                0,
                start,
            )

            end = (
                start
                + clip_duration
            )

            if end > video_duration:

                end = video_duration

                start = max(
                    0,
                    end - clip_duration,
                )

            duration = end - start

            if duration < min_duration:
                continue

            raw_candidates.append(
                (
                    start,
                    end,
                )
            )

    # ------------------------------------------------
    # Hilangkan duplikat
    # ------------------------------------------------

    unique = []

    for start, end in raw_candidates:

        duplicate = False

        for old_start, old_end in unique:

            if (
                abs(
                    start - old_start
                ) < 5
                and abs(
                    end - old_end
                ) < 5
            ):

                duplicate = True
                break

        if not duplicate:

            unique.append(
                (
                    start,
                    end,
                )
            )

    # ------------------------------------------------
    # Scoring
    # ------------------------------------------------

    candidates = []

    for index, (
        start,
        end,
    ) in enumerate(
        unique,
        start=1,
    ):

        candidate = build_candidate(
            transcript,
            audio,
            visual,
            start,
            end,
            index,
        )

        candidates.append(
            candidate
        )

    # ------------------------------------------------
    # Sort
    # ------------------------------------------------

    candidates.sort(
        key=lambda item: item.score,
        reverse=True,
    )

    # ------------------------------------------------
    # Non-overlap selection
    # ------------------------------------------------

    selected = []

    for candidate in candidates:

        overlaps = False

        for existing in selected:

            overlap_start = max(
                candidate.start,
                existing.start,
            )

            overlap_end = min(
                candidate.end,
                existing.end,
            )

            overlap = max(
                0,
                overlap_end
                - overlap_start,
            )

            shortest = min(
                candidate.duration,
                existing.duration,
            )

            if (
                shortest > 0
                and overlap
                / shortest
                > 0.45
            ):

                overlaps = True
                break

        if overlaps:
            continue

        selected.append(
            candidate
        )

        if len(selected) >= max_results:
            break

    return selected