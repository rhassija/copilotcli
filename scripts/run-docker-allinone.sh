#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="copilot-companion:allinone"
CONTAINER_NAME="copilot-companion-allinone"
FRONTEND_PORT="3000"
BACKEND_PORT="8000"
GITHUB_TOKEN_VALUE="${GITHUB_TOKEN:-}"
API_BASE_URL=""
WS_URL=""

usage() {
  cat <<EOF
Run CoPilot Companion all-in-one Docker container.

Usage:
  scripts/run-docker-allinone.sh [options]

Options:
  --token <github_token>        GitHub token (optional if you login in UI)
  --image <image_name>          Docker image name (default: ${IMAGE_NAME})
  --name <container_name>       Container name (default: ${CONTAINER_NAME})
  --frontend-port <port>        Host port for UI (default: ${FRONTEND_PORT})
  --backend-port <port>         Host port for API (default: ${BACKEND_PORT})
  --api-base-url <url>          Override frontend API base URL (default: http://localhost:<backend-port>)
  --ws-url <url>                Override frontend WebSocket URL (default: ws://localhost:<backend-port>)
  -h, --help                    Show this help

Examples:
  scripts/run-docker-allinone.sh
  scripts/run-docker-allinone.sh --token ghp_xxx
  scripts/run-docker-allinone.sh --frontend-port 3300 --backend-port 8800
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --token)
      GITHUB_TOKEN_VALUE="${2:-}"
      shift 2
      ;;
    --image)
      IMAGE_NAME="${2:-}"
      shift 2
      ;;
    --name)
      CONTAINER_NAME="${2:-}"
      shift 2
      ;;
    --frontend-port)
      FRONTEND_PORT="${2:-}"
      shift 2
      ;;
    --backend-port)
      BACKEND_PORT="${2:-}"
      shift 2
      ;;
    --api-base-url)
      API_BASE_URL="${2:-}"
      shift 2
      ;;
    --ws-url)
      WS_URL="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${API_BASE_URL}" ]]; then
  API_BASE_URL="http://localhost:${BACKEND_PORT}"
fi

if [[ -z "${WS_URL}" ]]; then
  WS_URL="ws://localhost:${BACKEND_PORT}"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed or not available in PATH."
  exit 1
fi

if lsof -ti tcp:"${FRONTEND_PORT}" >/dev/null 2>&1; then
  echo "Port ${FRONTEND_PORT} is already in use."
  echo "Use --frontend-port <port> to choose another host port."
  exit 1
fi

if lsof -ti tcp:"${BACKEND_PORT}" >/dev/null 2>&1; then
  echo "Port ${BACKEND_PORT} is already in use."
  echo "Use --backend-port <port> to choose another host port."
  exit 1
fi

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Removing existing container ${CONTAINER_NAME}..."
  docker rm -f "${CONTAINER_NAME}" >/dev/null
fi

echo "Starting container ${CONTAINER_NAME} from image ${IMAGE_NAME}..."

# Create local data directory for persistence
mkdir -p "${PWD}/.docker-data"

docker run -d \
  --name "${CONTAINER_NAME}" \
  -p "${FRONTEND_PORT}:3000" \
  -p "${BACKEND_PORT}:8000" \
  -v "${PWD}/.docker-data:/app/backend/.data" \
  -e "GITHUB_TOKEN=${GITHUB_TOKEN_VALUE}" \
  -e "NEXT_PUBLIC_API_BASE_URL=${API_BASE_URL}" \
  -e "NEXT_PUBLIC_WS_URL=${WS_URL}" \
  -e "CORS_ORIGINS=http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}" \
  "${IMAGE_NAME}" >/dev/null

echo ""
echo "Container started successfully."
echo "UI:   http://localhost:${FRONTEND_PORT}"
echo "API:  http://localhost:${BACKEND_PORT}"
echo "Docs: http://localhost:${BACKEND_PORT}/docs"
echo "API Base URL used by frontend: ${API_BASE_URL}"
echo "WebSocket URL used by frontend: ${WS_URL}"
echo ""
echo "Useful commands:"
echo "  docker logs -f ${CONTAINER_NAME}"
echo "  docker stop ${CONTAINER_NAME}"
echo "  docker rm -f ${CONTAINER_NAME}"
