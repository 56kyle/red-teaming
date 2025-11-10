#!/bin/bash

# Quick start script for the red teaming harness

echo "=================================================="
echo "Atlas Red Teaming Harness - Quick Start"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env file"
        echo ""
        echo "⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY"
        echo ""
        read -p "Press Enter after you've added your API key to .env..."
    else
        echo "❌ .env.example not found. Please create .env manually."
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Run the orchestrator
echo "=================================================="
echo "Starting Red Teaming Campaign"
echo "=================================================="
echo ""

python attack_orchestrator.py

echo ""
echo "=================================================="
echo "Campaign Complete!"
echo "=================================================="
echo ""
echo "View results in:"
echo "  - results/ directory (JSON files)"
echo "  - reports/ directory (HTML reports)"
echo ""
echo "To generate a new report from results:"
echo "  python report_generator.py results/results_TIMESTAMP.json"
echo ""

