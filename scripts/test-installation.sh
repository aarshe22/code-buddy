#!/bin/bash

# Test Installation Script
# Verifies that all services are working correctly

echo "=========================================="
echo "Testing Code Buddy Installation"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_service() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Status: $response, Expected: $expected_status)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Check if services are running
echo "Checking if services are running..."
if ! docker compose ps | grep -q "Up"; then
    echo -e "${RED}Error: Services are not running. Start them with: docker compose up -d${NC}"
    exit 1
fi

echo ""
echo "Waiting for services to be ready..."
sleep 5

echo ""
echo "Running tests..."
echo ""

# Test 1: Nginx
test_service "Nginx" "http://localhost/health" "200"

# Test 2: API Gateway Health (via Nginx proxy)
test_service "API Gateway Health" "http://localhost/api/health" "200"

# Test 3: Rules Engine (via API Gateway)
test_service "Rules Engine (via Gateway)" "http://localhost/api/rules" "200"

# Test 4: API Gateway Health (checks all services)
# This endpoint checks the health of all internal services
test_service "All Services Health Check" "http://localhost/api/health" "200"

# Test 7: Ollama (direct - runs on host)
test_service "Ollama" "http://localhost:11434/api/tags" "200"

# Test 8: Code Server (direct - exposed on host)
# Get CODE_SERVER_PORT from .env if it exists
if [ -f ../.env ]; then
    export $(grep -v '^#' ../.env | grep CODE_SERVER_PORT | xargs) 2>/dev/null || true
fi
CODE_SERVER_PORT=${CODE_SERVER_PORT:-8080}
test_service "Code Server (direct)" "http://localhost:${CODE_SERVER_PORT}" "200"

# Test 9: API Gateway Rules Endpoint
test_service "API Gateway Rules" "http://localhost/api/rules" "200"

# Test 10: Ollama Models via API Gateway
test_service "Ollama Models (via Gateway)" "http://localhost/api/models" "200"

echo ""
echo "=========================================="
echo "Test Results"
echo "=========================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
else
    echo -e "${GREEN}Failed: $TESTS_FAILED${NC}"
fi
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! Installation is working correctly.${NC}"
    echo ""
    echo "You can now:"
    echo "  1. Open http://localhost in your browser"
    echo "  2. Login with your CODE_SERVER_PASSWORD"
    echo "  3. Start coding with AI assistance!"
    exit 0
else
    echo -e "${YELLOW}Some tests failed. Check the service logs:${NC}"
    echo "  docker compose logs"
    exit 1
fi

