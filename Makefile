.PHONY: help install dev-setup test lint format type-check clean docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all dependencies
	cd backend && pip install -e .[dev]
	cd frontend && npm install

dev-setup: install ## Set up development environment
	cd backend && pre-commit install
	@echo "Development environment set up successfully!"

test: ## Run all tests
	cd backend && pytest
	cd frontend && npm run build

lint: ## Run linting for all projects
	cd backend && ruff check .
	cd frontend && npm run lint

format: ## Format code for all projects
	cd backend && black .
	cd backend && ruff check . --fix

type-check: ## Run type checking
	cd backend && mypy .
	cd frontend && npx tsc --noEmit

clean: ## Clean build artifacts
	cd backend && rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
	cd frontend && rm -rf dist/ node_modules/.cache/

docker-up: ## Start development environment with Docker
	cd infrastructure && docker-compose up -d

docker-down: ## Stop development environment
	cd infrastructure && docker-compose down

docker-logs: ## Show Docker logs
	cd infrastructure && docker-compose logs -f

backend-dev: ## Start backend development server
	cd backend && uvicorn main:app --reload

frontend-dev: ## Start frontend development server
	cd frontend && npm run dev