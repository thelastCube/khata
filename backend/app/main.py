"""FastAPI app: wiring, middleware, error mapping, and route mounts."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from .api import analysis as analysis_api
from .api import auth as auth_api
from .api import budgets as budgets_api
from .api import expenses as expenses_api
from .api import funds as funds_api
from .api import labels as labels_api
from .auth import require_auth
from .config import get_settings
from .db import init_db
from .schemas import HealthResponse

VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
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

    # Service-layer validation errors -> 404 when it's a missing entity, else 400.
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        msg = str(exc)
        status = 404 if "not found" in msg.lower() else 400
        return JSONResponse(status_code=status, content={"detail": msg})

    for r in (auth_api.router, funds_api.router, labels_api.router, labels_api.groups_router,
              expenses_api.router, budgets_api.router, analysis_api.router):
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

    @app.get("/whoami")
    def whoami(_: None = Depends(require_auth)) -> dict:
        return {"user": "owner"}

    return app


app = create_app()
