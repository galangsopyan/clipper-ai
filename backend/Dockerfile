FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ============================================================
# SYSTEM DEPENDENCIES
# ============================================================

RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# INSTALL DENO
# ============================================================

RUN curl -fsSL https://deno.land/install.sh | sh

ENV DENO_INSTALL=/root/.deno
ENV PATH=/root/.deno/bin:$PATH

# Verify Deno exists
RUN deno --version

# ============================================================
# PYTHON DEPENDENCIES
# ============================================================

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir \
    "yt-dlp[default]"

RUN pip install --no-cache-dir \
    -r requirements.txt

# ============================================================
# APPLICATION
# ============================================================

COPY . .

# ============================================================
# VERIFY IMPORTANT COMPONENTS
# ============================================================

RUN python -c "import yt_dlp; print('yt-dlp:', yt_dlp.version.__version__)"

RUN python -c "import yt_dlp_ejs; print('yt-dlp-ejs: OK')"

RUN ffmpeg -version | head -n 1

RUN deno --version

# ============================================================
# PORT
# ============================================================

EXPOSE 8000

# IMPORTANT:
# backend/main.py adalah API utama
# bukan app/main.py
# ============================================================

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]