"""AI Engine microservice - exposes AIDiagnoser via HTTP API."""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

if TYPE_CHECKING:
    from ai_engine.diagnoser import AIDiagnoser

load_dotenv()

app = FastAPI(title="Lobster AI Engine", version="1.0.0")

# Module-level singleton – avoids repeated Ollama is_available() probes per request.
_diagnoser: AIDiagnoser | None = None


def _get_diagnoser() -> AIDiagnoser:
    """Return the shared AIDiagnoser singleton, creating it on first use."""
    global _diagnoser  # noqa: PLW0603 – intentional module-level singleton
    if _diagnoser is None:
        from ai_engine.diagnoser import AIDiagnoser  # noqa: PLC0415
        _diagnoser = AIDiagnoser()
    return _diagnoser


class DiagnoseRequest(BaseModel):
    """Request body for AI-powered pod diagnosis."""

    pod_name: str
    namespace: str
    describe: str
    logs: str
    error_type: str = "Unknown"


class DiagnoseResponse(BaseModel):
    """Response model for AI diagnosis results."""

    root_cause: str
    detailed_analysis: str | None = None
    remediation: str
    raw_analysis: str
    model_used: str


@app.get("/health")
async def health() -> dict[str, str]:
    """Return a simple health status for the AI Engine service."""
    return {"status": "ok"}


@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(req: DiagnoseRequest) -> DiagnoseResponse:
    """Run AI-powered pod diagnosis and return structured root cause analysis."""
    diagnoser = _get_diagnoser()
    result = diagnoser.diagnose({
        "pod_name": req.pod_name,
        "namespace": req.namespace,
        "describe": req.describe,
        "logs": req.logs,
        "error_type": req.error_type,
    })
    return DiagnoseResponse(
        root_cause=result.get("root_cause", ""),
        detailed_analysis=result.get("detailed_analysis") or None,
        remediation=result.get("remediation", ""),
        raw_analysis=result.get("raw_analysis", ""),
        model_used=result.get("model_used", "unknown"),
    )


class SuggestRequest(BaseModel):
    """Request body for a raw prompt suggestion."""

    prompt: str


class SuggestResponse(BaseModel):
    """Response model for raw prompt suggestions."""

    suggestion: str


@app.post("/suggest", response_model=SuggestResponse)
async def suggest(req: SuggestRequest) -> SuggestResponse:
    """Run a raw prompt through the AI provider and return the response text."""
    diagnoser = _get_diagnoser()
    return SuggestResponse(suggestion=diagnoser.suggest(req.prompt))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
