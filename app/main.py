import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.database import connect_db, close_db
from app.services.question_service import ensure_indexes
from app.api.v1.router import router

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await ensure_indexes()
    yield
    await close_db()


app = FastAPI(
    title="AdaptIQ — Adaptive Diagnostic Engine",
    description=(
        "A 1-Dimension Adaptive Testing system using Item Response Theory (IRT). "
        "Questions are dynamically selected based on the student's estimated ability level. "
        "After 10 questions, an AI-powered personalized study plan is generated."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)

# Serve the frontend UI
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", tags=["ui"], include_in_schema=False)
async def serve_ui() -> FileResponse:
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "healthy"}
