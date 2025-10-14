#!/bin/bash
set -euo pipefail

# Install dependencies for the GitHub Action
# This script installs uv and the runtime dependencies needed for the action

echo "🚀 Installing dependencies..."

# Install uv for fast dependency management
echo "Installing uv package manager..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Install only runtime dependencies for the action
echo "Installing runtime dependencies..."
uv pip install --system -e ".[runtime]"

echo "✅ Dependencies installed successfully!"
