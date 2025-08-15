#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running health checks...${NC}"

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local name=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $name... "
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url"); then
        if [ "$response" -eq "$expected_status" ]; then
            echo -e "${GREEN}✓ OK (HTTP $response)${NC}"
            return 0
        else
            echo -e "${RED}✗ FAIL (HTTP $response)${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ FAIL (Connection error)${NC}"
        return 1
    fi
}

# Function to check database connection
check_database() {
    echo -n "Checking database connection... "
    
    if docker-compose exec -T analytics_db pg_isready -U analytics -d analytics > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

# Function to check Redis connection
check_redis() {
    echo -n "Checking Redis connection... "
    
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

# Health check results
failed_checks=0

# Check core services
check_endpoint "http://localhost:8080/health" "Analytics API" || ((failed_checks++))
check_endpoint "http://localhost:3001/api/health" "Grafana" || ((failed_checks++))
check_endpoint "http://localhost:9090/-/healthy" "Prometheus" || ((failed_checks++))
check_endpoint "http://localhost:16686/" "Jaeger UI" || ((failed_checks++))
check_endpoint "http://localhost:3100/ready" "Loki" || ((failed_checks++))

# Check databases
check_database || ((failed_checks++))
check_redis || ((failed_checks++))

# Check API endpoints
check_endpoint "http://localhost:8080/api/analytics/data" "Analytics Data API" || ((failed_checks++))
check_endpoint "http://localhost:8080/api/performance/report" "Performance API" || ((failed_checks++))
check_endpoint "http://localhost:8080/api/feedback/analysis" "Feedback API" || ((failed_checks++))
check_endpoint "http://localhost:8080/api/ab-testing/tests/active" "A/B Testing API" || ((failed_checks++))

# Check metrics endpoints
check_endpoint "http://localhost:8080/metrics" "Analytics Metrics" || ((failed_checks++))
check_endpoint "http://localhost:9090/metrics" "Prometheus Metrics" || ((failed_checks++))

# Summary
echo ""
if [ $failed_checks -eq 0 ]; then
    echo -e "${GREEN}All health checks passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}$failed_checks health check(s) failed! ✗${NC}"
    echo -e "${YELLOW}Check the logs for more details:${NC}"
    echo "  docker-compose logs analytics"
    echo "  docker-compose logs grafana"
    echo "  docker-compose logs prometheus"
    exit 1
fi