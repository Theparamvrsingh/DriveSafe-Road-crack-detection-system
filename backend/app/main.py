from __future__ import annotations

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.db.sqlite import init_db, seed_demo_history_if_empty


def create_app() -> FastAPI:
    app = FastAPI(title="DriveSafe Road Crack Detection System", version="0.1.0")

    # ✅ GLOBAL EXCEPTION HANDLER (FIX)
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal Server Error: {str(exc)}"}
        )

    # CORS (allow frontend to call backend)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        # Ensure storage directories exist (important for Docker/cloud deploy)
        storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage"))
        os.makedirs(os.path.join(storage_dir, "uploads"), exist_ok=True)
        os.makedirs(os.path.join(storage_dir, "outputs"), exist_ok=True)
        init_db()
        seed_demo_history_if_empty()

    # API routes
    app.include_router(api_router, prefix="/api")

    # ✅ FRONTEND PATH
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
    print("Frontend dir:", frontend_dir)

    if os.path.isdir(frontend_dir):
        app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")

        @app.get("/", include_in_schema=False)
        def _root() -> RedirectResponse:
            return RedirectResponse(url="/frontend/")

    # ✅ STORAGE SERVING
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    storage_dir = os.path.join(BASE_DIR, "storage")

    if os.path.isdir(storage_dir):
        app.mount("/storage", StaticFiles(directory=storage_dir), name="storage")

    return app


app = create_app()