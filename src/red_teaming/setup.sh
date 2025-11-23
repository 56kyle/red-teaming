#!/bin/bash
# Quick setup script for the browser automation framework

set -e

echo "=========================================="
echo "🌐 Atlas Browser Automation Setup"
echo "=========================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python3 --version || { echo "❌ Python 3 not found. Please install Python 3.9+"; exit 1; }

# Check if we're in the right directory
if [ ! -f "atlas_orchestrator.py" ]; then
    echo "❌ Please run this script from src/red_teaming/ directory"
    exit 1
fi

# Install dependencies
echo ""
echo "📦 Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt || {
        echo "⚠️  Some dependencies failed. Trying individual installs..."
        pip3 install playwright flask python-dotenv openai aiohttp tqdm jinja2
    }
else
    echo "❌ pip3 not found. Please install pip first."
    exit 1
fi

# Install Playwright browsers
echo ""
echo "🌐 Installing Playwright browsers..."
playwright install chromium || {
    echo "⚠️  Playwright install failed. You may need to run: python3 -m playwright install chromium"
}

# Check if .env exists
echo ""
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY"
else
    echo "✓ .env file already exists"
fi

# Create necessary directories
echo ""
echo "📁 Creating necessary directories..."
mkdir -p results/screenshots
mkdir -p results/videos
mkdir -p reports
mkdir -p test_pages

# Check if test pages exist
if [ ! -f "test_pages/indirect_injection.html" ]; then
    echo "⚠️  Test pages not found. Copying from tests/data/test_pages/..."
    if [ -d "../../tests/data/test_pages" ]; then
        cp ../../tests/data/test_pages/*.html test_pages/
        echo "✓ Test pages copied"
    else
        echo "⚠️  Test pages directory not found. You may need to create test pages manually."
    fi
fi

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your OPENAI_API_KEY"
echo "  2. (Optional) Set ATLAS_BROWSER_PATH if you have Atlas installed"
echo "  3. Run: python3 quick_test.py"
echo "  4. Then run: python3 atlas_orchestrator.py"
echo ""
echo "For more help, see GETTING_STARTED.md"
echo ""

