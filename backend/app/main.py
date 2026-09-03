from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="ClipForge AI",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    # Development
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://clipper-ai-azure.vercel.app",

        # Tambahkan domain frontend Vercel kamu di sini
        # contoh:
        # "https://clipforge-ai.vercel.app",
    ],

    allow_credentials=True,

    allow_methods=[
        "*",
    ],

    allow_headers=[
        "*",
    ],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "status": "ok",
        "message": "ClipForge AI Backend is running",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
    }