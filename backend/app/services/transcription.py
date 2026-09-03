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

MODEL_SIZE = os.getenv(
    "WHISPER_MODEL",
    "base",
)

DEVICE = os.getenv(
    "WHISPER_DEVICE",
    "cpu",
)

COMPUTE_TYPE = os.getenv(
    "WHISPER_COMPUTE_TYPE",
    "int8",
)

LANGUAGE = os.getenv(
    "WHISPER_LANGUAGE",
    "id",
)

BEAM_SIZE = int(
    os.getenv(
        "WHISPER_BEAM_SIZE",
        "1",
    )
)

BEST_OF = int(
    os.getenv(
        "WHISPER_BEST_OF",
        "1",
    )
)

CPU_THREADS = int(
    os.getenv(
        "WHISPER_CPU_THREADS",
        "2",
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
        "[INFO] HF_TOKEN tidak tersedia."
    )

    print(
        "[INFO] Model akan menggunakan download "
        "tanpa autentikasi jika diperlukan."
    )


# ============================================================
# MODEL
# ============================================================

_model: WhisperModel | None = None


# ============================================================
# GET MODEL
# ============================================================

def get_model() -> WhisperModel:

    global _model

    # --------------------------------------------------------
    # Jangan load ulang model
    # --------------------------------------------------------

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
        f"HF Token       : "
        f"{'YES' if HF_TOKEN else 'NO'}"
    )

    print("=" * 70)

    start_time = time.perf_counter()

    try:

        # ====================================================
        # PENTING
        # ====================================================
        #
        # JANGAN menggunakan:
        #
        # token=HF_TOKEN
        #
        # karena token tersebut dapat diteruskan ke
        # ctranslate2 dan menyebabkan:
        #
        # TypeError:
        # incompatible constructor arguments
        #
        # Gunakan:
        #
        # use_auth_token=HF_TOKEN
        #
        # ====================================================

        model_kwargs = {
            "device": DEVICE,
            "compute_type": COMPUTE_TYPE,
            "cpu_threads": CPU_THREADS,
            "num_workers": NUM_WORKERS,
        }

        # ----------------------------------------------------
        # Hugging Face authentication
        # ----------------------------------------------------

        if HF_TOKEN:

            model_kwargs[
                "use_auth_token"
            ] = HF_TOKEN

        # ----------------------------------------------------
        # Load model
        # ----------------------------------------------------

        _model = WhisperModel(
            MODEL_SIZE,
            **model_kwargs,
        )

    except TypeError as e:

        print()
        print("=" * 70)
        print("FASTER-WHISPER TYPE ERROR")
        print("=" * 70)

        print(
            str(e)
        )

        print()

        print(
            "Kemungkinan besar ada parameter yang "
            "tidak kompatibel dengan CTranslate2."
        )

        print()

        print(
            "Pastikan tidak ada kode:"
        )

        print(
            "token=HF_TOKEN"
        )

        print()

        print(
            "Gunakan:"
        )

        print(
            "use_auth_token=HF_TOKEN"
        )

        print()

        traceback.print_exc()

        print("=" * 70)

        raise

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

        raise

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print()
    print("=" * 70)
    print("WHISPER MODEL LOADED")
    print("=" * 70)

    print(
        f"Model      : {MODEL_SIZE}"
    )

    print(
        f"Device     : {DEVICE}"
    )

    print(
        f"Compute    : {COMPUTE_TYPE}"
    )

    print(
        f"Load time  : {elapsed:.2f} sec"
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
        "Word timing    : ENABLED"
    )

    print(
        f"Cache          : {cache_path}"
    )

    print(
        f"Force          : {force}"
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

        try:

            with cache_path.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(
                    file
                )

        except Exception as e:

            print(
                "[WARNING] Cache rusak."
            )

            print(
                f"{type(e).__name__}: {e}"
            )

            data = None

        if isinstance(
            data,
            dict,
        ) and data.get(
            "segments"
        ):

            print(
                "[OK] Transcript cache loaded."
            )

            return data

        print(
            "[WARNING] Cache tidak valid."
        )

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
            # TASK
            # ------------------------------------------------

            task="transcribe",

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

            # ------------------------------------------------
            # PROGRESS
            # ------------------------------------------------

            log_progress=True,
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
                or ""
            ).strip()

            if not text:

                continue

            words = []

            if segment.words:

                for word in segment.words:

                    word_text = (
                        word.word
                        or ""
                    ).strip()

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
            # Progress
            # ------------------------------------------------

            if segment_number % 10 == 0:

                elapsed = (
                    time.perf_counter()
                    - start_time
                )

                print(
                    "[TRANSCRIBE] "
                    f"Segments={segment_number} "
                    f"Words={total_words} "
                    f"Elapsed={elapsed:.1f}s"
                )

        # ====================================================
        # VALIDATE
        # ====================================================

        if not result_segments:

            raise RuntimeError(
                "Whisper selesai tetapi tidak "
                "menghasilkan segment."
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

        duration = float(
            duration or 0.0
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
                language_probability or 0.0
            ),

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
            f"Segments        : "
            f"{len(result_segments)}"
        )

        print(
            f"Words           : {total_words}"
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