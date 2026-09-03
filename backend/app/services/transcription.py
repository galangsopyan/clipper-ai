from pathlib import Path
from typing import Any
import json
import os
import time

from faster_whisper import WhisperModel


# ============================================================
# CONFIG
# ============================================================

# Model Whisper
#
# small = akurasi lebih baik daripada base
# base  = lebih ringan untuk Railway
#
# Bisa diubah melalui Railway Variables:
#
# WHISPER_MODEL=small
#
MODEL_SIZE = os.getenv(
    "WHISPER_MODEL",
    "small",
)

# Railway biasanya menggunakan CPU
DEVICE = os.getenv(
    "WHISPER_DEVICE",
    "cpu",
)

# INT8 lebih hemat RAM untuk CPU
COMPUTE_TYPE = os.getenv(
    "WHISPER_COMPUTE_TYPE",
    "int8",
)

# Bahasa Indonesia
LANGUAGE = os.getenv(
    "WHISPER_LANGUAGE",
    "id",
)

# Jumlah thread CPU
#
# Jangan terlalu tinggi karena Railway memiliki
# resource terbatas.
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

# Akurasi
BEAM_SIZE = int(
    os.getenv(
        "WHISPER_BEAM_SIZE",
        "5",
    )
)

BEST_OF = int(
    os.getenv(
        "WHISPER_BEST_OF",
        "5",
    )
)

# VAD
MIN_SILENCE_DURATION_MS = int(
    os.getenv(
        "WHISPER_MIN_SILENCE_MS",
        "500",
    )
)


# ============================================================
# MODEL CACHE
# ============================================================

_model: WhisperModel | None = None


# ============================================================
# LOG HELPER
# ============================================================

def print_header(
    title: str,
):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def print_config():
    print_header(
        "WHISPER CONFIGURATION"
    )

    print(
        f"Model                 : {MODEL_SIZE}"
    )

    print(
        f"Device                : {DEVICE}"
    )

    print(
        f"Compute type          : {COMPUTE_TYPE}"
    )

    print(
        f"Language              : {LANGUAGE}"
    )

    print(
        f"CPU threads           : {CPU_THREADS}"
    )

    print(
        f"Workers               : {NUM_WORKERS}"
    )

    print(
        f"Beam size             : {BEAM_SIZE}"
    )

    print(
        f"Best of               : {BEST_OF}"
    )

    print(
        f"Word timestamps       : ENABLED"
    )

    print(
        f"VAD                   : ENABLED"
    )

    print(
        f"Min silence           : "
        f"{MIN_SILENCE_DURATION_MS} ms"
    )


# ============================================================
# MODEL CACHE DIRECTORY
# ============================================================

def get_model_download_path() -> Path:
    """
    Menentukan lokasi cache model Whisper.

    Railway dapat menggunakan HF_HOME atau
    WHISPER_MODEL_DIR jika tersedia.
    """

    custom_dir = os.getenv(
        "WHISPER_MODEL_DIR"
    )

    if custom_dir:
        path = Path(
            custom_dir
        )

    else:
        hf_home = os.getenv(
            "HF_HOME"
        )

        if hf_home:
            path = Path(
                hf_home
            ) / "hub"

        else:
            path = (
                Path.home()
                / ".cache"
                / "huggingface"
                / "hub"
            )

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


# ============================================================
# LOAD MODEL
# ============================================================

def get_model() -> WhisperModel:

    global _model

    # --------------------------------------------------------
    # MODEL SUDAH ADA
    # --------------------------------------------------------

    if _model is not None:

        return _model

    # --------------------------------------------------------
    # CONFIG
    # --------------------------------------------------------

    print_config()

    model_cache_dir = (
        get_model_download_path()
    )

    print_header(
        "LOADING FASTER-WHISPER MODEL"
    )

    print(
        f"Model              : {MODEL_SIZE}"
    )

    print(
        f"Device             : {DEVICE}"
    )

    print(
        f"Compute            : {COMPUTE_TYPE}"
    )

    print(
        f"CPU threads        : {CPU_THREADS}"
    )

    print(
        f"Workers            : {NUM_WORKERS}"
    )

    print(
        f"Model cache        : "
        f"{model_cache_dir}"
    )

    # --------------------------------------------------------
    # HF TOKEN
    # --------------------------------------------------------

    hf_token = os.getenv(
        "HF_TOKEN"
    )

    if hf_token:

        print(
            "Hugging Face token : configured"
        )

    else:

        print(
            "Hugging Face token : not configured"
        )

        print(
            "Public model akan dicoba tanpa token."
        )

    # --------------------------------------------------------
    # TIMER
    # --------------------------------------------------------

    start_time = time.perf_counter()

    # --------------------------------------------------------
    # LOAD MODEL
    # --------------------------------------------------------

    try:

        model_kwargs = {
            "device": DEVICE,
            "compute_type": COMPUTE_TYPE,
            "cpu_threads": CPU_THREADS,
            "num_workers": NUM_WORKERS,
            "download_root": str(
                model_cache_dir
            ),
        }

        # Token hanya ditambahkan jika tersedia.
        #
        # Faster-Whisper menggunakan parameter
        # yang diteruskan ke model downloader.
        #
        if hf_token:

            model_kwargs[
                "token"
            ] = hf_token

        _model = WhisperModel(
            MODEL_SIZE,
            **model_kwargs,
        )

    except TypeError as e:

        # ----------------------------------------------------
        # FALLBACK
        #
        # Beberapa versi faster-whisper/CTranslate2
        # mungkin tidak menerima token langsung.
        # Dalam kasus tersebut model tetap dicoba
        # menggunakan cache/download normal.
        # ----------------------------------------------------

        print_header(
            "WHISPER MODEL LOAD WARNING"
        )

        print(
            "Parameter token tidak didukung "
            "oleh versi faster-whisper ini."
        )

        print(
            f"Error: {e}"
        )

        print(
            "Mencoba load ulang tanpa token..."
        )

        try:

            _model = WhisperModel(
                MODEL_SIZE,
                device=DEVICE,
                compute_type=COMPUTE_TYPE,
                cpu_threads=CPU_THREADS,
                num_workers=NUM_WORKERS,
                download_root=str(
                    model_cache_dir
                ),
            )

        except Exception as retry_error:

            print_header(
                "WHISPER MODEL LOAD FAILED"
            )

            print(
                f"Error type : "
                f"{type(retry_error).__name__}"
            )

            print(
                f"Error      : "
                f"{retry_error}"
            )

            raise

    except Exception as e:

        # ----------------------------------------------------
        # ERROR UTAMA
        # ----------------------------------------------------

        print_header(
            "WHISPER MODEL LOAD FAILED"
        )

        print(
            f"Error type : "
            f"{type(e).__name__}"
        )

        print(
            f"Error      : "
            f"{e}"
        )

        print(
            f"Model      : "
            f"{MODEL_SIZE}"
        )

        print(
            f"Device     : "
            f"{DEVICE}"
        )

        print(
            f"Compute    : "
            f"{COMPUTE_TYPE}"
        )

        print(
            f"Threads    : "
            f"{CPU_THREADS}"
        )

        print(
            f"Cache      : "
            f"{model_cache_dir}"
        )

        print_header(
            "END WHISPER MODEL ERROR"
        )

        raise

    # --------------------------------------------------------
    # LOAD TIME
    # --------------------------------------------------------

    load_time = (
        time.perf_counter()
        - start_time
    )

    print()
    print(
        f"[OK] Whisper model loaded."
    )

    print(
        f"Load time : "
        f"{load_time:.2f} seconds"
    )

    print(
        f"Model     : "
        f"{MODEL_SIZE}"
    )

    print_header(
        "WHISPER MODEL READY"
    )

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
    # VALIDATE PATH
    # ========================================================

    audio_path = Path(
        audio_path
    )

    if not audio_path.exists():

        raise FileNotFoundError(
            f"Audio/video tidak ditemukan: "
            f"{audio_path}"
        )

    if not audio_path.is_file():

        raise RuntimeError(
            f"Path bukan file: "
            f"{audio_path}"
        )

    # ========================================================
    # FILE SIZE
    # ========================================================

    file_size = audio_path.stat().st_size

    if file_size <= 0:

        raise RuntimeError(
            "File audio/video kosong."
        )

    # ========================================================
    # HEADER
    # ========================================================

    print_header(
        "WHISPER WORD-LEVEL TRANSCRIPTION"
    )

    print(
        f"Input       : "
        f"{audio_path}"
    )

    print(
        f"File size   : "
        f"{file_size:,} bytes"
    )

    print(
        f"Model       : "
        f"{MODEL_SIZE}"
    )

    print(
        f"Device      : "
        f"{DEVICE}"
    )

    print(
        f"Compute     : "
        f"{COMPUTE_TYPE}"
    )

    print(
        "Word timing : ENABLED"
    )

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
            f"Loading transcript cache:"
        )

        print(
            cache_path
        )

        try:

            with cache_path.open(
                "r",
                encoding="utf-8",
            ) as file:

                cached_result = json.load(
                    file
                )

            if not isinstance(
                cached_result,
                dict,
            ):

                raise RuntimeError(
                    "Format cache transcript "
                    "tidak valid."
                )

            print(
                "[OK] Transcript cache loaded."
            )

            return cached_result

        except Exception as e:

            print(
                "[WARNING] Cache tidak dapat "
                "digunakan."
            )

            print(
                f"[WARNING] {e}"
            )

            print(
                "Transcription baru akan dijalankan."
            )

    # ========================================================
    # MODEL
    # ========================================================

    model = get_model()

    # ========================================================
    # TIMER
    # ========================================================

    start_time = time.perf_counter()

    # ========================================================
    # TRANSCRIBE START
    # ========================================================

    print_header(
        "STARTING FASTER-WHISPER"
    )

    print(
        f"Input       : "
        f"{audio_path}"
    )

    print(
        f"Model       : "
        f"{MODEL_SIZE}"
    )

    print(
        f"Language    : "
        f"{LANGUAGE}"
    )

    print(
        f"Beam size   : "
        f"{BEAM_SIZE}"
    )

    print(
        f"Best of     : "
        f"{BEST_OF}"
    )

    print(
        "Word timing : ENABLED"
    )

    print(
        "VAD         : ENABLED"
    )

    # ========================================================
    # FASTER-WHISPER
    # ========================================================

    try:

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

            # ------------------------------------------------
            # CONTEXT
            # ------------------------------------------------

            condition_on_previous_text=True,

            # ------------------------------------------------
            # VAD
            # ------------------------------------------------

            vad_filter=True,

            vad_parameters={
                "min_silence_duration_ms":
                    MIN_SILENCE_DURATION_MS,
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

    except Exception as e:

        print_header(
            "FASTER-WHISPER TRANSCRIPTION FAILED"
        )

        print(
            f"Error type : "
            f"{type(e).__name__}"
        )

        print(
            f"Error      : "
            f"{e}"
        )

        print(
            f"Input      : "
            f"{audio_path}"
        )

        print(
            f"File size  : "
            f"{file_size:,} bytes"
        )

        print(
            f"Model      : "
            f"{MODEL_SIZE}"
        )

        print(
            f"Device     : "
            f"{DEVICE}"
        )

        print(
            f"Compute    : "
            f"{COMPUTE_TYPE}"
        )

        print_header(
            "END TRANSCRIPTION ERROR"
        )

        raise

    # ========================================================
    # BUILD RESULT
    # ========================================================

    result_segments = []

    full_text = []

    total_words = 0

    # ========================================================
    # PROCESS SEGMENTS
    # ========================================================

    try:

        for segment in segments:

            text = (
                segment.text
                .strip()
            )

            if not text:
                continue

            # ------------------------------------------------
            # WORDS
            # ------------------------------------------------

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

                    # ----------------------------------------
                    # PROBABILITY
                    # ----------------------------------------

                    if (
                        word.probability
                        is not None
                    ):

                        word_data[
                            "probability"
                        ] = float(
                            word.probability
                        )

                    words.append(
                        word_data
                    )

            total_words += len(
                words
            )

            # ------------------------------------------------
            # SEGMENT
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

            full_text.append(
                text
            )

    except Exception as e:

        print_header(
            "WHISPER RESULT PROCESSING FAILED"
        )

        print(
            f"Error type : "
            f"{type(e).__name__}"
        )

        print(
            f"Error      : "
            f"{e}"
        )

        raise

    # ========================================================
    # VALIDATE RESULT
    # ========================================================

    if len(result_segments) == 0:

        raise RuntimeError(
            "Whisper selesai tetapi "
            "tidak menghasilkan segment."
        )

    # ========================================================
    # INFO
    # ========================================================

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

    # ========================================================
    # RESULT
    # ========================================================

    result = {

        "text": " ".join(
            full_text
        ),

        "language": detected_language,

        "language_probability": float(
            language_probability
            if language_probability is not None
            else 0.0
        ),

        "duration": float(
            duration
            if duration
            else 0.0
        ),

        "segments": result_segments,

        "word_timestamps": True,

        "word_count": total_words,
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
    # REALTIME FACTOR
    # ========================================================

    duration_value = result[
        "duration"
    ]

    if duration_value > 0:

        realtime_factor = (
            elapsed
            / duration_value
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

        cache_path = Path(
            cache_path
        )

        cache_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_cache = cache_path.with_suffix(
            cache_path.suffix + ".tmp"
        )

        try:

            with temp_cache.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    result,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

            temp_cache.replace(
                cache_path
            )

            print()
            print(
                "[OK] Transcript cache saved:"
            )

            print(
                cache_path
            )

        except Exception as e:

            print_header(
                "CACHE SAVE FAILED"
            )

            print(
                f"Error type : "
                f"{type(e).__name__}"
            )

            print(
                f"Error      : "
                f"{e}"
            )

            # Temporary file dibersihkan
            try:

                if temp_cache.exists():

                    temp_cache.unlink()

            except Exception:
                pass

            raise

    # ========================================================
    # STATISTICS
    # ========================================================

    print_header(
        "TRANSCRIPTION COMPLETE"
    )

    print(
        f"Video duration : "
        f"{duration_value:.2f} sec"
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
        f"Words          : "
        f"{total_words}"
    )

    print(
        f"Realtime factor: "
        f"{realtime_factor:.3f}x"
    )

    print(
        f"Language       : "
        f"{detected_language}"
    )

    print(
        f"Word timestamps: ENABLED"
    )

    print_header(
        "TRANSCRIPTION SUCCESS"
    )

    return result