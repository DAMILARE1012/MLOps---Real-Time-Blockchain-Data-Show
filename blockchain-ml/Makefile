.PHONY: help install install-dev test lint format clean docker-build docker-run docker-stop

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

test:  ## Run tests with coverage
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-unit:  ## Run unit tests only
	pytest tests/unit/ -v

test-integration:  ## Run integration tests only
	pytest tests/integration/ -v

test-e2e:  ## Run end-to-end tests only
	pytest tests/e2e/ -v

lint:  ## Run linting tools
	flake8 src/ tests/
	mypy src/
	black --check src/ tests/
	isort --check-only src/ tests/

format:  ## Format code
	black src/ tests/
	isort src/ tests/

clean:  ## Clean up Python cache files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

docker-build:  ## Build Docker image
	docker build -t blockchain-ml .

docker-run:  ## Run Docker containers (development)
	docker-compose up -d

docker-run-prod:  ## Run Docker containers (production)
	docker-compose -f docker-compose.prod.yml up -d

docker-stop:  ## Stop Docker containers
	docker-compose down

docker-stop-prod:  ## Stop Docker containers (production)
	docker-compose -f docker-compose.prod.yml down

docker-logs:  ## Show Docker logs
	docker-compose logs -f

setup-db:  ## Setup database
	python scripts/setup_database.py

run-pipeline:  ## Run data pipeline
	python -m src.data_pipeline.main

run-api:  ## Run API server
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-training:  ## Run model training
	python -m src.models.train

monitor:  ## Start monitoring
	python -m src.monitoring.main 