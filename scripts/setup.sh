#!/bin/bash

# Honeypot API Setup Script
# This script helps you set up the honeypot API quickly and correctly

set -e  # Exit on error

echo "🚀 Honeypot API Setup Script"
echo "=============================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install pip first."
    exit 1
fi
echo "✓ pip3 is available"
echo ""

# Create virtual environment (recommended)
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate 2>/dev/null || echo "Note: Manual activation may be needed"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed successfully"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit the .env file and add your API keys:"
    echo "   - ANTHROPIC_API_KEY: Get from https://console.anthropic.com"
    echo "   - HONEYPOT_API_KEY: Create your own secret key"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Check if API keys are set
echo "🔐 Checking API keys..."
if grep -q "your-anthropic-api-key-here" .env 2>/dev/null; then
    echo "⚠️  WARNING: Please set your ANTHROPIC_API_KEY in .env file"
    echo "   Get your API key from: https://console.anthropic.com"
fi

if grep -q "your-secret-api-key-here" .env 2>/dev/null; then
    echo "⚠️  WARNING: Please set your HONEYPOT_API_KEY in .env file"
    echo "   Choose a strong random string"
fi
echo ""

# Success message
echo "✅ Setup completed successfully!"
echo ""
echo "📚 Next Steps:"
echo "   1. Edit .env file with your API keys"
echo "   2. Run: python app.py"
echo "   3. Test: python test_api.py"
echo ""
echo "💡 Quick Commands:"
echo "   • Start server: python app.py"
echo "   • Run tests: python test_api.py"
echo "   • Check health: curl http://localhost:5000/health"
echo ""
echo "📖 For more information, see README.md or QUICKSTART.md"
echo ""
