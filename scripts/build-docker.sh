#!/bin/bash
# Build Docker image for OpenSkill Skill Host

set -e

IMAGE_NAME=${IMAGE_NAME:-"openskill-host"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
DOCKERFILE=${DOCKERFILE:-"Dockerfile"}

echo "🐳 Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"

# Build the image
docker build \
    -f "${DOCKERFILE}" \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    .

echo ""
echo "✅ Docker image built successfully!"
echo ""
echo "To run the container:"
echo "  docker run -p 8000:8000 ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "Or use docker-compose:"
echo "  docker-compose up -d"
echo ""

