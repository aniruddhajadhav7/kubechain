# Makefile for KubeChain Platform Development
# Provides automated tasks for environment setup, quality checks, testing, and local services.

.PHONY: help install lint format format-check typecheck test test-unit test-cov up down restart clean docker-build

SHELL := /bin/bash
PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin

# Default target
.DEFAULT_GOAL := help

help: ## Show available Makefile targets with descriptions
	@echo "======================================================================"
	@echo "KubeChain Platform Development Tasks"
	@echo "======================================================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

venv: ## Create virtual environment if it does not exist
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@echo "Virtual environment ready at $(VENV)"

install: venv ## Install project in editable mode with development dependencies
	@$(BIN)/pip install --upgrade pip
	@$(BIN)/pip install -e ".[dev]"
	@test -f .env || cp .env.example .env
	@echo "KubeChain installed in development mode."

lint: ## Run Ruff linter on all codebase files
	@$(BIN)/ruff check .

format: ## Run Ruff formatter to automatically reformat codebase
	@$(BIN)/ruff format .

format-check: ## Check code formatting compliance without modifying files
	@$(BIN)/ruff format --check .

typecheck: ## Run Mypy static type analysis across all packages
	@$(BIN)/mypy core api operator gateway node_manager tests/unit/test_foundation.py

test: ## Run complete automated test suite
	@$(BIN)/pytest --rootdir=.

test-unit: ## Run unit test suite only
	@$(BIN)/pytest --rootdir=. tests/unit

test-cov: ## Run unit tests with code coverage report
	@$(BIN)/pytest --rootdir=. --cov=core --cov=api --cov=operator --cov=gateway --cov=node_manager --cov-report=term-missing tests/unit

up: ## Start local supporting services (Redis) using Docker Compose
	@docker compose up -d
	@echo "Local supporting services started."

down: ## Stop local supporting services using Docker Compose
	@docker compose down
	@echo "Local supporting services stopped."

restart: down up ## Restart local supporting services

docker-build: ## Build container images for operator and gateway
	@docker build -t kubechain-operator:latest -f operator/Dockerfile .
	@docker build -t kubechain-gateway:latest -f gateway/Dockerfile .
	@echo "Container images built successfully."

clean: ## Remove build artifacts, bytecode, and cache directories
	@rm -rf build/ dist/ *.egg-info/ .coverage .pytest_cache/ .mypy_cache/ .ruff_cache/
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "Cleaned build artifacts and cache directories."
