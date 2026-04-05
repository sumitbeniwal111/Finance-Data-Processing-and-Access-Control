from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, dashboard, records, users
from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.frontend.routes import router as frontend_router
from app.services.user_service import ensure_bootstrap_admin, seed_demo_users

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with SessionLocal() as db:
        bootstrap_result = ensure_bootstrap_admin(db)
        if settings.auto_seed_demo_data:
            seed_demo_users(db)
    if bootstrap_result:
        user, token = bootstrap_result
        print(
            f"Bootstrap admin created: email={user.email}, role={user.role.value}, token={token}"
        )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "Backend assignment for finance data processing, access control, "
            "record management, and dashboard analytics."
        ),
        lifespan=lifespan,
    )

    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=jsonable_encoder({"detail": exc.errors()}),
        )

    @app.get("/", tags=["Health"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")
    app.include_router(frontend_router)
    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(users.router, prefix=settings.api_prefix)
    app.include_router(records.router, prefix=settings.api_prefix)
    app.include_router(dashboard.router, prefix=settings.api_prefix)
    return app


app = create_app()
