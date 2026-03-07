# ---- Builder stage ----
FROM python:3.12-slim AS builder

WORKDIR /build

COPY ai-engine/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime stage ----
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy ai-engine code (accessible as both ai_engine and ai-engine)
COPY ai-engine/ ./ai_engine/
COPY ai-engine/main.py ./main.py

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
