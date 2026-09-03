from __future__ import annotations

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

# Railway Variables:
#
# WHISPER_MODEL=base
#
# Pilihan:
# tiny
# base
# small
#
# Untuk Railway CPU/RAM terbatas:
# base direkomendasikan.
MODEL_SIZE = os.getenv(
    "WHISPER_MODEL",
    "base",
).strip()


# ============================================================
# DEVICE
# ============================================================

DEVICE = os.getenv(
    "WHISPER_DEVICE",
    "cpu",
).strip().lower()


# ============================================================
# COMPUTE TYPE
# ============================================================

# CPU Railway:
# int8
#
# Jika muncul masalah compatibility:
# int8_float32
#
# Default menggunakan int8.
COMPUTE_TYPE = os.getenv(
    "WHISPER_COMPUTE_TYPE",
    "int8",
).strip()


# ============================================================
# LANGUAGE
# ============================================================

LANGUAGE = os.getenv(
    "WHISPER_LANGUAGE",
    "id",
).strip()


# ============================================================
# BEAM SIZE
# ============================================================

BEAM_SIZE = int(
    os.getenv(
        "WHISPER_BEAM_SIZE",
        "5",
    )
)


# ============================================================
# BEST OF
# ============================================================

BEST_OF = int(
    os.getenv(
        "WHISPER_BEST_OF",
        "5",
    )
)


# ============================================================
# CPU THREADS
# ============================================================

CPU_THREADS = int(
    os.getenv(
        "WHISPER_CPU_THREADS",
        "4",
    )
)


# ============================================================
# WORKERS
# ============================================================

NUM_WORKERS = int(
    os.getenv(
        "WHISPER_NUM_WORKERS",
        "1",
    )
)


# ============================================================
# HF TOKEN
# ============================================================

# Token tidak diberikan ke WhisperModel().
#
# faster-whisper hanya membutuhkan nama model.
#
# Variabel ini tetap dibaca untuk logging/status saja.
HF_TOKEN = os.getenv(
    "HF_TOKEN",
)


# ============================================================
# MODEL CACHE
# ============================================================

_model: WhisperModel | None = None


# ============================================================
# UTILITY
# ============================================================

def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Mengubah value menjadi float dengan aman.
    """

    try:

        if value is None:
            return default

        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return default


# ============================================================
# LOAD MODEL
# ============================================================

def get_model() -> WhisperModel:
    """
    Load Faster-Whisper model.

    Model hanya dibuat satu kali dan kemudian
    disimpan di memory.
    """

    global _model

    # --------------------------------------------------------
    # RETURN CACHE
    # --------------------------------------------------------

    if _model is not None:

        return _model

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

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
        f"Language       : {LANGUAGE}"
    )

    print(
        f"Beam size      : {BEAM_SIZE}"
    )

    print(
        f"Best of        : {BEST_OF}"
    )

    print(
        f"HF Token       : "
        f"{'YES' if HF_TOKEN else 'NO'}"
    )

    print("=" * 70)

    start_time = time.perf_counter()

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    try:

        print()
        print(
            "[INFO] Membuat WhisperModel..."
        )

        # ====================================================
        # PENTING
        # ====================================================
        #
        # JANGAN gunakan:
        #
        # token=HF_TOKEN
        #
        # karena pada kombinasi versi package kamu,
        # token tersebut diteruskan ke CTranslate2
        # dan menyebabkan:
        #
        # TypeError:
        # incompatible constructor arguments
        #
        # ====================================================

        _model = WhisperModel(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            cpu_threads=CPU_THREADS,
            num_workers=NUM_WORKERS,
        )

    except TypeError as e:

        print()
        print("=" * 70)
        print("WHISPER CONSTRUCTOR ERROR")
        print("=" * 70)

        print(
            f"{type(e).__name__}: {e}"
        )

        print()

        traceback.print_exc()

        print()
        print(
            "[ERROR] Faster-Whisper gagal membuat model."
        )

        print(
            "[ERROR] Periksa versi faster-whisper "
            "dan ctranslate2."
        )

        print("=" * 70)

        raise RuntimeError(
            "Faster-Whisper gagal membuat model. "
            "Pastikan token tidak dikirim ke "
            "WhisperModel() dan gunakan kombinasi "
            "versi faster-whisper/ctranslate2 "
            "yang kompatibel."
        ) from e

    except Exception as e:

        print()
        print("=" * 70)
        print("WHISPER MODEL ERROR")
        print("=" * 70)

        print(
            f"Error type : {type(e).__name__}"
        )

        print(
            f"Error      : {e}"
        )

        print()

        traceback.print_exc()

        print("=" * 70)

        raise RuntimeError(
            f"Gagal memuat Faster-Whisper model: {e}"
        ) from e

    # --------------------------------------------------------
    # TIMER
    # --------------------------------------------------------

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print()
    print("=" * 70)
    print("WHISPER MODEL READY")
    print("=" * 70)

    print(
        f"[OK] Model loaded in {elapsed:.2f} seconds."
    )

    print(
        f"Model          : {MODEL_SIZE}"
    )

    print(
        f"Device         : {DEVICE}"
    )

    print(
        f"Compute type   : {COMPUTE_TYPE}"
    )

    print("=" * 70)

    return _model


# ============================================================
# TRANSCRIBE AUDIO
# ============================================================

def transcribe_audio(
    audio_path: Path,
    cache_path: Path | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """
    Transcribe audio/video menggunakan Faster-Whisper.

    Features:
    - Bahasa Indonesia
    - Word timestamps
    - VAD
    - Cache JSON
    - Progress logging
    - Realtime factor
    """

    # ========================================================
    # NORMALIZE PATH
    # ========================================================

    audio_path = Path(
        audio_path
    )

    # ========================================================
    # VALIDATE FILE
    # ========================================================

    if not audio_path.exists():

        raise FileNotFoundError(
            f"Audio/video tidak ditemukan: "
            f"{audio_path}"
        )

    if not audio_path.is_file():

        raise RuntimeError(
            f"Path bukan file: {audio_path}"
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
        f"Input           : {audio_path}"
    )

    print(
        f"File size       : {file_size:,} bytes"
    )

    print(
        f"Model           : {MODEL_SIZE}"
    )

    print(
        f"Device          : {DEVICE}"
    )

    print(
        f"Compute         : {COMPUTE_TYPE}"
    )

    print(
        f"Language        : {LANGUAGE}"
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
        and Path(cache_path).exists()
        and not force
    ):

        cache_path = Path(
            cache_path
        )

        print()
        print(
            "[CACHE] Loading transcript cache..."
        )

        try:

            with cache_path.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

        except json.JSONDecodeError as e:

            print(
                "[WARNING] Cache JSON rusak."
            )

            print(
                f"[WARNING] {e}"
            )

            print(
                "[WARNING] Melakukan transcription ulang."
            )

            data = None

        except OSError as e:

            print(
                "[WARNING] Tidak dapat membaca cache."
            )

            print(
                f"[WARNING] {e}"
            )

            data = None

        if isinstance(
            data,
            dict,
        ):

            segments = data.get(
                "segments"
            )

            if segments:

                print(
                    "[OK] Transcript cache loaded."
                )

                print(
                    f"[CACHE] Segments: "
                    f"{len(segments)}"
                )

                print("=" * 70)

                return data

            print(
                "[WARNING] Cache tidak memiliki segments."
            )

            print(
                "[WARNING] Melakukan transcription ulang."
            )

    # ========================================================
    # LOAD MODEL
    # ========================================================

    model = get_model()

    # ========================================================
    # TIMER
    # ========================================================

    start_time = time.perf_counter()

    # ========================================================
    # HEADER
    # ========================================================

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

    print()
    print(
        "Word-level timestamps : ENABLED"
    )

    print(
        "VAD                   : ENABLED"
    )

    print("=" * 70)

    # ========================================================
    # TRANSCRIBE
    # ========================================================

    try:

        segments, info = model.transcribe(

            str(audio_path),

            # ------------------------------------------------
            # LANGUAGE
            # ------------------------------------------------

            language=LANGUAGE,

            # ------------------------------------------------
            # BEAM SEARCH
            # ------------------------------------------------

            beam_size=BEAM_SIZE,

            # ------------------------------------------------
            # BEST OF
            # ------------------------------------------------

            best_of=BEST_OF,

            # ------------------------------------------------
            # TEMPERATURE
            # ------------------------------------------------

            temperature=0,

            # ------------------------------------------------
            # CONTEXT
            # ------------------------------------------------

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
        # RESULT CONTAINERS
        # ====================================================

        result_segments: list[
            dict[str, Any]
        ] = []

        full_text: list[str] = []

        total_words = 0

        segment_number = 0

        # ====================================================
        # PROCESS SEGMENTS
        # ====================================================

        for segment in segments:

            segment_number += 1

            # ------------------------------------------------
            # TEXT
            # ------------------------------------------------

            text = (
                segment.text or ""
            ).strip()

            if not text:

                continue

            # ------------------------------------------------
            # WORDS
            # ------------------------------------------------

            words: list[
                dict[str, Any]
            ] = []

            segment_words = getattr(
                segment,
                "words",
                None,
            )

            if segment_words:

                for word in segment_words:

                    word_text = (
                        getattr(
                            word,
                            "word",
                            "",
                        )
                        or ""
                    ).strip()

                    if not word_text:

                        continue

                    word_start = _safe_float(
                        getattr(
                            word,
                            "start",
                            None,
                        )
                    )

                    word_end = _safe_float(
                        getattr(
                            word,
                            "end",
                            None,
                        )
                    )

                    word_data: dict[
                        str,
                        Any,
                    ] = {
                        "start": word_start,
                        "end": word_end,
                        "word": word_text,
                    }

                    # ----------------------------------------
                    # PROBABILITY
                    # ----------------------------------------

                    probability = getattr(
                        word,
                        "probability",
                        None,
                    )

                    if probability is not None:

                        word_data[
                            "probability"
                        ] = _safe_float(
                            probability
                        )

                    words.append(
                        word_data
                    )

            # ------------------------------------------------
            # TOTAL WORDS
            # ------------------------------------------------

            total_words += len(
                words
            )

            # ------------------------------------------------
            # SEGMENT DATA
            # ------------------------------------------------

            segment_data: dict[
                str,
                Any,
            ] = {

                "start": _safe_float(
                    getattr(
                        segment,
                        "start",
                        None,
                    )
                ),

                "end": _safe_float(
                    getattr(
                        segment,
                        "end",
                        None,
                    )
                ),

                "text": text,

                "words": words,
            }

            result_segments.append(
                segment_data
            )

            full_text.append(
                text
            )

            # =================================================
            # PROGRESS
            # =================================================

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

        if not result_segments:

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

        if not detected_language:

            detected_language = LANGUAGE

        language_probability = _safe_float(
            getattr(
                info,
                "language_probability",
                None,
            )
        )

        duration = _safe_float(
            getattr(
                info,
                "duration",
                None,
            )
        )

        # ====================================================
        # FULL TEXT
        # ====================================================

        combined_text = " ".join(
            full_text
        ).strip()

        # ====================================================
        # RESULT
        # ====================================================

        result: dict[str, Any] = {

            "text": combined_text,

            "language": detected_language,

            "language_probability":
                language_probability,

            "duration": duration,

            "segments": result_segments,

            "word_timestamps": True,

            "word_count": total_words,
        }

        # ====================================================
        # PROCESSING TIME
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

            # ----------------------------------------------
            # Temporary cache
            # ----------------------------------------------

            temp_path = cache_path.with_suffix(
                cache_path.suffix + ".tmp"
            )

            try:

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

                # ------------------------------------------
                # Atomic replace
                # ------------------------------------------

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

            except Exception:

                # ------------------------------------------
                # Cleanup temporary file
                # ------------------------------------------

                try:

                    temp_path.unlink(
                        missing_ok=True
                    )

                except Exception:

                    pass

                raise

        # ====================================================
        # COMPLETE
        # ====================================================

        print()
        print("=" * 70)
        print("TRANSCRIPTION COMPLETE")
        print("=" * 70)

        print(
            f"Video duration  : "
            f"{duration:.2f} sec"
        )

        print(
            f"Processing      : "
            f"{elapsed:.2f} sec"
        )

        print(
            f"Segments        : "
            f"{len(result_segments)}"
        )

        print(
            f"Words           : "
            f"{total_words}"
        )

        print(
            f"Realtime factor : "
            f"{realtime_factor:.3f}x"
        )

        print(
            f"Language        : "
            f"{detected_language}"
        )

        print(
            f"Language prob.  : "
            f"{language_probability:.4f}"
        )

        print(
            "Word timestamps : ENABLED"
        )

        print("=" * 70)

        return result

    # ========================================================
    # ERROR
    # ========================================================

    except Exception as e:

        elapsed = (
            time.perf_counter()
            - start_time
        )

        print()
        print("=" * 70)
        print("FASTER-WHISPER FAILED")
        print("=" * 70)

        print(
            f"Error type : "
            f"{type(e).__name__}"
        )

        print(
            f"Error      : {e}"
        )

        print(
            f"Elapsed    : "
            f"{elapsed:.2f} sec"
        )

        print()
        print(
            "FULL TRACEBACK:"
        )

        traceback.print_exc()

        print("=" * 70)

        raise