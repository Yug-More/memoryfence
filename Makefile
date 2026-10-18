.DEFAULT_GOAL := help
UV ?= uv
MERMAID_CLI ?= @mermaid-js/mermaid-cli@12.0.0
MERMAID_FILES = $(shell grep -l --include='*.md' -r '^```mermaid' README.md docs)

.PHONY: help setup lint format format-check typecheck test coverage build citation contracts pre-commit diagrams check clean

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

setup: ## Create the virtual environment from uv.lock and install git hooks
	$(UV) sync --frozen
	$(UV) run --frozen pre-commit install

lint: ## Run Ruff lint rules
	$(UV) run --frozen ruff check .

format: ## Apply Ruff formatting and safe lint fixes
	$(UV) run --frozen ruff format .
	$(UV) run --frozen ruff check --fix .

format-check: ## Verify formatting without modifying files
	$(UV) run --frozen ruff format --check .

typecheck: ## Run mypy in strict mode
	$(UV) run --frozen mypy

test: ## Run the test suite
	$(UV) run --frozen pytest

coverage: ## Run the test suite with branch coverage (fails below 90%)
	$(UV) run --frozen pytest --cov --cov-report=term-missing

build: ## Build the sdist and wheel into dist/ and validate their metadata
	rm -rf dist
	$(UV) build
	$(UV) run --frozen twine check --strict dist/*

citation: ## Validate CITATION.cff against the Citation File Format schema
	$(UV) run --frozen check-jsonschema --builtin-schema vendor.citation-file-format CITATION.cff

contracts: ## Enforce import contracts
	$(UV) run --frozen lint-imports

pre-commit: ## Run all pre-commit hooks against all files
	$(UV) run --frozen pre-commit run --all-files

diagrams: ## Render every Mermaid diagram with mermaid-cli (requires Node.js and network access)
	@mkdir -p .diagrams
	@echo '{"args": ["--no-sandbox"]}' > .diagrams/puppeteer.json
	@for f in $(MERMAID_FILES); do \
		echo "Rendering $$f"; \
		npx --yes $(MERMAID_CLI) --quiet -p .diagrams/puppeteer.json -i "$$f" -o ".diagrams/$$(echo "$$f" | tr / _)" || exit 1; \
	done

check: lint format-check typecheck coverage build citation contracts ## Run the checks of the CI quality job

clean: ## Remove caches and build artifacts
	rm -rf build dist .diagrams .mypy_cache .pytest_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
