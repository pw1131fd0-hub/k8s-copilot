#!/bin/sh
# Smoke test script — verifies all services respond correctly after startup.
# Usage: ./scripts/smoke_test.sh [BASE_URL]
# Can also be run via docker-compose --profile smoke-test up smoke-test
set -e

BACKEND_URL="${BACKEND_URL:-http://backend:8000}"
AI_ENGINE_URL="${AI_ENGINE_URL:-http://ai-engine:8001}"
FRONTEND_URL="${FRONTEND_URL:-http://frontend:80}"

PASS=0
FAIL=0

check() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"

    actual=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")
    if [ "$actual" = "$expected_status" ]; then
        echo "  ✓  $name  ($url)  → HTTP $actual"
        PASS=$((PASS + 1))
    else
        echo "  ✗  $name  ($url)  → HTTP $actual (expected $expected_status)"
        FAIL=$((FAIL + 1))
    fi
}

echo ""
echo "════════════════════════════════════════"
echo "  Lobster K8s Copilot — Smoke Tests"
echo "════════════════════════════════════════"
echo ""

echo "▶ Backend (FastAPI)"
check "Root health"              "$BACKEND_URL/"
check "Cluster status"           "$BACKEND_URL/api/v1/cluster/status"

echo ""
echo "▶ AI Engine"
check "AI Engine health"         "$AI_ENGINE_URL/health"

echo ""
echo "▶ Frontend (Nginx)"
check "Frontend index"           "$FRONTEND_URL/"

echo ""
echo "════════════════════════════════════════"
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "════════════════════════════════════════"
echo ""

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
