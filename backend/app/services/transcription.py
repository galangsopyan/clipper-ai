from pathlib import Path
from typing import Any
import json
import time

from faster_whisper import WhisperModel


# ============================================================
# CONFIG - OPTIMIZED FOR AMD RYZEN 5 5600G
# ============================================================

MODEL_SIZE = "base"

DEVICE = "cpu"
COMPUTE_TYPE = "int8"

# Kecepatan lebih penting daripada beam search besar
BEAM_SIZE = 1
BEST_OF = 1

# Bahasa Indonesia
LANGUAGE = "id"

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
# TRANSCRIBE AUDIO / VIDEO
# ============================================================

def transcribe_audio(
    audio_path: Path,
    cache_path: Path | None = None,
    force: bool = False,
) -> dict[str, Any]:

    # ========================================================
    # VALIDATE FILE
    # ========================================================

    if not audio_path.exists():

        raise FileNotFoundError(
            f"Audio/video tidak ditemukan: "
            f"{audio_path}"
        )

    file_size = audio_path.stat().st_size

    if file_size <= 0:

        raise RuntimeError(
            "File audio/video kosong."
        )

    print("=" * 60)
    print("WHISPER TRANSCRIPTION")
    print("=" * 60)

    print(
        f"Input       : {audio_path}"
    )

    print(
        f"File size   : {file_size:,} bytes"
    )

    print(
        f"Model       : {MODEL_SIZE}"
    )

    print(
        f"Device      : {DEVICE}"
    )

    print(
        f"Compute     : {COMPUTE_TYPE}"
    )

    # ========================================================
    # CACHE
    # ========================================================

    if (
        cache_path is not None
        and cache_path.exists()
        and not force
    ):

        print(
            f"Loading transcript cache: "
            f"{cache_path}"
        )

        with cache_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    # ========================================================
    # LOAD MODEL
    # ========================================================

    model = get_model()

    # ========================================================
    # START TIMER
    # ========================================================

    start_time = time.perf_counter()

    print(
        "\nStarting local Whisper transcription..."
    )

    # ========================================================
    # TRANSCRIBE
    # ========================================================

    segments, info = model.transcribe(

        str(audio_path),

        # Bahasa Indonesia
        language="id",

        # ====================================================
        # SPEED OPTIMIZATION
        # ====================================================

        beam_size=1,

        best_of=1,

        # Jangan mempertahankan konteks terlalu agresif
        # sehingga processing lebih cepat.
        condition_on_previous_text=False,

        # Buang bagian yang tidak memiliki speech
        vad_filter=True,

        # Threshold VAD
        vad_parameters={
            "min_silence_duration_ms": 500,
        },
    )

    # ========================================================
    # BUILD RESULT
    # ========================================================

    result_segments = []

    full_text = []

    for segment in segments:

        text = segment.text.strip()

        if not text:
            continue

        result_segments.append(
            {
                "start": float(
                    segment.start
                ),

                "end": float(
                    segment.end
                ),

                "text": text,
            }
        )

        full_text.append(text)

    # ========================================================
    # RESULT
    # ========================================================

    result = {

        "text": " ".join(
            full_text
        ),

        "language": info.language,

        "language_probability": float(
            info.language_probability
        ),

        "duration": float(
            info.duration
        )
        if info.duration
        else 0.0,

        "segments": result_segments,
    }

    # ========================================================
    # TIME
    # ========================================================

    elapsed = (
        time.perf_counter()
        - start_time
    )

    result[
        "transcription_time"
    ] = elapsed

    # ========================================================
    # REAL-TIME FACTOR
    # ========================================================

    duration = result["duration"]

    if duration > 0:

        realtime_factor = (
            elapsed / duration
        )

    else:

        realtime_factor = 0.0

    result[
        "realtime_factor"
    ] = realtime_factor

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

        print(
            f"\n[OK] Transcript cache saved:"
        )

        print(
            cache_path
        )

    # ========================================================
    # STATISTICS
    # ========================================================

    print("\n" + "=" * 60)
    print("TRANSCRIPTION COMPLETE")
    print("=" * 60)

    print(
        f"Video duration : "
        f"{duration:.2f} sec"
    )

    print(
        f"Processing     : "
        f"{elapsed:.2f} sec"
    )

    print(
        f"Segments       : "
        f"{len(result_segments)}"
    )

    print(
        f"Realtime factor: "
        f"{realtime_factor:.3f}x"
    )

    if realtime_factor <= 1:

        print(
            "[FAST] Lebih cepat dari durasi video."
        )

    else:

        print(
            "[INFO] Processing lebih lambat "
            "dari durasi video."
        )

    print("=" * 60)

    return result