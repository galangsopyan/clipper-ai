from pathlib import Path
from typing import Any
import json
import time

from faster_whisper import WhisperModel


# ============================================================
# CONFIG
# ============================================================

# Untuk akurasi lebih baik daripada "base"
MODEL_SIZE = "small"

DEVICE = "cpu"
COMPUTE_TYPE = "int8"

LANGUAGE = "id"

# Akurasi lebih diprioritaskan
BEAM_SIZE = 5
BEST_OF = 5


# ============================================================
# MODEL CACHE
# ============================================================

_model: WhisperModel | None = None


# ============================================================
# LOAD MODEL
# ============================================================

def get_model() -> WhisperModel:

    global _model

    if _model is None:

        print("=" * 60)
        print("LOADING WHISPER MODEL")
        print("=" * 60)

        print(f"Model       : {MODEL_SIZE}")
        print(f"Device      : {DEVICE}")
        print(f"Compute     : {COMPUTE_TYPE}")
        print(f"Beam size   : {BEAM_SIZE}")
        print(f"Best of     : {BEST_OF}")
        print(f"Language    : {LANGUAGE}")

        start_time = time.perf_counter()

        _model = WhisperModel(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            cpu_threads=8,
            num_workers=1,
        )

        load_time = time.perf_counter() - start_time

        print(
            f"Whisper model loaded "
            f"in {load_time:.2f} seconds."
        )

        print("=" * 60)

    return _model


# ============================================================
# TRANSCRIBE
# ============================================================

def transcribe_audio(
    audio_path: Path,
    cache_path: Path | None = None,
    force: bool = False,
) -> dict[str, Any]:

    # ========================================================
    # VALIDATE
    # ========================================================

    if not audio_path.exists():

        raise FileNotFoundError(
            f"Audio/video tidak ditemukan: {audio_path}"
        )

    file_size = audio_path.stat().st_size

    if file_size <= 0:

        raise RuntimeError(
            "File audio/video kosong."
        )

    print("=" * 60)
    print("WHISPER WORD-LEVEL TRANSCRIPTION")
    print("=" * 60)

    print(f"Input       : {audio_path}")
    print(f"File size   : {file_size:,} bytes")
    print(f"Model       : {MODEL_SIZE}")
    print(f"Device      : {DEVICE}")
    print(f"Compute     : {COMPUTE_TYPE}")
    print(f"Word timing : ENABLED")

    # ========================================================
    # CACHE
    # ========================================================

    if (
        cache_path is not None
        and cache_path.exists()
        and not force
    ):

        print(
            f"Loading transcript cache: {cache_path}"
        )

        with cache_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    # ========================================================
    # MODEL
    # ========================================================

    model = get_model()

    # ========================================================
    # TIMER
    # ========================================================

    start_time = time.perf_counter()

    print()
    print("Starting Faster-Whisper...")
    print("Word-level timestamps sedang dibuat...")
    print()

    # ========================================================
    # TRANSCRIBE
    # ========================================================

    segments, info = model.transcribe(

        str(audio_path),

        # Bahasa Indonesia
        language=LANGUAGE,

        # ====================================================
        # AKURASI
        # ====================================================

        beam_size=BEAM_SIZE,

        best_of=BEST_OF,

        temperature=0,

        # Pertahankan konteks antar segment
        condition_on_previous_text=True,

        # ====================================================
        # VAD
        # ====================================================

        vad_filter=True,

        vad_parameters={
            "min_silence_duration_ms": 500,
        },

        # ====================================================
        # WORD TIMESTAMPS
        # ====================================================

        word_timestamps=True,

        # ====================================================
        # SPEECH SETTINGS
        # ====================================================

        without_timestamps=False,
    )

    # ========================================================
    # BUILD RESULT
    # ========================================================

    result_segments = []

    full_text = []

    total_words = 0

    # ========================================================
    # PROCESS SEGMENTS
    # ========================================================

    for segment in segments:

        text = segment.text.strip()

        if not text:
            continue

        # ----------------------------------------------------
        # WORDS
        # ----------------------------------------------------

        words = []

        if segment.words:

            for word in segment.words:

                word_text = word.word.strip()

                if not word_text:
                    continue

                word_data = {
                    "start": float(word.start),
                    "end": float(word.end),
                    "word": word_text,
                }

                # Probability jika tersedia
                if word.probability is not None:

                    word_data["probability"] = float(
                        word.probability
                    )

                words.append(word_data)

        total_words += len(words)

        # ----------------------------------------------------
        # SEGMENT
        # ----------------------------------------------------

        result_segments.append(
            {
                "start": float(segment.start),
                "end": float(segment.end),
                "text": text,
                "words": words,
            }
        )

        full_text.append(text)

    # ========================================================
    # RESULT
    # ========================================================

    result = {

        "text": " ".join(full_text),

        "language": info.language,

        "language_probability": float(
            info.language_probability
        ),

        "duration": float(info.duration)
        if info.duration
        else 0.0,

        "segments": result_segments,

        "word_timestamps": True,

        "word_count": total_words,
    }

    # ========================================================
    # TIME
    # ========================================================

    elapsed = time.perf_counter() - start_time

    result["transcription_time"] = elapsed

    # ========================================================
    # REALTIME FACTOR
    # ========================================================

    duration = result["duration"]

    if duration > 0:

        realtime_factor = elapsed / duration

    else:

        realtime_factor = 0.0

    result["realtime_factor"] = realtime_factor

    # ========================================================
    # SAVE CACHE
    # ========================================================

    if cache_path is not None:

        cache_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with cache_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=2,
            )

        print()
        print("[OK] Transcript cache saved:")
        print(cache_path)

    # ========================================================
    # STATISTICS
    # ========================================================

    print()
    print("=" * 60)
    print("TRANSCRIPTION COMPLETE")
    print("=" * 60)

    print(
        f"Video duration : {duration:.2f} sec"
    )

    print(
        f"Processing     : {elapsed:.2f} sec"
    )

    print(
        f"Segments       : {len(result_segments)}"
    )

    print(
        f"Words          : {total_words}"
    )

    print(
        f"Realtime factor: {realtime_factor:.3f}x"
    )

    print(
        "Word timestamps: ENABLED"
    )

    print("=" * 60)

    return result