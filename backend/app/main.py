from fastapi import FastAPI

app = FastAPI(
    title="ClipForge AI",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "ClipForge AI Backend is running"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }