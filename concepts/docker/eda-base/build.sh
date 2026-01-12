#!/bin/bash
# Build script for Silicon Arena EDA Docker image
# Task ID: silicon-arena-6g7.3

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="silicon-arena/eda-base"
IMAGE_TAG="${1:-latest}"

echo "=== Building Silicon Arena EDA Base Image ==="
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Context: ${SCRIPT_DIR}"

# Build the image
docker build \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    -f "${SCRIPT_DIR}/Dockerfile" \
    "${SCRIPT_DIR}"

echo ""
echo "=== Build Complete ==="
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"

# Show image size
docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "Size: {{.Size}}"

# Verify tools
echo ""
echo "=== Verifying Tools ==="
docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" bash -c '
    echo "Verilator: $(verilator --version 2>&1 | head -1)"
    echo "Yosys: $(yosys --version 2>&1 | head -1)"
    echo "SymbiYosys: $(sby --version 2>&1 | head -1 || echo "installed")"
    echo "Python: $(python3 --version)"
    python3 -c "import cocotb; print(f\"Cocotb: {cocotb.__version__}\")"
'

echo ""
echo "=== To run interactively ==="
echo "docker run -it --rm -v \$(pwd):/workspace ${IMAGE_NAME}:${IMAGE_TAG}"
