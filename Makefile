.PHONY: help setup run backend frontend stop clean test lint type-check install-deps build docker-up docker-down

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

# Directories
BACKEND_DIR := backend
FRONTEND_DIR := frontend
VENV_DIR := $(BACKEND_DIR)/venv

# Python and Node commands
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
ACTIVATE := source $(VENV_DIR)/bin/activate

# Defaults
BACKEND_PORT ?= 8001
FRONTEND_PORT ?= 3000

help: ## Show this help message
	@echo "$(BLUE)Copilot CLI Web UI - Make Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Examples:$(NC)"
	@echo "  make setup              # Initial setup"
	@echo "  make run                # Run both backend and frontend"
	@echo "  make stop               # Stop all services"
	@echo "  make clean              # Clean build artifacts"
	@echo ""

# ============================================================================
# Setup Commands
# ============================================================================

setup: ## Run automated setup script
	@echo "$(BLUE)Running setup script...$(NC)"
	@bash setup.sh
	@echo "$(GREEN)Setup complete!$(NC)"

install-deps: ## Install Python and Node dependencies
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	$(PIP) install -r $(BACKEND_DIR)/requirements.txt
	@echo "$(GREEN)Python dependencies installed$(NC)"
	@echo ""
	@echo "$(BLUE)Installing Node dependencies...$(NC)"
	cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)Node dependencies installed$(NC)"

# ============================================================================
# Development Commands
# ============================================================================

run: backend frontend ## Run both backend and frontend servers

backend: ## Run FastAPI backend server on port 8001
	@echo "$(BLUE)Starting backend server on port $(BACKEND_PORT)...$(NC)"
	@echo "$(GREEN)✓ Backend running on http://localhost:$(BACKEND_PORT)$(NC)"
	@echo "$(GREEN)✓ API docs available at http://localhost:$(BACKEND_PORT)/docs$(NC)"
	@cd $(BACKEND_DIR) && \
	$(VENV_DIR)/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

frontend: ## Run Next.js frontend development server on port 3000
	@echo "$(BLUE)Starting frontend server on port $(FRONTEND_PORT)...$(NC)"
	@echo "$(GREEN)✓ Frontend running on http://localhost:$(FRONTEND_PORT)$(NC)"
	cd $(FRONTEND_DIR) && npm run dev

backend-bg: ## Run backend server in background
	@echo "$(BLUE)Starting backend server in background...$(NC)"
	@cd $(BACKEND_DIR) && \
	$(VENV_DIR)/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT) > backend.log 2>&1 &
	@echo "$(GREEN)Backend started (logs in backend.log)$(NC)"

frontend-bg: ## Run frontend server in background
	@echo "$(BLUE)Starting frontend server in background...$(NC)"
	@cd $(FRONTEND_DIR) && npm run dev > frontend.log 2>&1 &
	@echo "$(GREEN)Frontend started (logs in frontend.log)$(NC)"

stop: ## Stop all running services
	@echo "$(BLUE)Stopping services...$(NC)"
	@pkill -f "uvicorn src.main:app" || true
	@pkill -f "next dev" || true
	@echo "$(GREEN)All services stopped$(NC)"

# ============================================================================
# Testing and Quality Commands
# ============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@cd $(BACKEND_DIR) && $(PYTHON) -m pytest -v
	@cd $(FRONTEND_DIR) && npm run test
	@echo "$(GREEN)All tests passed$(NC)"

test-backend: ## Run backend tests only
	@echo "$(BLUE)Running backend tests...$(NC)"
	@cd $(BACKEND_DIR) && $(PYTHON) -m pytest -v --cov=src --cov-report=html
	@echo "$(GREEN)Backend tests complete$(NC)"
	@echo "$(BLUE)Coverage report: $(BACKEND_DIR)/htmlcov/index.html$(NC)"

test-frontend: ## Run frontend tests only
	@echo "$(BLUE)Running frontend tests...$(NC)"
	@cd $(FRONTEND_DIR) && npm run test
	@echo "$(GREEN)Frontend tests complete$(NC)"

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint Python code
	@echo "$(BLUE)Linting backend code...$(NC)"
	@cd $(BACKEND_DIR) && $(PYTHON) -m flake8 src --max-line-length=100
	@cd $(BACKEND_DIR) && $(PYTHON) -m black src --check
	@echo "$(GREEN)Backend lint passed$(NC)"

lint-frontend: ## Lint TypeScript/JavaScript code
	@echo "$(BLUE)Linting frontend code...$(NC)"
	@cd $(FRONTEND_DIR) && npm run lint
	@echo "$(GREEN)Frontend lint passed$(NC)"

type-check: ## Run type checkers
	@echo "$(BLUE)Running type checks...$(NC)"
	@cd $(BACKEND_DIR) && $(PYTHON) -m mypy src --ignore-missing-imports
	@cd $(FRONTEND_DIR) && npm run type-check
	@echo "$(GREEN)Type checking passed$(NC)"

format: ## Auto-format code
	@echo "$(BLUE)Formatting code...$(NC)"
	@cd $(BACKEND_DIR) && $(PYTHON) -m black src
	@cd $(BACKEND_DIR) && $(PYTHON) -m isort src
	@cd $(FRONTEND_DIR) && npm run lint -- --fix
	@echo "$(GREEN)Code formatted$(NC)"

# ============================================================================
# Build Commands
# ============================================================================

build: build-backend build-frontend ## Build for production

build-backend: ## Build backend Docker image
	@echo "$(BLUE)Building backend Docker image...$(NC)"
	@docker build -t copilot-backend:latest $(BACKEND_DIR)
	@echo "$(GREEN)Backend image built$(NC)"

build-frontend: ## Build frontend Docker image
	@echo "$(BLUE)Building frontend Docker image...$(NC)"
	@docker build -t copilot-frontend:latest $(FRONTEND_DIR)
	@echo "$(GREEN)Frontend image built$(NC)"

# ============================================================================
# Docker Commands
# ============================================================================

docker-up: ## Start services with Docker Compose
	@echo "$(BLUE)Starting Docker services...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)Docker services started$(NC)"
	@echo "$(GREEN)Backend: http://localhost:8000$(NC)"
	@echo "$(GREEN)Frontend: http://localhost:3000$(NC)"

docker-down: ## Stop Docker services
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)Docker services stopped$(NC)"

docker-logs: ## View Docker service logs
	@docker-compose logs -f

docker-rebuild: ## Rebuild Docker images
	@echo "$(BLUE)Rebuilding Docker images...$(NC)"
	@docker-compose build --no-cache
	@echo "$(GREEN)Docker images rebuilt$(NC)"

# ============================================================================
# Cleanup Commands
# ============================================================================

clean: clean-backend clean-frontend clean-docker ## Clean all build artifacts and caches

clean-backend: ## Clean backend build artifacts
	@echo "$(BLUE)Cleaning backend...$(NC)"
	@cd $(BACKEND_DIR) && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@cd $(BACKEND_DIR) && find . -type f -name "*.pyc" -delete
	@cd $(BACKEND_DIR) && rm -rf .pytest_cache htmlcov .coverage $(BACKEND_DIR)/*.egg-info
	@echo "$(GREEN)Backend cleaned$(NC)"

clean-frontend: ## Clean frontend build artifacts
	@echo "$(BLUE)Cleaning frontend...$(NC)"
	@cd $(FRONTEND_DIR) && rm -rf .next out node_modules/.cache
	@echo "$(GREEN)Frontend cleaned$(NC)"

clean-docker: ## Clean Docker images and volumes
	@echo "$(BLUE)Cleaning Docker...$(NC)"
	@docker-compose down -v 2>/dev/null || true
	@docker image prune -f 2>/dev/null || true
	@echo "$(GREEN)Docker cleaned$(NC)"

clean-all: clean ## Deep clean including dependencies
	@echo "$(BLUE)Performing deep clean...$(NC)"
	@rm -rf $(VENV_DIR)
	@cd $(FRONTEND_DIR) && rm -rf node_modules package-lock.json
	@echo "$(GREEN)Deep clean complete$(NC)"

# ============================================================================
# Utility Commands
# ============================================================================

status: ## Show service status
	@echo "$(BLUE)Service Status$(NC)"
	@echo ""
	@ps aux | grep -E "(uvicorn|next)" | grep -v grep || echo "No services running"
	@echo ""
	@echo "Check ports:"
	@lsof -i :8001 || echo "Backend (8001): Not running"
	@lsof -i :3000 || echo "Frontend (3000): Not running"

logs-backend: ## View backend logs in real-time
	@tail -f backend.log

logs-frontend: ## View frontend logs in real-time
	@tail -f frontend.log

check-ports: ## Check if development ports are available
	@echo "$(BLUE)Checking ports...$(NC)"
	@echo "Backend port (8001):"
	@lsof -i :8001 || echo "  ✓ Available"
	@echo "Frontend port (3000):"
	@lsof -i :3000 || echo "  ✓ Available"

version: ## Show component versions
	@echo "$(BLUE)Version Info$(NC)"
	@echo "Python: $$(python3 --version)"
	@echo "Node.js: $$(node --version)"
	@echo "npm: $$(npm --version)"
	@echo "Docker: $$(docker --version)"

.DEFAULT_GOAL := help
