"""FastAPI app: wiring, middleware, error mapping, and route mounts."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from .api import analysis as analysis_api
from .api import auth as auth_api
from .api import budgets as budgets_api
from .api import expenses as expenses_api
from .api import funds as funds_api
from .api import labels as labels_api
from .api import users as users_api
from .auth_db import connect_auth, init_auth_db
from .config import get_settings
from .db import profile_db_path
from .schemas import HealthResponse
from .services.user_service import DEFAULT_ADMIN_NAME, seed_default_admin

VERSION = "0.2.0"


def _migrate_legacy_db(settings) -> None:
    """One-time: fold a pre-profiles data/khata.db into Chai's profile file."""
    legacy = settings.db_path
    if not legacy.exists():
        return
    conn = connect_auth(settings)
    try:
        row = conn.execute("SELECT id FROM users WHERE name = ? COLLATE NOCASE", (DEFAULT_ADMIN_NAME,)).fetchone()
    finally:
        conn.close()
    if not row:
        return
    target = profile_db_path(settings, row["id"])
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        src = legacy.parent / (legacy.name + suffix)
        if src.exists():
            src.rename(target.parent / (target.name + suffix))


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_auth_db(settings)
    seed_default_admin(settings)
    _migrate_legacy_db(settings)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="khata", version=VERSION, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        msg = str(exc)
        status = 404 if "not found" in msg.lower() else 400
        return JSONResponse(status_code=status, content={"detail": msg})

    for r in (auth_api.router, users_api.router, funds_api.router, labels_api.router,
              labels_api.groups_router, expenses_api.router, budgets_api.router, analysis_api.router):
        app.include_router(r)

    @app.get("/")
    def root() -> dict:
        return {"app": "khata", "version": VERSION, "docs": "/docs"}

    @app.get("/favicon.ico")
    def favicon() -> Response:
        return Response(status_code=204)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", version=VERSION)

    return app


app = create_app()
