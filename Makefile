.PHONY: help dev test test-unit test-integration test-cov lint load-test seed docker-up docker-down docker-logs clean

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo '$(BLUE)Stories Service - Commands$(NC)'
	@echo ''
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

dev: ## Run API in development mode
	@echo '$(BLUE)Starting development server...$(NC)'
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run all tests
	@echo '$(BLUE)Running all tests...$(NC)'
	PYTHONPATH=. uv run pytest tests/ -v

test-unit: ## Run unit tests only
	@echo '$(BLUE)Running unit tests...$(NC)'
	PYTHONPATH=. uv run pytest tests/unit/ -v -m unit

test-integration: ## Run integration tests only
	@echo '$(BLUE)Running integration tests...$(NC)'
	PYTHONPATH=. uv run pytest tests/integration/ -v -m integration

test-cov: ## Run tests with coverage report
	@echo '$(BLUE)Running tests with coverage...$(NC)'
	PYTHONPATH=. uv run pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
	@echo '$(GREEN)Coverage report: htmlcov/index.html$(NC)'

lint: ## Run linting checks
	@echo '$(BLUE)Running linters...$(NC)'
	@echo '$(YELLOW)Checking with ruff...$(NC)'
	uv run ruff check app/ --fix
	@echo '$(YELLOW)Formatting with ruff...$(NC)'
	uv run ruff format app/
	@echo '$(GREEN)✓ Linting complete$(NC)'

load-test: ## Run load tests
	@echo '$(BLUE)Running load tests...$(NC)'
	./tests/load/create_view_autocannon.sh

seed: ## Seed database with test data
	@echo '$(BLUE)Seeding database...$(NC)'
	uv run python scripts/seed.py

docker-up: ## Start all services with Docker Compose
	@echo '$(BLUE)Starting Docker services...$(NC)'
	docker-compose up -d
	@echo '$(GREEN)✓ Services started$(NC)'
	@echo '$(YELLOW)API: http://localhost:8000$(NC)'
	@echo '$(YELLOW)Docs: http://localhost:8000/docs$(NC)'
	@echo '$(YELLOW)MinIO Console: http://localhost:9001$(NC)'

docker-down: ## Stop all Docker services
	@echo '$(BLUE)Stopping Docker services...$(NC)'
	docker-compose down
	@echo '$(GREEN)✓ Services stopped$(NC)'

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-build: ## Build Docker images
	@echo '$(BLUE)Building Docker images...$(NC)'
	docker-compose build
	@echo '$(GREEN)✓ Build complete$(NC)'

docker-clean: ## Clean Docker volumes and images
	@echo '$(YELLOW)Cleaning Docker resources...$(NC)'
	docker-compose down -v
	docker system prune -f
	@echo '$(GREEN)✓ Cleanup complete$(NC)'

db-migrate: ## Run database migrations
	@echo '$(BLUE)Running migrations...$(NC)'
	docker exec -it stories-postgres psql -U postgres -d stories_db -f /docker-entrypoint-initdb.d/001_create_tables.sql
	docker exec -it stories-postgres psql -U postgres -d stories_db -f /docker-entrypoint-initdb.d/002_create_indexes.sql
	docker exec -it stories-postgres psql -U postgres -d stories_db -f /docker-entrypoint-initdb.d/003_add_search.sql
	@echo '$(GREEN)✓ Migrations complete$(NC)'

db-reset: ## Reset database (WARNING: destroys all data)
	@echo '$(YELLOW)⚠️  This will destroy all data. Are you sure? [y/N]$(NC)' && read ans && [ $${ans:-N} = y ]
	docker-compose down -v postgres
	docker-compose up -d postgres
	sleep 5
	make db-migrate
	@echo '$(GREEN)✓ Database reset complete$(NC)'

clean: ## Clean temporary files
	@echo '$(BLUE)Cleaning temporary files...$(NC)'
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo '$(GREEN)✓ Cleanup complete$(NC)'

install: ## Install dependencies
	@echo '$(BLUE)Installing dependencies...$(NC)'
	uv sync
	@echo '$(GREEN)✓ Installation complete$(NC)'

.DEFAULT_GOAL := help
