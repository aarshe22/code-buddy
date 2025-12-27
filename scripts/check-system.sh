#!/bin/bash

# System Check Script for Dev Stack
# Verifies all prerequisites are met

echo "=========================================="
echo "Dev Stack System Check"
echo "=========================================="
echo ""

# Check Docker
echo -n "Checking Docker... "
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "✓ Found: $DOCKER_VERSION"
else
    echo "✗ Docker not found. Please install Docker."
    exit 1
fi

# Check Docker Compose
echo -n "Checking Docker Compose... "
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo "✓ Found: $COMPOSE_VERSION"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    echo "✓ Found: $COMPOSE_VERSION"
else
    echo "✗ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

# Check NVIDIA Docker
echo -n "Checking NVIDIA Docker runtime... "
if docker info 2>/dev/null | grep -q nvidia; then
    echo "✓ NVIDIA runtime detected"
    GPU_AVAILABLE=true
else
    echo "⚠ NVIDIA runtime not detected (GPU acceleration may not work)"
    GPU_AVAILABLE=false
fi

# Check GPU
if [ "$GPU_AVAILABLE" = true ]; then
    echo -n "Checking GPU... "
    if command -v nvidia-smi &> /dev/null; then
        GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1)
        echo "✓ $GPU_INFO"
    else
        echo "⚠ nvidia-smi not found"
    fi
fi

# Check disk space
echo -n "Checking disk space... "
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
echo "✓ Available: $AVAILABLE_SPACE"

# Check memory
echo -n "Checking system memory... "
TOTAL_MEM=$(free -h | awk '/^Mem:/ {print $2}')
echo "✓ Total: $TOTAL_MEM"

# Check .env file
echo -n "Checking .env file... "
if [ -f .env ]; then
    echo "✓ Found"
    
    # Check for required variables
    if grep -q "CODE_SERVER_PASSWORD" .env && ! grep -q "CODE_SERVER_PASSWORD=$" .env; then
        echo "  ✓ CODE_SERVER_PASSWORD is set"
    else
        echo "  ⚠ CODE_SERVER_PASSWORD not set or empty"
    fi
else
    echo "⚠ .env file not found. Run setup.sh first."
fi

# Check Docker daemon
echo -n "Checking Docker daemon... "
if docker info &> /dev/null; then
    echo "✓ Running"
else
    echo "✗ Docker daemon not running. Please start Docker."
    exit 1
fi

# Check ports
echo -n "Checking ports... "
PORTS=(80 8080 9000 11434 3001 3002 8000 8001)
ALL_CLEAR=true
for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠ Port $port is already in use"
        ALL_CLEAR=false
    fi
done
if [ "$ALL_CLEAR" = true ]; then
    echo "✓ All required ports are available"
fi

echo ""
echo "=========================================="
echo "System Check Complete"
echo "=========================================="
echo ""
echo "If all checks passed, you can run:"
echo "  docker-compose up -d"
echo ""

