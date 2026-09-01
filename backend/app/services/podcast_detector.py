from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import re


@dataclass
class PodcastMoment:
    start: float
    end: float
    duration: float

    score: int

    hook_score: float
    insight_score: float
    emotion_score: float
    story_score: float
    curiosity_score: float
    audio_score: float
    duration_score: float

    category: str
    title: str
    transcript: str
    reason: str


HOOK_PATTERNS = [
    "ternyata",
    "akhirnya",
    "sebenarnya",
    "jujur",
    "saya pernah",
    "aku pernah",
    "waktu itu",
    "dulu saya",
    "dulu aku",
    "tidak banyak orang tahu",
    "yang orang tidak tahu",
    "kesalahan terbesar",
    "hal terbesar",
    "masalah terbesar",
    "rahasia",
    "jangan pernah",
    "jangan sampai",
    "kalau saya tahu",
    "seandainya",
    "saya hampir",
    "aku hampir",
]


INSIGHT_PATTERNS = [
    "pelajaran",
    "belajar",
    "caranya",
    "cara",
    "kuncinya",
    "intinya",
    "menurut saya",
    "menurutku",
    "prinsip",
    "strategi",
    "tips",
    "solusi",
    "penting",
    "berarti",
    "karena",
    "alasan",
    "pengalaman",
    "kesimpulannya",
]


EMOTION_PATTERNS = [
    "takut",
    "sedih",
    "bahagia",
    "senang",
    "marah",
    "kecewa",
    "menangis",
    "menyesal",
    "cinta",
    "sayang",
    "rindu",
    "khawatir",
    "gagal",
    "berhasil",
    "berjuang",
    "sakit",
    "trauma",
    "mimpi",
    "bangga",
    "terharu",
]


STORY_PATTERNS = [
    "waktu itu",
    "ketika itu",
    "saat itu",
    "kemudian",
    "lalu",
    "setelah itu",
    "sebelumnya",
    "akhirnya",
    "awalnya",
    "dulu",
    "pernah",
    "suatu hari",
]


CURIOSITY_PATTERNS = [
    "kenapa",
    "mengapa",
    "bagaimana",
    "ternyata",
    "yang terjadi",
    "tidak menyangka",
    "tidak pernah menyangka",
    "tahu tidak",
    "percaya atau tidak",
    "masalahnya",
    "tapi",
    "namun",
]


def clamp(
    value: float,
    minimum: float = 0,
    maximum: float = 100,
) -> float:
    return max(
        minimum,
        min(maximum, value),
    )


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(
        r"\s+",
        " ",
        text,
    )
    return text.strip()


def count_patterns(
    text: str,
    patterns: list[str],
) -> int:

    normalized = normalize_text(text)

    return sum(
        1
        for pattern in patterns
        if pattern in normalized
    )


def score_hook(text: str) -> float:

    if not text:
        return 10

    score = 20

    hits = count_patterns(
        text,
        HOOK_PATTERNS,
    )

    score += min(
        hits * 15,
        60,
    )

    # Kalimat pendek sering cocok sebagai opening.
    words = text.split()

    if 5 <= len(words) <= 15:
        score += 10

    # Pertanyaan
    if "?" in text:
        score += 10

    return clamp(score)


def score_insight(text: str) -> float:

    if not text:
        return 10

    score = 20

    hits = count_patterns(
        text,
        INSIGHT_PATTERNS,
    )

    score += min(
        hits * 12,
        55,
    )

    words = text.split()

    if len(words) >= 15:
        score += 10

    if len(words) >= 30:
        score += 10

    return clamp(score)


def score_emotion(text: str) -> float:

    if not text:
        return 10

    score = 15

    hits = count_patterns(
        text,
        EMOTION_PATTERNS,
    )

    score += min(
        hits * 15,
        60,
    )

    if "!" in text:
        score += 10

    return clamp(score)


def score_story(text: str) -> float:

    if not text:
        return 10

    score = 20

    hits = count_patterns(
        text,
        STORY_PATTERNS,
    )

    score += min(
        hits * 12,
        55,
    )

    words = text.split()

    if len(words) >= 20:
        score += 10

    if len(words) >= 40:
        score += 10

    return clamp(score)


def score_curiosity(text: str) -> float:

    if not text:
        return 10

    score = 20

    hits = count_patterns(
        text,
        CURIOSITY_PATTERNS,
    )

    score += min(
        hits * 12,
        60,
    )

    if "?" in text:
        score += 15

    return clamp(score)


def score_duration(
    duration: float,
) -> float:

    if 25 <= duration <= 40:
        return 100

    if 20 <= duration < 25:
        return 90

    if 40 < duration <= 50:
        return 88

    if 15 <= duration < 20:
        return 75

    return 50


def get_transcript(
    segments: list[dict[str, Any]],
    start: float,
    end: float,
) -> str:

    texts = []

    for segment in segments:

        segment_start = float(
            segment.get(
                "start",
                0,
            )
        )

        segment_end = float(
            segment.get(
                "end",
                0,
            )
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


def calculate_audio_score(
    audio_windows: list[dict[str, Any]],
    start: float,
    end: float,
) -> float:

    values = []

    for window in audio_windows:

        ws = float(
            window.get(
                "start",
                0,
            )
        )

        we = float(
            window.get(
                "end",
                0,
            )
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

    average = sum(values) / len(values)
    peak = max(values)

    return clamp(
        average * 0.60
        + peak * 0.40
    )


def determine_category(
    hook: float,
    insight: float,
    emotion: float,
    story: float,
    curiosity: float,
) -> str:

    scores = {
        "🔥 VIRAL": (
            hook
            + curiosity
        ) / 2,

        "🧠 INSIGHT": (
            insight
            + hook
        ) / 2,

        "❤️ EMOTIONAL": (
            emotion
            + story
        ) / 2,

        "📖 STORY": (
            story
            + curiosity
        ) / 2,
    }

    return max(
        scores,
        key=scores.get,
    )


def generate_title(
    text: str,
) -> str:

    text = " ".join(
        text.split()
    )

    if not text:
        return "Viral Podcast Moment"

    # Ambil maksimal sekitar 90 karakter.
    if len(text) <= 90:
        return text

    return (
        text[:87].rstrip()
        + "..."
    )


def generate_reason(
    hook: float,
    insight: float,
    emotion: float,
    story: float,
    curiosity: float,
) -> str:

    reasons = []

    if hook >= 65:
        reasons.append(
            "hook kuat"
        )

    if insight >= 65:
        reasons.append(
            "memiliki insight"
        )

    if emotion >= 65:
        reasons.append(
            "memiliki unsur emosional"
        )

    if story >= 65:
        reasons.append(
            "memiliki struktur cerita"
        )

    if curiosity >= 65:
        reasons.append(
            "memicu curiosity"
        )

    if not reasons:
        reasons.append(
            "memiliki potensi short-form"
        )

    return ", ".join(reasons)


def analyze_segment(
    text: str,
    duration: float,
    audio_score: float,
) -> dict[str, float]:

    hook = score_hook(text)
    insight = score_insight(text)
    emotion = score_emotion(text)
    story = score_story(text)
    curiosity = score_curiosity(text)
    duration_points = score_duration(
        duration
    )

    # Audio hanya 10%.
    #
    # Podcast lebih mengutamakan
    # isi percakapan daripada volume.
    score = (
        hook * 0.25
        + insight * 0.20
        + emotion * 0.15
        + story * 0.15
        + curiosity * 0.15
        + audio_score * 0.05
        + duration_points * 0.05
    )

    return {
        "score": round(
            clamp(score),
            2,
        ),
        "hook": round(
            hook,
            2,
        ),
        "insight": round(
            insight,
            2,
        ),
        "emotion": round(
            emotion,
            2,
        ),
        "story": round(
            story,
            2,
        ),
        "curiosity": round(
            curiosity,
            2,
        ),
        "audio": round(
            audio_score,
            2,
        ),
        "duration": round(
            duration_points,
            2,
        ),
    }


def detect_podcast_moments(
    transcript: dict[str, Any],
    audio: dict[str, Any],
    min_duration: float = 15,
    max_duration: float = 40,
    max_results: int = 5,
) -> list[PodcastMoment]:

    segments = transcript.get(
        "segments",
        [],
    )

    audio_windows = audio.get(
        "windows",
        [],
    )

    if not segments:
        return []

    moments = []

    # --------------------------------------------------
    # Buat kandidat berdasarkan kelompok transcript.
    # --------------------------------------------------

    for i in range(
        len(segments)
    ):

        start = float(
            segments[i].get(
                "start",
                0,
            )
        )

        collected = []

        end = start

        for j in range(
            i,
            len(segments),
        ):

            segment = segments[j]

            segment_end = float(
                segment.get(
                    "end",
                    0,
                )
            )

            text = str(
                segment.get(
                    "text",
                    "",
                )
            ).strip()

            if text:
                collected.append(
                    text
                )

            end = segment_end

            duration = end - start

            if duration >= min_duration:

                if duration <= max_duration:
                    break

                # Jika sudah terlalu panjang,
                # hentikan.
                break

        duration = end - start

        if (
            duration < min_duration
            or duration > max_duration
        ):
            continue

        text = " ".join(
            collected
        )

        audio_score = calculate_audio_score(
            audio_windows,
            start,
            end,
        )

        scores = analyze_segment(
            text,
            duration,
            audio_score,
        )

        category = determine_category(
            scores["hook"],
            scores["insight"],
            scores["emotion"],
            scores["story"],
            scores["curiosity"],
        )

        reason = generate_reason(
            scores["hook"],
            scores["insight"],
            scores["emotion"],
            scores["story"],
            scores["curiosity"],
        )

        moments.append(
            PodcastMoment(
                start=round(start, 2),
                end=round(end, 2),
                duration=round(
                    duration,
                    2,
                ),
                score=int(
                    round(
                        scores["score"]
                    )
                ),
                hook_score=scores["hook"],
                insight_score=scores["insight"],
                emotion_score=scores["emotion"],
                story_score=scores["story"],
                curiosity_score=scores["curiosity"],
                audio_score=scores["audio"],
                duration_score=scores["duration"],
                category=category,
                title=generate_title(
                    text
                ),
                transcript=text,
                reason=reason,
            )
        )

    # --------------------------------------------------
    # Urutkan
    # --------------------------------------------------

    moments.sort(
        key=lambda item: item.score,
        reverse=True,
    )

    # --------------------------------------------------
    # Hindari kandidat terlalu overlap.
    # --------------------------------------------------

    selected = []

    for moment in moments:

        overlap_found = False

        for existing in selected:

            overlap_start = max(
                moment.start,
                existing.start,
            )

            overlap_end = min(
                moment.end,
                existing.end,
            )

            overlap = max(
                0,
                overlap_end
                - overlap_start,
            )

            shortest = min(
                moment.duration,
                existing.duration,
            )

            if (
                shortest > 0
                and overlap / shortest > 0.45
            ):

                overlap_found = True
                break

        if overlap_found:
            continue

        selected.append(
            moment
        )

        if len(selected) >= max_results:
            break

    return selected