#!/bin/bash
# macOS-specific setup script for OpenSkill Skill Host

set -e  # Exit on error

echo "🍎 macOS Setup for OpenSkill Skill Host"
echo "========================================"
echo ""

# Check if running on macOS
if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "⚠️  Warning: This script is designed for macOS"
    echo "   Detected OS: $(uname -s)"
    echo "   You may want to use setup.sh instead"
    echo ""
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed"
    echo ""
    echo "💡 Install Python using Homebrew:"
    echo "   brew install python@3.11"
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "📌 Python version: $PYTHON_VERSION"

# Check if Python version is 3.10+
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "❌ Error: Python 3.10+ is required (found $PYTHON_VERSION)"
    echo ""
    echo "💡 Upgrade Python using Homebrew:"
    echo "   brew install python@3.11"
    echo ""
    exit 1
fi

# Check for Homebrew (optional, but recommended)
if command -v brew &> /dev/null; then
    echo "✅ Homebrew detected"
    BREW_PREFIX=$(brew --prefix)
    echo "   Homebrew prefix: $BREW_PREFIX"
else
    echo "ℹ️  Homebrew not detected (optional)"
    echo "   Install Homebrew: https://brew.sh"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo ""
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Next Steps:"
echo ""
echo "1. Activate the virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Start the Skill Host:"
echo "   ./scripts/start-macos.sh"
echo ""
echo "   Or manually:"
echo "   uvicorn src.app:app --host 127.0.0.1 --port 8000"
echo ""
echo "3. Open in browser (macOS):"
echo "   open http://127.0.0.1:8000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

