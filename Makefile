.PHONY: help build up down restart logs clean status health test shell-gateway shell-vllm pull push dev prod

# Default target
help: ## Show this help message
	@echo "Edge Computing Docker Commands"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Build Commands
build: ## Build all services
	docker-compose build

build-no-cache: ## Build all services without cache
	docker-compose build --no-cache

build-vllm: ## Build only vLLM service
	docker-compose build vllm

build-gateway: ## Build only gateway service
	docker-compose build gateway

# Runtime Commands
up: ## Start all services in background
	docker-compose up -d

up-logs: ## Start all services with logs
	docker-compose up

down: ## Stop and remove all containers
	docker-compose down

restart: ## Restart all services
	docker-compose restart

stop: ## Stop all services (keep containers)
	docker-compose stop

start: ## Start existing containers
	docker-compose start

# Development Commands
dev: build up ## Build and start for development
	@echo "🚀 Services starting..."
	@echo "📡 vLLM API: http://localhost:8000"
	@echo "🌐 Gateway API: http://localhost:8080"

prod: build-no-cache up ## Build from scratch and start for production

# Log Commands
logs: ## Show logs for all services
	docker-compose logs -f

logs-vllm: ## Show logs for vLLM service
	docker-compose logs -f vllm

logs-gateway: ## Show logs for gateway service
	docker-compose logs -f gateway

logs-tail: ## Show last 100 lines of logs
	docker-compose logs --tail=100

# Status and Health
status: ## Show status of all containers
	docker-compose ps

health: ## Check health of services
	@echo "🔍 Checking service health..."
	@curl -s http://localhost:8080/health || echo "❌ Gateway health check failed"
	@curl -s http://localhost:8000/v1/health || echo "❌ vLLM health check failed"

# Shell Access
shell-gateway: ## Open shell in gateway container
	docker-compose exec gateway /bin/bash

shell-vllm: ## Open shell in vLLM container
	docker-compose exec vllm /bin/bash

# Testing
test: ## Run stress test against the services
	@echo "🧪 Running stress test..."
	cd stress_test && python stress_test.py

test-request: ## Test with sample request
	@echo "📤 Testing sample request..."
	curl -X POST http://localhost:8080/v1/chat/completions \
		-H "Content-Type: application/json" \
		-d @request.json

# Cleanup Commands
clean: down ## Stop services and clean up containers
	docker-compose down --rmi local --volumes --remove-orphans

clean-all: ## Stop services and remove everything (including images)
	docker-compose down --rmi all --volumes --remove-orphans
	docker system prune -a -f

clean-volumes: ## Remove only volumes
	docker-compose down -v

# Monitoring
monitor: ## Monitor container resource usage
	docker stats $(shell docker-compose ps -q)

# Image Management
pull: ## Pull latest base images
	docker-compose pull

push: ## Push images to registry (configure registry first)
	docker-compose push

# Individual Service Management
up-vllm: ## Start only vLLM service
	docker-compose up -d vllm

up-gateway: ## Start only gateway service
	docker-compose up -d gateway

restart-vllm: ## Restart only vLLM service
	docker-compose restart vllm

restart-gateway:
	docker compose build gateway
	docker compose up -d gateway

# Quick Commands
quick-start: build up logs ## Quick start with logs
	@echo "✅ All services started!"

rebuild: down build up ## Full rebuild and restart

# Environment
env-check: ## Check if .env file exists
	@if [ -f .env ]; then echo "✅ .env file found"; else echo "❌ .env file missing - copy .env.example"; fi