"""FastAPI application entry point for ClawBook - AI Diary System."""
import logging
import os
import pathlib
import secrets
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from kubernetes import client, config
import socketio

from backend.database import init_db
from backend.api.v1.router import router as v1_router
from backend.websocket.manager import WebSocketManager
from backend.websocket.namespaces import create_collaboration_namespace
from backend.websocket import handlers as ws_handlers

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Optional API key authentication middleware (enabled via LOBSTER_API_KEY env var)."""

    EXCLUDED_PATHS = {"/", "/docs", "/redoc", "/openapi.json"}

    def __init__(self, app, api_key: str | None):
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self._api_key:
            return await call_next(request)
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        if request.method == "OPTIONS":
            return await call_next(request)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if secrets.compare_digest(token, self._api_key):
                return await call_next(request)
        api_key_header = request.headers.get("X-API-Key", "")
        if api_key_header and secrets.compare_digest(api_key_header, self._api_key):
            return await call_next(request)
        return Response(
            content='{"detail":"Invalid or missing API key"}',
            status_code=401,
            media_type="application/json",
        )

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise the database and load Kubernetes configuration on application startup."""
    init_db()
    try:
        if os.getenv('KUBERNETES_SERVICE_HOST'):
            config.load_incluster_config()
        else:
            config.load_kube_config()
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning('Could not load K8s config: %s', e)
    yield


# Initialize WebSocket Manager
ws_manager = WebSocketManager()

# Create Socket.IO instance
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    ping_interval=25,
    ping_timeout=60,
    max_http_buffer_size=1e6,
    logger=logger,
    engineio_logger=logging.getLogger('engineio')
)

app = FastAPI(title='ClawBook - AI Diary System', version='1.6.0', lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
_allow_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()] if _raw_origins else []
_is_wildcard = not _allow_origins

if _is_wildcard:
    logger.warning(
        "ALLOWED_ORIGINS is not set — CORS is restricted to same-origin only. "
        "Set ALLOWED_ORIGINS to a comma-separated list of trusted origins for cross-origin access."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins if not _is_wildcard else [],
    allow_credentials=not _is_wildcard,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add optional API key authentication (enabled via LOBSTER_API_KEY env var)
_api_key = os.getenv("LOBSTER_API_KEY")
if _api_key:
    logger.info("API key authentication is ENABLED")
    app.add_middleware(APIKeyAuthMiddleware, api_key=_api_key)
else:
    logger.warning(
        "LOBSTER_API_KEY is not set — API endpoints are publicly accessible. "
        "Set LOBSTER_API_KEY to enable authentication."
    )

# Register Socket.IO namespace
create_collaboration_namespace(sio, ws_manager)

# Set Socket.IO instance in handlers for REST API to use
ws_handlers.set_sio_instance(sio)

# Mount Socket.IO ASGI app
app.mount("/socket.io", socketio.ASGIApp(sio))

# Include API routers
app.include_router(v1_router, prefix="/api/v1")

# Serve frontend build if available (single-binary / K8s single-pod mode).
# The build directory is resolved relative to the project root so it works
# both in local dev (frontend/build/) and inside a container image where the
# build artefacts are copied alongside the backend.
_FRONTEND_BUILD = pathlib.Path(
    os.getenv(
        "FRONTEND_BUILD_DIR",
        str(pathlib.Path(__file__).parent.parent / "frontend" / "build"),
    )
)
if _FRONTEND_BUILD.is_dir():
    _STATIC_DIR = _FRONTEND_BUILD / "static"
    if _STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/")
async def root() -> dict[str, str]:
    """Return API health check and version information."""
    return {"message": "Lobster K8s Copilot API is running", "version": "1.0.0"}


@app.get("/api/v1/cluster/status")
async def get_cluster_status() -> dict[str, str | None]:
    """Return whether the backend can reach the Kubernetes API server."""
    try:
        v1 = client.CoreV1Api()
        v1.list_namespace(limit=1, _request_timeout=10)
        # Get K8s server version
        version_api = client.VersionApi()
        version_info = version_api.get_code(_request_timeout=5)
        version = version_info.git_version if version_info else None
        return {"status": "connected", "version": version, "message": None}
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.debug("K8s cluster unreachable: %s", e)
        # Security: Don't expose detailed K8s error info to clients
        return {"status": "disconnected", "version": None, "message": "Unable to connect to Kubernetes cluster"}


@app.get("/{full_path:path}")
async def spa_catch_all(full_path: str) -> FileResponse:
    """Forward all non-API, non-static routes to the React SPA index.html."""
    # Security: Reject path traversal attempts
    if ".." in full_path or full_path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid path")
    # Security: Normalize and decode URL-encoded variants
    normalized = pathlib.Path(full_path).as_posix()
    if normalized.startswith("api/") or normalized.startswith("static/"):
        raise HTTPException(status_code=404)
    index_html = _FRONTEND_BUILD / "index.html"
    if index_html.is_file():
        return FileResponse(str(index_html))
    raise HTTPException(status_code=404)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
