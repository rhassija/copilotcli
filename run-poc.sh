#!/bin/bash

# Copilot SDLC POC - Run Script
# Activates copilotcompanion environment and starts Streamlit app

set -e

echo "🚀 Starting Copilot SDLC POC (001-spec-generator)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"

# Check if pyenv is available
if ! command -v pyenv &> /dev/null; then
    echo "❌ Error: pyenv not found. Please install pyenv first."
    exit 1
fi

# Activate copilotcompanion environment
echo "📦 Activating copilotcompanion environment..."
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

if ! pyenv shell copilotcompanion 2>/dev/null; then
    echo "❌ Error: copilotcompanion environment not found"
    echo "   Available versions:"
    pyenv versions
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version)
echo "✅ Using Python: $PYTHON_VERSION"

# Verify Streamlit is installed
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📥 Installing Streamlit in copilotcompanion..."
    pip install -q streamlit>=1.28.0
fi

# Check spec.md exists
SPEC_FILE="$REPO_ROOT/specs/001-spec-generator/spec.md"
if [ ! -f "$SPEC_FILE" ]; then
    echo "⚠️  Warning: Specification file not found at $SPEC_FILE"
    echo "   The specification should exist. Try running /speckit.specify first."
fi

echo ""
echo "🌐 Starting Streamlit app..."
echo "   URL: http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start Streamlit app
cd "$REPO_ROOT"
streamlit run src/ui/app.py
