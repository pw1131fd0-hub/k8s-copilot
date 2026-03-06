import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from kubernetes import client, config

from backend.database import init_db
from backend.api.v1.router import router as v1_router

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
        print(f'Warning: Could not load K8s config: {e}')
    yield


app = FastAPI(title='Lobster K8s Copilot API', version='1.0.0', lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Lobster K8s Copilot API is running", "version": "1.0.0"}


@app.get("/api/v1/cluster/status")
async def get_cluster_status(request: Request):
    try:
        v1 = client.CoreV1Api()
        v1.list_namespace(limit=1)
        return {"status": "connected"}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
