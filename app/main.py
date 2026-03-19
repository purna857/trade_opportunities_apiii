from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.core.auth import AuthContext, get_auth_context
from app.core.rate_limit import enforce_rate_limit
from app.core.store import store
from app.models import AnalyzeRequestPath
from app.services.analysis import AnalysisService
from app.services.search import MarketSearchService

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Analyzes Indian sector-level market news and produces a markdown report with trade opportunities. "
        "Use the `X-API-Key` header for authenticated access, or enable guest mode for local demos."
    ),
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    max_age=settings.session_max_age_seconds,
    same_site="lax",
    https_only=settings.environment == "production",
)

search_service = MarketSearchService()
analysis_service = AnalysisService()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Invalid request input",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "Something went wrong while processing the request.",
        },
    )


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "gemini_configured": bool(settings.gemini_api_key),
        "guest_access_enabled": settings.guest_access_enabled,
    }


@app.get(
    "/analyze/{sector}",
    tags=["analysis"],
    summary="Analyze an Indian market sector and return a markdown report",
    response_class=PlainTextResponse,
)
async def analyze_sector(
    sector: str,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
) -> PlainTextResponse:
    validated = AnalyzeRequestPath(sector=sector)
    await enforce_rate_limit(auth)

    try:
        search_result = await search_service.collect_sector_news(validated.sector)
    except Exception as exc:
        logger.exception("Search failure for sector=%s: %s", validated.sector, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to collect market data from external sources at the moment.",
        ) from exc

    report = await analysis_service.generate_markdown_report(validated.sector, search_result)

    usage = store.record_session_hit(auth.session_id, validated.sector, auth.user_type)
    request.session["last_usage"] = usage
    request.session["last_requested_at"] = datetime.now(timezone.utc).isoformat()

    return PlainTextResponse(
        content=report,
        media_type="text/markdown",
        headers={
            "X-Session-Id": auth.session_id,
            "X-RateLimit-Limit": str(settings.rate_limit_requests),
            "X-RateLimit-Window": str(settings.rate_limit_window_seconds),
        },
    )
