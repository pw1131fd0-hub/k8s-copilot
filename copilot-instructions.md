# Lobster K8s Copilot Development Instructions

## Project Overview
You are developing "Lobster K8s Copilot", an AI-powered Kubernetes assistant.
- Backend: FastAPI (Python)
- K8s Logic: client-go (Go) - optional for now, sticking to Python's kubernetes-client if easier.
- Frontend: React + Tailwind

## Architecture Guidelines
- Follow the Clean Architecture pattern: Controller -> Service -> Repository.
- Use `pydantic` for data validation.
- Mask sensitive data (passwords, tokens) before sending anything to LLMs.
- All AI logic should reside in the `ai-engine/` directory.
- All API endpoints should be under `backend/`.

## Coding Standards
- Use Type Hints for all Python code.
- Write docstrings for all functions.
- Follow PEP 8 style guide.
- Ensure all Kubernetes interactions use the officially supported client.

## Workflow
- Run tests using `pytest`.
- Do not install heavyweight browser automation tools (like Playwright) unless explicitly required for the UI.
- Focus on the Core Logic (Diagnosis and YAML scanning) first.

## Goal
Achieve a functional MVP that can list pods, fetch logs/describe, and provide a basic AI-driven root cause analysis.
