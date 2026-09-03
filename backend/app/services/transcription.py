from pathlib import Path
from typing import Any
import json
import os
import time
import traceback

from faster_whisper import WhisperModel


# ============================================================
# CONFIG
# ============================================================

# Bisa diganti dari Railway Variables:
# WHISPER_MODEL=small
#
# Pilihan:
# tiny
# base
# small
#
# Untuk Railway dengan RAM terbatas:
# base lebih aman daripada small.
MODEL_SIZE = os.getenv(
    "WHISPER_MODEL",
    "base",
)

# Railway CPU
DEVICE = os.getenv(
    "WHISPER_DEVICE",
    "cpu",
)

# CPU cocok menggunakan int8
COMPUTE_TYPE = os.getenv(
    "WHISPER_COMPUTE_TYPE",
    "int8",
)

LANGUAGE = "id"

# Akurasi
BEAM_SIZE = int(
    os.getenv(
        "WHISPER_BEAM_SIZE",
        "5",
    )
)

# Dipakai jika temperature > 0
BEST_OF = int(
    os.getenv(
        "WHISPER_BEST_OF",
        "5",
    )
)

# CPU thread
CPU_THREADS = int(
    os.getenv(
        "WHISPER_CPU_THREADS",
        "4",
    )
)

NUM_WORKERS = int(
    os.getenv(
        "WHISPER_NUM_WORKERS",
        "1",
    )
)


# ============================================================
# HUGGING FACE
# ============================================================

HF_TOKEN = os.getenv(
    "HF_TOKEN"
)

if HF_TOKEN:
    print(
        "[INFO] HF_TOKEN ditemukan."
    )
else:
    print(
        "[WARNING] HF_TOKEN tidak ditemukan."
    )

    print(
        "[WARNING] Hugging Face akan menggunakan "
        "unauthenticated download."
    )


# ============================================================
# MODEL CACHE
# ============================================================

_model: WhisperModel | None = None


# ============================================================
# LOAD MODEL
# ============================================================

def get_model() -> WhisperModel:

    global _model

    if _model is not None:
        return _model

    print()
    print("=" * 70)
    print("LOADING FASTER-WHISPER MODEL")
    print("=" * 70)

    print(
        f"Model          : {MODEL_SIZE}"
    )

    print(
        f"Device         : {DEVICE}"
    )

    print(
        f"Compute type   : {COMPUTE_TYPE}"
    )

    print(
        f"CPU threads    : {CPU_THREADS}"
    )

    print(
        f"Workers        : {NUM_WORKERS}"
    )

    print(
        f"Beam size      : {BEAM_SIZE}"
    )

    print(
        f"Best of        : {BEST_OF}"
    )

    print(
        f"Language       : {LANGUAGE}"
    )

    print(
        f"HF Token       : {'YES' if HF_TOKEN else 'NO'}"
    )

    print("=" * 70)

    start_time = time.perf_counter()

    try:

        # ----------------------------------------------------
        # Model
        # ----------------------------------------------------

        if HF_TOKEN:

            _model = WhisperModel(
                MODEL_SIZE,
                device=DEVICE,
                compute_type=COMPUTE_TYPE,
                cpu_threads=CPU_THREADS,
                num_workers=NUM_WORKERS,
                token=HF_TOKEN,
            )

        else:

            _model = WhisperModel(
                MODEL_SIZE,
                device=DEVICE,
                compute_type=COMPUTE_TYPE,
                cpu_threads=CPU_THREADS,
                num_workers=NUM_WORKERS,
            )

    except Exception as e:

        print()
        print("=" * 70)
        print("WHISPER MODEL ERROR")
        print("=" * 70)

        print(
            f"{type(e).__name__}: {e}"
        )

        print()
        traceback.print_exc()

        print("=" * 70)

        raise

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print()
    print(
        f"[OK] Whisper model loaded "
        f"in {elapsed:.2f} seconds."
    )

    print("=" * 70)

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

    audio_path = Path(
        audio_path
    )

    if not audio_path.exists():

        raise FileNotFoundError(
            f"Audio/video tidak ditemukan: {audio_path}"
        )

    file_size = audio_path.stat().st_size

    if file_size <= 0:

        raise RuntimeError(
            "File audio/video kosong."
        )

    # ========================================================
    # HEADER
    # ========================================================

    print()
    print("=" * 70)
    print("WHISPER WORD-LEVEL TRANSCRIPTION")
    print("=" * 70)

    print(
        f"Input          : {audio_path}"
    )

    print(
        f"File size      : {file_size:,} bytes"
    )

    print(
        f"Model          : {MODEL_SIZE}"
    )

    print(
        f"Device         : {DEVICE}"
    )

    print(
        f"Compute        : {COMPUTE_TYPE}"
    )

    print(
        f"Language       : {LANGUAGE}"
    )

    print(
        "Word timing     : ENABLED"
    )

    print(
        f"Cache           : {cache_path}"
    )

    print(
        f"Force           : {force}"
    )

    print("=" * 70)

    # ========================================================
    # CACHE
    # ========================================================

    if (
        cache_path is not None
        and cache_path.exists()
        and not force
    ):

        print(
            "[CACHE] Loading transcript cache..."
        )

        with cache_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if not isinstance(
            data,
            dict,
        ):

            raise RuntimeError(
                "Transcript cache bukan object JSON."
            )

        if not data.get(
            "segments"
        ):

            raise RuntimeError(
                "Transcript cache tidak memiliki segments."
            )

        print(
            "[OK] Transcript cache loaded."
        )

        return data

    # ========================================================
    # LOAD MODEL
    # ========================================================

    model = get_model()

    # ========================================================
    # TIMER
    # ========================================================

    start_time = time.perf_counter()

    print()
    print("=" * 70)
    print("STARTING FASTER-WHISPER")
    print("=" * 70)

    print(
        "Sedang melakukan transcription."
    )

    print(
        "Jangan menghentikan proses."
    )

    print("=" * 70)

    try:

        # ====================================================
        # TRANSCRIBE
        # ====================================================

        segments, info = model.transcribe(

            str(audio_path),

            # ------------------------------------------------
            # LANGUAGE
            # ------------------------------------------------

            language=LANGUAGE,

            # ------------------------------------------------
            # ACCURACY
            # ------------------------------------------------

            beam_size=BEAM_SIZE,

            best_of=BEST_OF,

            temperature=0,

            condition_on_previous_text=True,

            # ------------------------------------------------
            # VAD
            # ------------------------------------------------

            vad_filter=True,

            vad_parameters={
                "min_silence_duration_ms": 500,
            },

            # ------------------------------------------------
            # WORD TIMESTAMPS
            # ------------------------------------------------

            word_timestamps=True,

            # ------------------------------------------------
            # TIMESTAMPS
            # ------------------------------------------------

            without_timestamps=False,
        )

        # ====================================================
        # BUILD RESULT
        # ====================================================

        result_segments = []

        full_text = []

        total_words = 0

        segment_number = 0

        # ====================================================
        # PROCESS SEGMENTS
        # ====================================================

        for segment in segments:

            segment_number += 1

            text = (
                segment.text
                .strip()
            )

            if not text:
                continue

            words = []

            if segment.words:

                for word in segment.words:

                    word_text = (
                        word.word
                        .strip()
                    )

                    if not word_text:
                        continue

                    word_data = {
                        "start": float(
                            word.start
                        ),
                        "end": float(
                            word.end
                        ),
                        "word": word_text,
                    }

                    probability = getattr(
                        word,
                        "probability",
                        None,
                    )

                    if probability is not None:

                        word_data[
                            "probability"
                        ] = float(
                            probability
                        )

                    words.append(
                        word_data
                    )

            total_words += len(
                words
            )

            result_segments.append(
                {
                    "start": float(
                        segment.start
                    ),
                    "end": float(
                        segment.end
                    ),
                    "text": text,
                    "words": words,
                }
            )

            full_text.append(
                text
            )

            # ------------------------------------------------
            # Progress log
            # ------------------------------------------------

            if segment_number % 10 == 0:

                elapsed = (
                    time.perf_counter()
                    - start_time
                )

                print(
                    f"[TRANSCRIBE] "
                    f"Segments={segment_number} "
                    f"Words={total_words} "
                    f"Elapsed={elapsed:.1f}s"
                )

        # ====================================================
        # VALIDATE
        # ====================================================

        if len(
            result_segments
        ) == 0:

            raise RuntimeError(
                "Whisper selesai tetapi "
                "tidak menghasilkan segment."
            )

        # ====================================================
        # INFO
        # ====================================================

        detected_language = getattr(
            info,
            "language",
            LANGUAGE,
        )

        language_probability = getattr(
            info,
            "language_probability",
            0.0,
        )

        duration = getattr(
            info,
            "duration",
            0.0,
        )

        # ====================================================
        # RESULT
        # ====================================================

        result = {

            "text": " ".join(
                full_text
            ),

            "language": detected_language,

            "language_probability": float(
                language_probability
            ),

            "duration": float(
                duration
            )
            if duration
            else 0.0,

            "segments": result_segments,

            "word_timestamps": True,

            "word_count": total_words,
        }

        # ====================================================
        # TIME
        # ====================================================

        elapsed = (
            time.perf_counter()
            - start_time
        )

        result[
            "transcription_time"
        ] = elapsed

        # ====================================================
        # REALTIME FACTOR
        # ====================================================

        duration = result[
            "duration"
        ]

        if duration > 0:

            realtime_factor = (
                elapsed / duration
            )

        else:

            realtime_factor = 0.0

        result[
            "realtime_factor"
        ] = realtime_factor

        # ====================================================
        # SAVE CACHE
        # ====================================================

        if cache_path is not None:

            cache_path = Path(
                cache_path
            )

            cache_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            temp_path = cache_path.with_suffix(
                cache_path.suffix + ".tmp"
            )

            with temp_path.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    result,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

            temp_path.replace(
                cache_path
            )

            print()
            print(
                "[OK] Transcript cache saved:"
            )

            print(
                cache_path
            )

        # ====================================================
        # COMPLETE
        # ====================================================

        print()
        print("=" * 70)
        print("TRANSCRIPTION COMPLETE")
        print("=" * 70)

        print(
            f"Video duration  : {duration:.2f} sec"
        )

        print(
            f"Processing      : {elapsed:.2f} sec"
        )

        print(
            f"Segments        : {len(result_segments)}"
        )

        print(
            f"Words           : {total_words}"
        )

        print(
            f"Realtime factor : {realtime_factor:.3f}x"
        )

        print(
            f"Language        : {detected_language}"
        )

        print(
            "Word timestamps : ENABLED"
        )

        print("=" * 70)

        return result

    except Exception as e:

        # ====================================================
        # ERROR
        # ====================================================

        elapsed = (
            time.perf_counter()
            - start_time
        )

        print()
        print("=" * 70)
        print("FASTER-WHISPER FAILED")
        print("=" * 70)

        print(
            f"Error type : {type(e).__name__}"
        )

        print(
            f"Error      : {e}"
        )

        print(
            f"Elapsed    : {elapsed:.2f} sec"
        )

        print()
        print(
            "FULL TRACEBACK:"
        )

        traceback.print_exc()

        print("=" * 70)

        raise