#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"

echo -e "${GREEN}Starting deployment for ${ENVIRONMENT} environment...${NC}"

# Check if required files exist
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Error: $COMPOSE_FILE not found${NC}"
    exit 1
fi

if [ ! -f ".env.${ENVIRONMENT}" ]; then
    echo -e "${RED}Error: .env.${ENVIRONMENT} not found${NC}"
    exit 1
fi

# Load environment variables
export $(cat .env.${ENVIRONMENT} | xargs)

# Create necessary directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p nginx/ssl
mkdir -p grafana/dashboards
mkdir -p prometheus/data
mkdir -p loki/data
mkdir -p elasticsearch/data

# Generate SSL certificates if they don't exist
if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
    echo -e "${YELLOW}Generating SSL certificates...${NC}"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=documentlearning.app"
fi

# Build custom images
echo -e "${YELLOW}Building custom images...${NC}"
docker-compose -f $COMPOSE_FILE build --no-cache

# Pull latest images
echo -e "${YELLOW}Pulling latest images...${NC}"
docker-compose -f $COMPOSE_FILE pull

# Stop existing services
echo -e "${YELLOW}Stopping existing services...${NC}"
docker-compose -f $COMPOSE_FILE down --remove-orphans

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 30

# Check service health
echo -e "${YELLOW}Checking service health...${NC}"
services=("analytics_prod" "grafana_prod" "prometheus_prod" "jaeger_prod")

for service in "${services[@]}"; do
    if docker ps --filter "name=$service" --filter "status=running" | grep -q $service; then
        echo -e "${GREEN}✓ $service is running${NC}"
    else
        echo -e "${RED}✗ $service is not running${NC}"
        docker logs $service --tail 20
    fi
done

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
docker-compose -f $COMPOSE_FILE exec -T analytics npm run migrate

# Update Prometheus configuration
echo -e "${YELLOW}Reloading Prometheus configuration...${NC}"
curl -X POST http://localhost:9090/-/reload || echo "Prometheus reload failed"

# Import Grafana dashboards
echo -e "${YELLOW}Importing Grafana dashboards...${NC}"
sleep 10  # Wait for Grafana to be fully ready
./scripts/import-dashboards.sh

# Run health checks
echo -e "${YELLOW}Running health checks...${NC}"
./scripts/health-check.sh

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}Services available at:${NC}"
echo -e "  Analytics API: https://analytics.documentlearning.app/api"
echo -e "  Monitoring Dashboard: https://analytics.documentlearning.app/dashboard"
echo -e "  Grafana: https://grafana.documentlearning.app"
echo -e "  Jaeger: https://jaeger.documentlearning.app"
echo -e "  Prometheus: http://localhost:9090"