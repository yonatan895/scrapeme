# Fix docker-compose filename references to .yaml
# Add load-run target for Locust headless execution
# Improve docker-prepare messaging regarding config/sites.yaml

.PHONY: load-run compose-down compose-logs compose-ps compose-clean docker-prepare

load-run: ## Run Locust headless with sensible defaults (override with LOAD_BASE_URL, USERS, SPAWN, DURATION)
	@USERS=$${USERS:-30}; \
	SPAWN=$${SPAWN:-3}; \
	DURATION=$${DURATION:-1m}; \
	printf 'Running Locust: users=%s spawn=%s duration=%s host=%s\n' "$$USERS" "$$SPAWN" "$$DURATION" "$$LOAD_BASE_URL"; \
	. $(VENV_BIN)/activate 2>/dev/null || true; \
	command -v locust >/dev/null 2>&1 || { \
		printf 'Locust not found, installing...\n'; \
		$(UV) pip install -e ".[load]"; \
	}; \
	locust -f tests/load/locustfile.py --headless -u "$$USERS" -r "$$SPAWN" -t "$$DURATION"

compose-down: ## Stop Docker Compose stack
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml down
	@printf '$(GREEN)✅ Docker Compose stack stopped$(NC)\n'

compose-logs: ## View Docker Compose logs (live)
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml logs -f

compose-ps: ## Show running Docker Compose containers
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml ps

compose-clean: compose-down ## Stop and remove volumes
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml down -v
	@printf '$(GREEN)✅ Docker Compose cleaned (volumes removed)$(NC)\n'

docker-prepare: ## Prepare directories for Docker
	@printf '$(YELLOW)Preparing Docker volumes...$(NC)\n'
	@mkdir -p results artifacts config
	@chmod 755 results artifacts || true
	@if [ ! -f "config/sites.yaml" ]; then \
		printf '$(YELLOW)⚠️  config/sites.yaml not found$(NC)\n'; \
		printf 'Create one based on the example at $(BLUE)config/sites.yaml$(NC) (already committed example)\n'; \
	fi
	@printf '$(GREEN)✅ Docker volumes ready$(NC)\n'
