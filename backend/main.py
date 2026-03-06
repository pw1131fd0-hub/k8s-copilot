"""FastAPI application entry point for Lobster K8s Copilot backend."""
import logging
import os
import pathlib
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from kubernetes import client, config

from backend.database import init_db
from backend.api.v1.router import router as v1_router

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        if os.getenv('KUBERNETES_SERVICE_HOST'):
            config.load_incluster_config()
        else:
            config.load_kube_config()
    except Exception as e:
        logger.warning('Could not load K8s config: %s', e)
    yield


app = FastAPI(title='Lobster K8s Copilot API', version='1.0.0', lifespan=lifespan)

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
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(v1_router, prefix="/api/v1")

# Serve frontend build if available (single-binary / K8s single-pod mode).
# The build directory is resolved relative to the project root so it works
# both in local dev (frontend/build/) and inside a container image where the
# build artefacts are copied alongside the backend.
_FRONTEND_BUILD = pathlib.Path(
    os.getenv("FRONTEND_BUILD_DIR", str(pathlib.Path(__file__).parent.parent / "frontend" / "build"))
)
if _FRONTEND_BUILD.is_dir():
    _STATIC_DIR = _FRONTEND_BUILD / "static"
    if _STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/")
async def root():
    """Return API health check and version information."""
    return {"message": "Lobster K8s Copilot API is running", "version": "1.0.0"}


@app.get("/api/v1/cluster/status")
async def get_cluster_status(request: Request):
    """Return whether the backend can reach the Kubernetes API server."""
    try:
        v1 = client.CoreV1Api()
        v1.list_namespace(limit=1, _request_timeout=10)
        return {"status": "connected"}
    except Exception as e:
        logger.debug("K8s cluster unreachable: %s", e)
        return {"status": "disconnected"}


@app.get("/{full_path:path}")
async def spa_catch_all(full_path: str):
    """Forward all non-API, non-static routes to the React SPA index.html."""
    if full_path.startswith("api/") or full_path.startswith("static/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    index_html = _FRONTEND_BUILD / "index.html"
    if index_html.is_file():
        return FileResponse(str(index_html))
    from fastapi import HTTPException
    raise HTTPException(status_code=404)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
