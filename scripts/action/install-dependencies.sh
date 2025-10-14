#!/bin/bash
set -euo pipefail

# Install dependencies for the GitHub Action
# This script installs uv and the runtime dependencies needed for the action

echo "🚀 Installing dependencies..."

# Install uv for fast dependency management
echo "Installing uv package manager..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Get the action directory path (where this script is located)
ACTION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "Action directory: $ACTION_DIR"

# Install only runtime dependencies for the action
echo "Installing runtime dependencies..."

# Check if we're in a virtual environment or need --system flag
if [[ -n "${VIRTUAL_ENV:-}" ]] || [[ -n "${CONDA_DEFAULT_ENV:-}" ]]; then
    echo "Virtual environment detected, installing without --system"
    uv pip install -e "$ACTION_DIR[runtime]"
else
    echo "No virtual environment detected (GitHub Actions), using --system"
    uv pip install --system --python "$(which python)" -e "$ACTION_DIR[runtime]"
fi

echo "✅ Dependencies installed successfully!"
