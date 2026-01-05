#!/bin/bash
# Install macOS dependencies using Homebrew

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🍎 Installing macOS Dependencies${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}⚠️  Homebrew is not installed${NC}"
    echo ""
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo ""
fi

echo -e "${GREEN}✅ Homebrew detected${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Installing Python 3.11...${NC}"
    brew install python@3.11
else
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python already installed: ${PYTHON_VERSION}${NC}"
fi

# Check Docker (optional)
if ! command -v docker &> /dev/null; then
    echo ""
    echo -e "${YELLOW}Docker is not installed${NC}"
    echo "   Install Docker Desktop for macOS:"
    echo "   https://www.docker.com/products/docker-desktop"
else
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✅ Docker already installed: ${DOCKER_VERSION}${NC}"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Dependencies check completed${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

