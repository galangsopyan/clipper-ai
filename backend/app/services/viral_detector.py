from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ViralMoment:
    start: float
    end: float
    score: int
    title: str
    reason: str


HOOK_WORDS = {
    "ternyata",
    "tiba-tiba",
    "akhirnya",
    "kenapa",
    "bagaimana",
    "jangan",
    "rahasia",
    "penting",
    "serius",
    "gila",
    "wow",
    "percaya",
    "ingat",
    "salah",
    "benar",
}


EMOTION_WORDS = {
    "cinta",
    "sayang",
    "rindu",
    "sedih",
    "bahagia",
    "marah",
    "takut",
    "menangis",
    "kecewa",
    "senang",
    "hati",
    "perasaan",
}


def normalize_text(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.lower().strip(),
    )


def text_score(text: str) -> int:
    """
    Menilai kekuatan transcript.
    Skor dasar sengaja tidak terlalu tinggi agar
    video tanpa speech tidak otomatis dianggap viral.
    """

    normalized = normalize_text(text)

    if not normalized:
        return 0

    words = normalized.split()

    score = 0

    hook_hits = sum(
        1
        for word in HOOK_WORDS
        if word in normalized
    )

    emotion_hits = sum(
        1
        for word in EMOTION_WORDS
        if word in normalized
    )

    score += min(hook_hits * 12, 35)
    score += min(emotion_hits * 10, 30)

    if len(words) >= 8:
        score += 10

    if len(words) >= 15:
        score += 10

    return min(score, 100)


def duration_score(
    duration: float,
    minimum: float = 15.0,
    maximum: float = 60.0,
) -> int:
    """
    Clip short-form idealnya tidak terlalu pendek
    dan tidak terlalu panjang.
    """

    if duration < 8:
        return 20

    if duration < minimum:
        return 55

    if duration <= maximum:
        return 100

    if duration <= 75:
        return 75

    return 45


def generate_title(text: str, index: int) -> str:
    text = text.strip()

    if not text:
        return f"Viral Moment #{index}"

    if len(text) <= 60:
        return text

    return text[:57].rstrip() + "..."


def build_candidate(
    segments: list[dict[str, Any]],
    start_index: int,
    min_duration: float,
    max_duration: float,
) -> ViralMoment | None:

    if start_index >= len(segments):
        return None

    start = float(
        segments[start_index]["start"]
    )

    end = start
    texts: list[str] = []

    for segment in segments[start_index:]:
        candidate_end = float(
            segment["end"]
        )

        if candidate_end - start > max_duration:
            break

        end = candidate_end

        text = str(
            segment.get("text", "")
        ).strip()

        if text:
            texts.append(text)

        if end - start >= min_duration:
            break

    duration = end - start

    if duration < min_duration:
        return None

    combined_text = " ".join(texts).strip()

    transcript_score = text_score(
        combined_text
    )

    duration_points = duration_score(
        duration
    )

    # Untuk video tanpa speech,
    # duration tetap memberi nilai dasar.
    base_score = 30

    final_score = round(
        (
            base_score * 0.25
            + transcript_score * 0.45
            + duration_points * 0.30
        )
    )

    final_score = max(
        0,
        min(100, final_score),
    )

    reason_parts = []

    if transcript_score >= 50:
        reason_parts.append(
            "memiliki hook/emosi kuat"
        )

    if duration_points >= 90:
        reason_parts.append(
            "durasi cocok untuk short-form"
        )

    if not combined_text:
        reason_parts.append(
            "cocok dianalisis berdasarkan audio/visual"
        )

    if not reason_parts:
        reason_parts.append(
            "memiliki struktur yang cukup untuk kandidat short"
        )

    return ViralMoment(
        start=start,
        end=end,
        score=final_score,
        title=generate_title(
            combined_text,
            start_index + 1,
        ),
        reason=", ".join(reason_parts),
    )


def overlaps(
    first: ViralMoment,
    second: ViralMoment,
    minimum_gap: float = 5.0,
) -> bool:

    return not (
        second.start
        >= first.end + minimum_gap
        or first.start
        >= second.end + minimum_gap
    )


def detect_viral_moments(
    transcript: dict[str, Any],
    min_duration: float = 15.0,
    max_duration: float = 60.0,
    max_results: int = 5,
) -> list[ViralMoment]:

    segments = transcript.get(
        "segments",
        [],
    )

    if not segments:
        return []

    candidates: list[ViralMoment] = []

    for index in range(len(segments)):
        candidate = build_candidate(
            segments,
            index,
            min_duration,
            max_duration,
        )

        if candidate:
            candidates.append(candidate)

    candidates.sort(
        key=lambda item: item.score,
        reverse=True,
    )

    selected: list[ViralMoment] = []

    for candidate in candidates:

        if any(
            overlaps(
                candidate,
                selected_item,
            )
            for selected_item in selected
        ):
            continue

        selected.append(candidate)

        if len(selected) >= max_results:
            break

    selected.sort(
        key=lambda item: item.start
    )

    return selected