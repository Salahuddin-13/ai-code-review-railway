from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from dotenv import load_dotenv

# =========================
# Base paths
# =========================
APP_DIR = Path(__file__).resolve().parent        # backend/app
BACKEND_DIR = APP_DIR.parent                     # backend
PROJECT_ROOT = BACKEND_DIR.parent                # ai-code-review

# Load env from backend/.env
load_dotenv(dotenv_path=BACKEND_DIR / ".env")

app = FastAPI(title="AI Code Review Agent")

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Frontend path (CORRECT)
# =========================
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Only mount if folder exists (prevents crash)
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# =========================
# Routes
# =========================
@app.get("/")
async def root():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Backend running — frontend not found"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Import AFTER env loaded
from app.routes import router
app.include_router(router, prefix="/api")

# =========================
# Run directly
# =========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)