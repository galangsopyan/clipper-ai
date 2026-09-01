from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ViralCandidate:
    start: float
    end: float
    duration: float

    score: float
    category: str

    title: str
    transcript: str
    reason: str

    hook_score: float
    insight_score: float
    emotion_score: float
    story_score: float
    curiosity_score: float
    controversy_score: float
    punchline_score: float
    audio_score: float
    duration_score: float
    completeness_score: float


# ============================================================
# KEYWORDS
# ============================================================

HOOK_PATTERNS = [
    r"\bpernah gak\b",
    r"\bpernahkah\b",
    r"\btahu gak\b",
    r"\btau gak\b",
    r"\napa yang terjadi\b",
    r"\bkenapa\b",
    r"\bmengapa\b",
    r"\bgimana\b",
    r"\bbagaimana\b",
    r"\bkamu tahu\b",
    r"\blo tahu\b",
    r"\bsaya punya satu\b",
    r"\bsatu hal\b",
    r"\nyang paling\b",
    r"\bkesalahan terbesar\b",
    r"\bjangan pernah\b",
    r"\bternyata\b",
]

INSIGHT_WORDS = [
    "belajar",
    "pelajaran",
    "pengalaman",
    "menurut",
    "karena",
    "sebab",
    "artinya",
    "intinya",
    "pelajaran saya",
    "yang saya pelajari",
    "solusinya",
    "caranya",
    "harus",
    "jangan",
    "penting",
    "prinsip",
    "strategi",
    "berpikir",
    "keputusan",
]

EMOTION_WORDS = [
    "takut",
    "trauma",
    "sedih",
    "senang",
    "bahagia",
    "marah",
    "kecewa",
    "menangis",
    "menyesal",
    "cinta",
    "sayang",
    "kehilangan",
    "gagal",
    "berhasil",
    "bangkrut",
    "menderita",
    "sakit",
    "khawatir",
    "harapan",
]

STORY_WORDS = [
    "waktu itu",
    "ketika itu",
    "dulu",
    "awalnya",
    "kemudian",
    "lalu",
    "akhirnya",
    "setelah itu",
    "saat itu",
    "saya pernah",
    "pernah",
    "kejadian",
    "cerita",
    "pengalaman",
]

CONTROVERSY_WORDS = [
    "salah",
    "bohong",
    "tidak benar",
    "gak benar",
    "bukan",
    "justru",
    "berbeda",
    "aneh",
    "masalahnya",
    "kontroversi",
    "menurut saya",
    "saya tidak setuju",
    "tidak setuju",
    "keliru",
    "kesalahan",
    "bahaya",
    "jangan percaya",
]

PUNCHLINE_WORDS = [
    "intinya",
    "kesimpulannya",
    "jadi",
    "makanya",
    "itulah",
    "yang paling penting",
    "pada akhirnya",
    "ujungnya",
    "dari situ",
    "saya belajar",
    "pelajaran terbesar",
]


# ============================================================
# HELPERS
# ============================================================

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def count_matches(
    text: str,
    patterns: list[str],
) -> int:

    total = 0

    for pattern in patterns:

        try:
            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):
                total += 1

        except re.error:
            if pattern.lower() in text.lower():
                total += 1

    return total


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def score_keywords(
    text: str,
    words: list[str],
    base: float = 20.0,
    per_match: float = 15.0,
) -> float:

    text = normalize_text(text)

    matches = 0

    for word in words:

        if word.lower() in text:
            matches += 1

    return clamp(
        base + matches * per_match
    )


def score_hook(
    text: str,
) -> float:

    text = normalize_text(text)

    score = 20.0

    score += count_matches(
        text,
        HOOK_PATTERNS,
    ) * 22.0

    if "?" in text:
        score += 20

    if len(text) < 250:
        score += 5

    return clamp(score)


def score_insight(
    text: str,
) -> float:

    return score_keywords(
        text,
        INSIGHT_WORDS,
        base=15,
        per_match=13,
    )


def score_emotion(
    text: str,
) -> float:

    return score_keywords(
        text,
        EMOTION_WORDS,
        base=10,
        per_match=15,
    )


def score_story(
    text: str,
) -> float:

    return score_keywords(
        text,
        STORY_WORDS,
        base=10,
        per_match=15,
    )


def score_controversy(
    text: str,
) -> float:

    return score_keywords(
        text,
        CONTROVERSY_WORDS,
        base=10,
        per_match=14,
    )


def score_punchline(
    text: str,
) -> float:

    return score_keywords(
        text,
        PUNCHLINE_WORDS,
        base=10,
        per_match=16,
    )


def score_curiosity(
    text: str,
    hook_score: float,
    controversy_score: float,
) -> float:

    text = normalize_text(text)

    score = 20.0

    if "?" in text:
        score += 25

    if hook_score >= 60:
        score += 25

    if controversy_score >= 60:
        score += 15

    curiosity_phrases = [
        "ternyata",
        "tapi",
        "namun",
        "justru",
        "awalnya",
        "akhirnya",
        "tidak menyangka",
        "gak nyangka",
        "rahasianya",
    ]

    for phrase in curiosity_phrases:

        if phrase in text:
            score += 5

    return clamp(score)


def score_duration(
    duration: float,
) -> float:

    if 25 <= duration <= 45:
        return 100.0

    if 20 <= duration < 25:
        return 90.0

    if 45 < duration <= 60:
        return 90.0

    if 15 <= duration < 20:
        return 80.0

    if 60 < duration <= 75:
        return 70.0

    return 50.0


def score_completeness(
    text: str,
) -> float:

    text = text.strip()

    if not text:
        return 0.0

    score = 40.0

    sentence_count = len(
        re.findall(
            r"[.!?]",
            text,
        )
    )

    if sentence_count >= 2:
        score += 20

    if sentence_count >= 3:
        score += 15

    ending_patterns = [
        "jadi",
        "makanya",
        "intinya",
        "akhirnya",
        "itulah",
        "kesimpulannya",
        "pelajarannya",
        "dari situ",
    ]

    for phrase in ending_patterns:

        if phrase in text.lower():
            score += 10
            break

    return clamp(score)


def score_audio(
    audio: list[dict[str, Any]] | None,
    start: float,
    end: float,
) -> float:

    if not audio:
        return 50.0

    values = []

    for item in audio:

        item_start = float(
            item.get(
                "start",
                0,
            )
        )

        item_end = float(
            item.get(
                "end",
                0,
            )
        )

        if (
            item_end >= start
            and item_start <= end
        ):

            energy = item.get(
                "energy",
                item.get(
                    "score",
                    50,
                ),
            )

            try:
                values.append(
                    float(energy)
                )
            except (
                TypeError,
                ValueError,
            ):
                pass

    if not values:
        return 50.0

    return clamp(
        sum(values) / len(values)
    )


# ============================================================
# TITLE GENERATOR
# ============================================================

def generate_title(
    text: str,
) -> str:

    clean = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    if not clean:
        return "Podcast Clip"

    sentences = re.split(
        r"(?<=[.!?])\s+",
        clean,
    )

    first = sentences[0].strip()

    if len(first) >= 25:

        title = first

    else:

        title = clean[:140]

    title = title.strip(
        " .,!?:;-"
    )

    if len(title) > 100:

        title = (
            title[:100]
            .rsplit(" ", 1)[0]
            + "..."
        )

    return title


# ============================================================
# CATEGORY
# ============================================================

def detect_category(
    scores: dict[str, float],
) -> str:

    category_scores = {
        "🔥 VIRAL": (
            scores["hook"] * 0.35
            + scores["curiosity"] * 0.35
            + scores["controversy"] * 0.30
        ),
        "🧠 INSIGHT": (
            scores["insight"] * 0.60
            + scores["completeness"] * 0.40
        ),
        "❤️ EMOTIONAL": (
            scores["emotion"] * 0.70
            + scores["story"] * 0.30
        ),
        "📖 STORY": (
            scores["story"] * 0.65
            + scores["emotion"] * 0.35
        ),
    }

    return max(
        category_scores,
        key=category_scores.get,
    )


# ============================================================
# REASON
# ============================================================

def generate_reason(
    scores: dict[str, float],
) -> str:

    reasons = []

    if scores["hook"] >= 65:
        reasons.append(
            "hook kuat"
        )

    if scores["insight"] >= 65:
        reasons.append(
            "memiliki insight"
        )

    if scores["emotion"] >= 60:
        reasons.append(
            "memiliki unsur emosional"
        )

    if scores["story"] >= 60:
        reasons.append(
            "memiliki struktur cerita"
        )

    if scores["curiosity"] >= 65:
        reasons.append(
            "memicu curiosity"
        )

    if scores["controversy"] >= 60:
        reasons.append(
            "berpotensi memicu diskusi"
        )

    if scores["punchline"] >= 60:
        reasons.append(
            "memiliki punchline"
        )

    if scores["completeness"] >= 70:
        reasons.append(
            "cukup lengkap sebagai standalone clip"
        )

    if not reasons:
        reasons.append(
            "memiliki potensi short-form"
        )

    return ", ".join(reasons)


# ============================================================
# TEXT WINDOWS
# ============================================================

def build_windows(
    segments: list[dict[str, Any]],
    min_duration: float,
    max_duration: float,
) -> list[dict[str, Any]]:

    windows = []

    total = len(segments)

    for i in range(total):

        start_segment = segments[i]

        start = float(
            start_segment["start"]
        )

        text_parts = []

        end = start

        for j in range(
            i,
            min(
                total,
                i + 30,
            ),
        ):

            segment = segments[j]

            segment_start = float(
                segment["start"]
            )

            segment_end = float(
                segment["end"]
            )

            duration = (
                segment_end - start
            )

            if duration > max_duration:
                break

            text_parts.append(
                segment.get(
                    "text",
                    "",
                ).strip()
            )

            end = segment_end

            if duration >= min_duration:

                text = " ".join(
                    text_parts
                ).strip()

                if len(text) >= 25:

                    windows.append(
                        {
                            "start": start,
                            "end": end,
                            "duration": duration,
                            "text": text,
                        }
                    )

    return windows


# ============================================================
# DEDUPLICATION
# ============================================================

def overlap_ratio(
    a_start: float,
    a_end: float,
    b_start: float,
    b_end: float,
) -> float:

    intersection = max(
        0.0,
        min(a_end, b_end)
        - max(a_start, b_start),
    )

    shortest = min(
        a_end - a_start,
        b_end - b_start,
    )

    if shortest <= 0:
        return 0.0

    return (
        intersection / shortest
    )


def deduplicate(
    candidates: list[ViralCandidate],
    limit: int,
) -> list[ViralCandidate]:

    selected = []

    candidates = sorted(
        candidates,
        key=lambda item: item.score,
        reverse=True,
    )

    for candidate in candidates:

        too_similar = False

        for existing in selected:

            overlap = overlap_ratio(
                candidate.start,
                candidate.end,
                existing.start,
                existing.end,
            )

            if overlap >= 0.55:

                too_similar = True
                break

        if not too_similar:

            selected.append(
                candidate
            )

        if len(selected) >= limit:
            break

    return selected


# ============================================================
# MAIN ENGINE
# ============================================================

def analyze_podcast_v4(
    transcript: dict[str, Any],
    audio: list[dict[str, Any]] | None = None,
    min_duration: float = 15.0,
    max_duration: float = 60.0,
    max_results: int = 20,
) -> list[ViralCandidate]:

    segments = transcript.get(
        "segments",
        [],
    )

    if not segments:
        return []

    windows = build_windows(
        segments,
        min_duration,
        max_duration,
    )

    candidates = []

    for window in windows:

        text = window["text"]

        hook = score_hook(
            text
        )

        insight = score_insight(
            text
        )

        emotion = score_emotion(
            text
        )

        story = score_story(
            text
        )

        controversy = score_controversy(
            text
        )

        punchline = score_punchline(
            text
        )

        curiosity = score_curiosity(
            text,
            hook,
            controversy,
        )

        duration = score_duration(
            window["duration"]
        )

        completeness = score_completeness(
            text
        )

        audio_score = score_audio(
            audio,
            window["start"],
            window["end"],
        )

        # ----------------------------------------------------
        # WEIGHT
        # ----------------------------------------------------

        final_score = (
            hook * 0.16
            + insight * 0.13
            + emotion * 0.11
            + story * 0.10
            + curiosity * 0.13
            + controversy * 0.10
            + punchline * 0.08
            + audio_score * 0.05
            + duration * 0.06
            + completeness * 0.08
        )

        final_score = round(
            clamp(final_score),
            2,
        )

        score_map = {
            "hook": hook,
            "insight": insight,
            "emotion": emotion,
            "story": story,
            "curiosity": curiosity,
            "controversy": controversy,
            "punchline": punchline,
            "audio": audio_score,
            "duration": duration,
            "completeness": completeness,
        }

        category = detect_category(
            score_map
        )

        reason = generate_reason(
            score_map
        )

        title = generate_title(
            text
        )

        candidates.append(
            ViralCandidate(
                start=window["start"],
                end=window["end"],
                duration=window["duration"],
                score=final_score,
                category=category,
                title=title,
                transcript=text,
                reason=reason,
                hook_score=round(hook, 2),
                insight_score=round(insight, 2),
                emotion_score=round(emotion, 2),
                story_score=round(story, 2),
                curiosity_score=round(curiosity, 2),
                controversy_score=round(
                    controversy,
                    2,
                ),
                punchline_score=round(
                    punchline,
                    2,
                ),
                audio_score=round(
                    audio_score,
                    2,
                ),
                duration_score=round(
                    duration,
                    2,
                ),
                completeness_score=round(
                    completeness,
                    2,
                ),
            )
        )

    return deduplicate(
        candidates,
        max_results,
    )