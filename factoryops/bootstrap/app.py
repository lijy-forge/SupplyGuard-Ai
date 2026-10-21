"""Independent FactoryOps FastAPI application.

This module intentionally imports none of the Ray/city simulation runtime.
"""

import os

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from factoryops import __version__
from factoryops.api.v1 import router
from factoryops.domain.exceptions import ConflictError, DomainRuleViolation, FactoryOpsError, NotFoundError
from factoryops.infrastructure.db.base import Base
from factoryops.infrastructure.db.session import (
    DEFAULT_DATABASE_URL,
    create_database_engine,
    create_session_factory,
)
from factoryops.infrastructure.db.uow import SqlAlchemyUnitOfWork


def error_payload(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def create_app(
    database_url: str | None = None,
    *,
    initialize_schema: bool = False,
) -> FastAPI:
    resolved_url = database_url or os.getenv("FACTORYOPS_DATABASE_URL", DEFAULT_DATABASE_URL)
    engine = create_database_engine(resolved_url)
    session_factory = create_session_factory(engine)

    app = FastAPI(
        title="SupplyGuard AI Business API",
        version=__version__,
        description="Manufacturing quality and supply-chain business services (no LLM).",
    )
    app.state.engine = engine
    app.state.uow_factory = lambda: SqlAlchemyUnitOfWork(session_factory)

    if initialize_schema:
        # Test/bootstrap convenience only. Production startup uses Alembic.
        Base.metadata.create_all(engine)

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_payload(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=error_payload(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(DomainRuleViolation)
    async def domain_handler(request: Request, exc: DomainRuleViolation):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=error_payload(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=error_payload(
                "VALIDATION_ERROR",
                "Request validation failed",
                {"errors": jsonable_encoder(exc.errors())},
            ),
        )

    @app.exception_handler(FactoryOpsError)
    async def factoryops_handler(request: Request, exc: FactoryOpsError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_payload(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(Exception)
    async def internal_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_payload(
                "INTERNAL_ERROR",
                "An unexpected internal error occurred",
            ),
        )

    app.include_router(router)
    return app


app = create_app()
