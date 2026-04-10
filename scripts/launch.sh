#!/usr/bin/env bash
# =============================================================================
# News Agent Collector — Boot script
# Runs on macOS login via launchd (com.newsagent.plist).
#
# Security properties:
#   - set -euo pipefail: any error aborts immediately
#   - Zero secrets in this file — .env is read by the FastAPI app, not here
#   - No source of .env needed: uvicorn loads it via pydantic-settings on start
#   - Script lives in ~/Library/Scripts/ (not ~/Desktop) to avoid macOS TCC
#   - PROJECT_DIR injected by plist EnvironmentVariables (a path, not a secret)
#   - Absolute paths: UVICORN_BIN is from project .venv, not system PATH
#   - No sudo, no privileged operations
#   - Executable by owner only: chmod 700
# =============================================================================
set -euo pipefail

# ── 1. Determine project root ─────────────────────────────────────────────────
#    PROJECT_DIR is injected by the plist's EnvironmentVariables block.
#    Falls back to BASH_SOURCE derivation for local manual runs.
if [[ -z "${PROJECT_DIR:-}" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
fi
LOG_DIR="${HOME}/Library/Logs/NewsAgent"
UVICORN_LOG="${LOG_DIR}/uvicorn.log"
UVICORN_PID_FILE="${LOG_DIR}/uvicorn.pid"
APP_HOST="127.0.0.1"
APP_PORT="8000"
UVICORN_BIN="${PROJECT_DIR}/.venv/bin/uvicorn"
CURL_BIN="/usr/bin/curl"
# launchd runs with a minimal PATH — hardcode well-known docker locations
DOCKER_BIN="/usr/local/bin/docker"
if [[ ! -x "${DOCKER_BIN}" ]]; then
    DOCKER_BIN="/opt/homebrew/bin/docker"
fi

# ── 2. Validate required binaries ────────────────────────────────────────────
if [[ ! -x "${UVICORN_BIN}" ]]; then
    echo "[NewsAgent] ERROR: uvicorn not found at ${UVICORN_BIN}" >&2
    echo "[NewsAgent] Run: cd ${PROJECT_DIR} && uv sync" >&2
    exit 1
fi

if [[ ! -x "${DOCKER_BIN}" ]]; then
    echo "[NewsAgent] ERROR: docker not found at ${DOCKER_BIN}" >&2
    echo "[NewsAgent] Is Docker Desktop installed?" >&2
    exit 1
fi

# ── 5. Ensure log directory exists ───────────────────────────────────────────
mkdir -p "${LOG_DIR}"

# ── 6. Wait for Docker daemon (Docker Desktop may still be starting) ─────────
echo "[NewsAgent] Waiting for Docker daemon..." >&2
docker_ready=0
for i in $(seq 1 30); do
    if "${DOCKER_BIN}" info > /dev/null 2>&1; then
        docker_ready=1
        break
    fi
    sleep 2
done
if [[ "${docker_ready}" -eq 0 ]]; then
    echo "[NewsAgent] ERROR: Docker daemon not ready after 60s" >&2
    exit 1
fi

# ── 7. Start docker compose (idempotent — 'up -d' is safe to re-run) ─────────
#    Use absolute path to compose file; pass --project-directory to avoid
#    docker trying to resolve relative paths from the Desktop.
echo "[NewsAgent] Starting docker compose..." >&2
"${DOCKER_BIN}" compose \
    --project-directory "${PROJECT_DIR}" \
    -f "${PROJECT_DIR}/docker-compose.yml" \
    up -d

# ── 8. Wait for Postgres to accept connections ────────────────────────────────
#    Use 'docker exec' with the explicit container name — avoids reading
#    docker-compose.yml again (which would require Desktop TCC access).
echo "[NewsAgent] Waiting for Postgres..." >&2
pg_ready=0
for i in $(seq 1 30); do
    if "${DOCKER_BIN}" exec news_agent_postgres \
           pg_isready -U postgres > /dev/null 2>&1; then
        pg_ready=1
        break
    fi
    sleep 2
done
if [[ "${pg_ready}" -eq 0 ]]; then
    echo "[NewsAgent] ERROR: Postgres not ready after 60s" >&2
    exit 1
fi

# ── 9. Kill any stale uvicorn process on the target port ─────────────────────
stale_pid="$(lsof -t -i TCP:"${APP_PORT}" 2>/dev/null | head -1 || true)"
if [[ -n "${stale_pid}" ]]; then
    echo "[NewsAgent] Killing stale process on port ${APP_PORT} (pid ${stale_pid})" >&2
    kill "${stale_pid}" 2>/dev/null || true
    sleep 1
fi

# ── 10. Start uvicorn in background ──────────────────────────────────────────
#    nohup + disown detaches uvicorn from the launchd session so it keeps
#    running after this script exits (launchd would otherwise kill the
#    process group when the parent script completes).
echo "[NewsAgent] Starting uvicorn..." >&2
cd "${PROJECT_DIR}"
nohup "${UVICORN_BIN}" src.app.main:app \
    --host "${APP_HOST}" \
    --port "${APP_PORT}" \
    --workers 1 \
    >> "${UVICORN_LOG}" 2>&1 &
UVICORN_PID=$!
disown "${UVICORN_PID}"
echo "${UVICORN_PID}" > "${UVICORN_PID_FILE}"

# ── 11. Wait for the app to be healthy ───────────────────────────────────────
echo "[NewsAgent] Waiting for app health check..." >&2
app_ready=0
for i in $(seq 1 30); do
    if "${CURL_BIN}" -sf "http://${APP_HOST}:${APP_PORT}/api/v1/health" > /dev/null 2>&1; then
        app_ready=1
        break
    fi
    sleep 2
done
if [[ "${app_ready}" -eq 0 ]]; then
    echo "[NewsAgent] ERROR: App not healthy after 60s — check ${UVICORN_LOG}" >&2
    exit 1
fi

# ── 12. Trigger delivery (idempotent — skips if already sent today) ───────────
echo "[NewsAgent] Triggering digest delivery..." >&2
delivery_response="$("${CURL_BIN}" -sf -X POST \
    "http://${APP_HOST}:${APP_PORT}/api/v1/deliver" \
    -H 'Content-Type: application/json' 2>&1 || true)"
echo "[NewsAgent] Delivery response: ${delivery_response}" >&2

# ── 13. Shut down uvicorn after a successful or idempotent delivery ───────────
#    On delivery error, leave uvicorn running so the problem can be debugged
#    via the browser UI or a manual curl.
case "${delivery_response}" in
    *'"status":"sent"'*|*'"status":"skipped"'*)
        echo "[NewsAgent] Delivery complete — shutting down uvicorn..." >&2
        uvicorn_pid="$(cat "${UVICORN_PID_FILE}" 2>/dev/null || true)"
        if [[ -n "${uvicorn_pid}" ]]; then
            kill "${uvicorn_pid}" 2>/dev/null || true
            # Wait up to 10s for graceful exit, then force-kill
            for i in $(seq 1 10); do
                kill -0 "${uvicorn_pid}" 2>/dev/null || break
                sleep 1
            done
            kill -9 "${uvicorn_pid}" 2>/dev/null || true
        fi
        echo "[NewsAgent] Uvicorn stopped." >&2
        ;;
    *)
        echo "[NewsAgent] Delivery failed — uvicorn left running for debugging." >&2
        ;;
esac

echo "[NewsAgent] Boot complete." >&2
