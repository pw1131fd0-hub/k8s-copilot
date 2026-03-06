"""AI Engine microservice - exposes AIDiagnoser via HTTP API."""
import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Lobster AI Engine", version="1.0.0")


class DiagnoseRequest(BaseModel):
    pod_name: str
    namespace: str
    describe: str
    logs: str
    error_type: str = "Unknown"


class DiagnoseResponse(BaseModel):
    root_cause: str
    remediation: str
    raw_analysis: str
    model_used: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(req: DiagnoseRequest):
    from ai_engine.diagnoser import AIDiagnoser
    diagnoser = AIDiagnoser()
    result = diagnoser.diagnose({
        "pod_name": req.pod_name,
        "namespace": req.namespace,
        "describe": req.describe,
        "logs": req.logs,
        "error_type": req.error_type,
    })
    return DiagnoseResponse(
        root_cause=result.get("root_cause", ""),
        remediation=result.get("remediation", ""),
        raw_analysis=result.get("raw_analysis", ""),
        model_used=result.get("model_used", "unknown"),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
