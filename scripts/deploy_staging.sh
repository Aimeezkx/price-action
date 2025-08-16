#!/bin/bash
"""
Staging environment deployment script for automated testing pipeline.
Sets up isolated staging environment for integration testing.
"""

set -e  # Exit on any error

# Configuration
STAGING_ENV_NAME="${STAGING_ENV_NAME:-staging}"
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-infrastructure/staging-environment.yml}"
DATABASE_NAME="${DATABASE_NAME:-testdb_staging}"
REDIS_DB="${REDIS_DB:-1}"
STAGING_PORT_BACKEND="${STAGING_PORT_BACKEND:-8001}"
STAGING_PORT_FRONTEND="${STAGING_PORT_FRONTEND:-3001}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Clean up existing staging environment
cleanup_staging() {
    log_info "Cleaning up existing staging environment..."
    
    # Stop and remove containers
    docker-compose -f "$DOCKER_COMPOSE_FILE" -p "$STAGING_ENV_NAME" down --volumes --remove-orphans 2>/dev/null || true
    
    # Remove staging network if exists
    docker network rm "${STAGING_ENV_NAME}_default" 2>/dev/null || true
    
    # Clean up any dangling volumes
    docker volume prune -f 2>/dev/null || true
    
    log_success "Staging environment cleaned up"
}

# Create staging environment configuration
create_staging_config() {
    log_info "Creating staging environment configuration..."
    
    # Create staging directory if it doesn't exist
    mkdir -p infrastructure/staging
    
    # Generate staging environment file
    cat > infrastructure/staging/.env << EOF
# Staging Environment Configuration
ENVIRONMENT=staging
DEBUG=true

# Database Configuration
DATABASE_URL=postgresql://postgres:stagingpass@postgres-staging:5432/${DATABASE_NAME}
POSTGRES_DB=${DATABASE_NAME}
POSTGRES_USER=postgres
POSTGRES_PASSWORD=stagingpass

# Redis Configuration
REDIS_URL=redis://redis-staging:6379/${REDIS_DB}

# Application Configuration
BACKEND_PORT=${STAGING_PORT_BACKEND}
FRONTEND_PORT=${STAGING_PORT_FRONTEND}
API_BASE_URL=http://localhost:${STAGING_PORT_BACKEND}

# Security Configuration (relaxed for testing)
SECRET_KEY=staging-secret-key-not-for-production
CORS_ORIGINS=http://localhost:${STAGING_PORT_FRONTEND},http://127.0.0.1:${STAGING_PORT_FRONTEND}

# File Storage
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=100MB

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=/app/logs/staging.log

# Testing Configuration
TESTING_MODE=true
SKIP_AUTH=false
MOCK_EXTERNAL_APIS=true
EOF
    
    log_success "Staging configuration created"
}

# Create Docker Compose file for staging
create_docker_compose() {
    log_info "Creating Docker Compose configuration for staging..."
    
    cat > "$DOCKER_COMPOSE_FILE" << 'EOF'
version: '3.8'

services:
  postgres-staging:
    image: postgres:15
    container_name: postgres-staging
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5433:5432"
    volumes:
      - postgres_staging_data:/var/lib/postgresql/data
      - ./backend/alembic/versions:/docker-entrypoint-initdb.d/migrations
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - staging-network

  redis-staging:
    image: redis:7-alpine
    container_name: redis-staging
    ports:
      - "6380:6379"
    volumes:
      - redis_staging_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - staging-network

  backend-staging:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: backend-staging
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - ENVIRONMENT=${ENVIRONMENT}
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - UPLOAD_DIR=${UPLOAD_DIR}
      - MAX_FILE_SIZE=${MAX_FILE_SIZE}
      - LOG_LEVEL=${LOG_LEVEL}
      - TESTING_MODE=${TESTING_MODE}
      - MOCK_EXTERNAL_APIS=${MOCK_EXTERNAL_APIS}
    ports:
      - "${BACKEND_PORT}:8000"
    volumes:
      - ./backend:/app
      - staging_uploads:/app/uploads
      - staging_logs:/app/logs
    depends_on:
      postgres-staging:
        condition: service_healthy
      redis-staging:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - staging-network
    restart: unless-stopped

  frontend-staging:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: frontend-staging
    environment:
      - VITE_API_BASE_URL=${API_BASE_URL}
      - VITE_ENVIRONMENT=${ENVIRONMENT}
    ports:
      - "${FRONTEND_PORT}:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend-staging
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - staging-network
    restart: unless-stopped

  nginx-staging:
    image: nginx:alpine
    container_name: nginx-staging
    ports:
      - "8080:80"
    volumes:
      - ./infrastructure/staging/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend-staging
      - frontend-staging
    networks:
      - staging-network
    restart: unless-stopped

volumes:
  postgres_staging_data:
  redis_staging_data:
  staging_uploads:
  staging_logs:

networks:
  staging-network:
    driver: bridge
EOF
    
    log_success "Docker Compose configuration created"
}

# Create Nginx configuration for staging
create_nginx_config() {
    log_info "Creating Nginx configuration for staging..."
    
    mkdir -p infrastructure/staging
    
    cat > infrastructure/staging/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend-staging:8000;
    }
    
    upstream frontend {
        server frontend-staging:3000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # Frontend routes
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # API routes
        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            # Handle large file uploads
            client_max_body_size 100M;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }
        
        # Health check endpoint
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }
    }
}
EOF
    
    log_success "Nginx configuration created"
}

# Deploy staging environment
deploy_staging() {
    log_info "Deploying staging environment..."
    
    # Load environment variables
    set -a
    source infrastructure/staging/.env
    set +a
    
    # Build and start services
    docker-compose -f "$DOCKER_COMPOSE_FILE" -p "$STAGING_ENV_NAME" build --no-cache
    docker-compose -f "$DOCKER_COMPOSE_FILE" -p "$STAGING_ENV_NAME" up -d
    
    log_success "Staging environment deployed"
}

# Wait for services to be healthy
wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts"
        
        # Check backend health
        if curl -f "http://localhost:${STAGING_PORT_BACKEND}/health" &>/dev/null; then
            log_success "Backend is healthy"
            backend_healthy=true
        else
            backend_healthy=false
        fi
        
        # Check frontend health
        if curl -f "http://localhost:${STAGING_PORT_FRONTEND}" &>/dev/null; then
            log_success "Frontend is healthy"
            frontend_healthy=true
        else
            frontend_healthy=false
        fi
        
        # Check if all services are healthy
        if [ "$backend_healthy" = true ] && [ "$frontend_healthy" = true ]; then
            log_success "All services are healthy"
            return 0
        fi
        
        log_info "Services not ready yet, waiting 10 seconds..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Services failed to become healthy within timeout"
    return 1
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for database to be ready
    sleep 5
    
    # Run migrations in backend container
    docker-compose -f "$DOCKER_COMPOSE_FILE" -p "$STAGING_ENV_NAME" exec -T backend-staging \
        python -m alembic upgrade head
    
    log_success "Database migrations completed"
}

# Seed test data
seed_test_data() {
    log_info "Seeding test data..."
    
    # Run test data seeding script
    if [ -f "scripts/seed_staging_data.py" ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" -p "$STAGING_ENV_NAME" exec -T backend-staging \
            python /app/scripts/seed_staging_data.py
        log_success "Test data seeded"
    else
        log_warning "Test data seeding script not found, skipping"
    fi
}

# Display deployment information
show_deployment_info() {
    log_success "Staging environment deployed successfully!"
    echo
    echo "=== Staging Environment Information ==="
    echo "Backend URL:    http://localhost:${STAGING_PORT_BACKEND}"
    echo "Frontend URL:   http://localhost:${STAGING_PORT_FRONTEND}"
    echo "Nginx Proxy:    http://localhost:8080"
    echo "Database:       localhost:5433 (${DATABASE_NAME})"
    echo "Redis:          localhost:6380"
    echo
    echo "=== Useful Commands ==="
    echo "View logs:      docker-compose -f $DOCKER_COMPOSE_FILE -p $STAGING_ENV_NAME logs -f"
    echo "Stop services:  docker-compose -f $DOCKER_COMPOSE_FILE -p $STAGING_ENV_NAME down"
    echo "Restart:        docker-compose -f $DOCKER_COMPOSE_FILE -p $STAGING_ENV_NAME restart"
    echo
}

# Main deployment function
main() {
    log_info "Starting staging environment deployment..."
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --cleanup-only)
                cleanup_staging
                exit 0
                ;;
            --no-cleanup)
                skip_cleanup=true
                shift
                ;;
            --no-seed)
                skip_seed=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --cleanup-only    Only cleanup existing staging environment"
                echo "  --no-cleanup      Skip cleanup of existing environment"
                echo "  --no-seed         Skip test data seeding"
                echo "  --help            Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Execute deployment steps
    check_prerequisites
    
    if [ "$skip_cleanup" != true ]; then
        cleanup_staging
    fi
    
    create_staging_config
    create_docker_compose
    create_nginx_config
    deploy_staging
    
    if wait_for_services; then
        run_migrations
        
        if [ "$skip_seed" != true ]; then
            seed_test_data
        fi
        
        show_deployment_info
    else
        log_error "Staging deployment failed - services are not healthy"
        
        # Show logs for debugging
        log_info "Showing service logs for debugging:"
        docker-compose -f "$DOCKER_COMPOSE_FILE" -p "$STAGING_ENV_NAME" logs --tail=50
        
        exit 1
    fi
}

# Run main function
main "$@"