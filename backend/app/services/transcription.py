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

# Railway Variable:
#
# WHISPER_MODEL=base
#
# Pilihan:
# tiny
# base
# small
#
# Untuk Railway CPU/RAM terbatas:
# base lebih aman.
MODEL_SIZE = os.getenv(
    "WHISPER_MODEL",
    "base",
)


# ============================================================
# DEVICE
# ============================================================

DEVICE = os.getenv(
    "WHISPER_DEVICE",
    "cpu",
)


# ============================================================
# COMPUTE TYPE
# ============================================================

COMPUTE_TYPE = os.getenv(
    "WHISPER_COMPUTE_TYPE",
    "int8",
)


# ============================================================
# LANGUAGE
# ============================================================

LANGUAGE = os.getenv(
    "WHISPER_LANGUAGE",
    "id",
)


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
# NUM WORKERS
# ============================================================

NUM_WORKERS = int(
    os.getenv(
        "WHISPER_NUM_WORKERS",
        "1",
    )
)


# ============================================================
# HUGGING FACE TOKEN
# ============================================================
#
# Token TIDAK diberikan langsung ke WhisperModel().
#
# Jika Railway memiliki:
#
# HF_TOKEN=hf_xxxxxxxxx
#
# Hugging Face Hub dapat menggunakan environment variable
# tersebut ketika membutuhkan autentikasi.
#
# Jangan melakukan:
#
# WhisperModel(..., token=HF_TOKEN)
#
# karena token tersebut dapat diteruskan ke CTranslate2
# dan menyebabkan:
#
# TypeError: incompatible constructor arguments
#
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
        "[INFO] HF_TOKEN tidak ditemukan."
    )

    print(
        "[INFO] Menggunakan Hugging Face tanpa autentikasi."
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

    # --------------------------------------------------------
    # Gunakan model yang sudah berada di memory
    # --------------------------------------------------------

    if _model is not None:

        return _model

    # --------------------------------------------------------
    # Header
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

    # ========================================================
    # LOAD MODEL
    # ========================================================

    try:

        # ----------------------------------------------------
        # PENTING:
        #
        # JANGAN memasukkan token=HF_TOKEN di sini.
        #
        # SALAH:
        #
        # WhisperModel(
        #     MODEL_SIZE,
        #     ...
        #     token=HF_TOKEN
        # )
        #
        # Hal tersebut menyebabkan token diteruskan ke
        # CTranslate2 dan menghasilkan error:
        #
        # TypeError:
        # incompatible constructor arguments
        #
        # ----------------------------------------------------

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
            f"Error type : {type(e).__name__}"
        )

        print(
            f"Error      : {e}"
        )

        print()
        print(
            "FULL TRACEBACK:"
        )

        traceback.print_exc()

        print("=" * 70)

        raise

    # ========================================================
    # LOAD TIME
    # ========================================================

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print()
    print("=" * 70)

    print(
        f"[OK] Whisper model loaded "
        f"in {elapsed:.2f} seconds."
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
        f"File size      : "
        f"{file_size:,} bytes"
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

        print()
        print(
            "[CACHE] Loading transcript cache..."
        )

        try:

            with Path(
                cache_path
            ).open(
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(
                    file
                )

        except json.JSONDecodeError as e:

            print(
                "[WARNING] Cache JSON rusak."
            )

            print(
                f"[WARNING] {e}"
            )

            print(
                "[INFO] Melakukan transcription ulang."
            )

            data = None

        if isinstance(
            data,
            dict,
        ):

            if data.get(
                "segments"
            ):

                print(
                    "[OK] Transcript cache loaded."
                )

                return data

            print(
                "[WARNING] Cache tidak memiliki segments."
            )

            print(
                "[INFO] Melakukan transcription ulang."
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
    # START
    # ========================================================

    print()
    print("=" * 70)
    print("STARTING FASTER-WHISPER")
    print("=" * 70)

    print(
        "Sedang melakukan transcription."
    )

    print(
        "Word-level timestamps: ENABLED"
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

            text = (
                segment.text
                .strip()
            )

            # ------------------------------------------------
            # Skip empty segment
            # ------------------------------------------------

            if not text:

                continue

            # ------------------------------------------------
            # WORDS
            # ------------------------------------------------

            words: list[
                dict[str, Any]
            ] = []

            if segment.words:

                for word in segment.words:

                    word_text = (
                        word.word
                        .strip()
                    )

                    if not word_text:

                        continue

                    word_data: dict[
                        str,
                        Any
                    ] = {

                        "start": float(
                            word.start
                        ),

                        "end": float(
                            word.end
                        ),

                        "word": word_text,
                    }

                    # ------------------------------------------------
                    # Probability
                    # ------------------------------------------------

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

            # ------------------------------------------------
            # Word count
            # ------------------------------------------------

            total_words += len(
                words
            )

            # ------------------------------------------------
            # Segment
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Full text
            # ------------------------------------------------

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

        result: dict[
            str,
            Any
        ] = {

            "text": " ".join(
                full_text
            ),

            "language": (
                detected_language
            ),

            "language_probability": float(
                language_probability
            ),

            "duration": (
                float(duration)
                if duration
                else 0.0
            ),

            "segments": (
                result_segments
            ),

            "word_timestamps": True,

            "word_count": (
                total_words
            ),
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

        result_duration = result[
            "duration"
        ]

        if result_duration > 0:

            realtime_factor = (
                elapsed
                / result_duration
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

            # ------------------------------------------------
            # Temporary file
            # ------------------------------------------------

            temp_path = cache_path.with_suffix(
                cache_path.suffix
                + ".tmp"
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

                # ------------------------------------------------
                # Atomic replace
                # ------------------------------------------------

                temp_path.replace(
                    cache_path
                )

            except Exception:

                # Bersihkan temp jika gagal

                try:

                    temp_path.unlink(
                        missing_ok=True
                    )

                except Exception:
                    pass

                raise

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
            f"Video duration  : "
            f"{result_duration:.2f} sec"
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
            f"{float(language_probability):.3f}"
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