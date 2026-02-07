#!/bin/bash
# Render Deployment Verification Script
# Tests all critical endpoints for production readiness

set -e  # Exit on any error

echo "========================================="
echo "🚀 Render Deployment Verification"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0

# Helper function
test_endpoint() {
    local name="$1"
    local cmd="$2"
    
    echo -n "Testing $name... "
    
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED+=1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED+=1))
    fi
}

echo "Step 1: Checking if server is available..."
# Kill any existing process on port 8000 to ensure fresh start
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
echo "Cleaned up port 8000"

if ! curl -s http://localhost:8000/ > /dev/null; then
    echo -e "${YELLOW}⚠️  Server not running. Starting server...${NC}"
    # python3 api_server.py &
    uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    SERVER_PID=$!
    sleep 5
    echo "Server started with PID: $SERVER_PID"
else
    echo -e "${GREEN}✓ Server is running${NC}"
fi

echo ""
echo "Step 2: Testing API Endpoints"
echo "-----------------------------------"

# Test health check
test_endpoint "Health Check" "curl -f -s http://localhost:8000/health"

# Test root endpoint
test_endpoint "Root Endpoint" "curl -f -s http://localhost:8000/"

# Test metrics
test_endpoint "Metrics Endpoint" "curl -f -s http://localhost:8000/metrics"

# Test monitoring/drift
test_endpoint "Drift Monitoring" "curl -f -s http://localhost:8000/monitoring/drift"

# Test monitoring/performance
test_endpoint "Performance Stats" "curl -f -s http://localhost:8000/monitoring/performance"

# Test Swagger docs
test_endpoint "API Documentation" "curl -f -s http://localhost:8000/docs"

echo ""
echo "Step 3: Testing Advisory Endpoint"
echo "-----------------------------------"

# Test valid request
echo -n "Testing valid advisory request... "
RESPONSE=$(curl -s -X POST http://localhost:8000/get-advisory \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_farmer",
    "gps_lat": 13.3409,
    "gps_long": 74.7421,
    "date": "2025-06-15"
  }')

if echo "$RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); sys.exit(0 if data.get('status') == 'success' else 1)"; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi

# Test invalid GPS
echo -n "Testing invalid GPS rejection... "
RESPONSE=$(curl -s -X POST http://localhost:8000/get-advisory \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_farmer",
    "gps_lat": 25.0,
    "gps_long": 74.7421,
    "date": "2025-06-15"
  }')

if echo "$RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); sys.exit(0 if 'detail' in data else 1)"; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi

echo ""
echo "Step 4: Checking Data Files"
echo "-----------------------------------"

FILES=(
    "models/final_rainfall_classifier_v1.pkl"
    "data/rainfall_daily_historical_v1.csv"
    "data/weather_drivers_daily_v1.csv"
    "data/taluk_boundaries.json"
    "data/feature_schema_v1.json"
)

for file in "${FILES[@]}"; do
    echo -n "Checking $file... "
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ EXISTS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ MISSING${NC}"
        ((FAILED++))
    fi
done

echo ""
echo "Step 5: Checking Configuration Files"
echo "-----------------------------------"

CONFIG_FILES=(
    "requirements.txt"
    "render.yaml"
    ".env.example"
    ".gitignore"
)

for file in "${CONFIG_FILES[@]}"; do
    echo -n "Checking $file... "
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ EXISTS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ MISSING${NC}"
        ((FAILED++))
    fi
done

echo ""
echo "========================================="
echo "📊 RESULTS"
echo "========================================="
echo -e "Tests Passed: ${GREEN}$PASSED${NC}"
echo -e "Tests Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}🚀 Ready for Render deployment!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Push to GitHub: git push origin main"
    echo "2. Connect to Render: https://render.com"
    echo "3. Deploy using render.yaml configuration"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo "Please fix the issues before deploying to Render"
    exit 1
fi
