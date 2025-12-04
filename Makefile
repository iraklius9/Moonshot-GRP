.PHONY: help run test lint docker-build docker-up docker-down docker-logs clean install

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

run: ## Run the service locally
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run pytest tests with coverage
	pytest tests/

lint: ## Run flake8 linter
	flake8 app/ tests/

docker-build: ## Build Docker image
	docker compose build

docker-up: ## Start services with docker compose
	docker compose up -d

docker-down: ## Stop services with docker compose
	docker compose down

docker-logs: ## View docker compose logs
	docker compose logs -f

docker-restart: ## Restart services
	docker compose restart

clean: ## Clean Python cache files and __pycache__ directories
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -r {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ .pytest_cache/ dist/ build/

