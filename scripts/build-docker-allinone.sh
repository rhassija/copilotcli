#!/bin/bash

# Build script for the Copilot Companion all-in-one Docker image
# Usage: ./build-docker-allinone.sh [--no-cache]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

IMAGE_NAME="copilot-companion:allinone"
DOCKERFILE="Dockerfile.allinone"

# Parse arguments
NO_CACHE=""
if [[ "$1" == "--no-cache" ]]; then
  NO_CACHE="--no-cache"
  echo "Building without cache..."
fi

# Navigate to project root
cd "$PROJECT_ROOT"

echo "Building Docker image: ${IMAGE_NAME}"
echo "From Dockerfile: ${DOCKERFILE}"
echo "Project root: ${PROJECT_ROOT}"
echo ""

# Build the image
docker build ${NO_CACHE} -t "${IMAGE_NAME}" -f "${DOCKERFILE}" .

echo ""
echo "✅ Build complete!"
echo ""
echo "Image: ${IMAGE_NAME}"
echo ""
echo "To run the container:"
echo "  cd scripts && ./run-docker-allinone.sh"
echo ""
echo "To rebuild without cache:"
echo "  ./build-docker-allinone.sh --no-cache"
