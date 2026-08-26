PYTHON ?= python3

.PHONY: help setup test demo ci

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: ## Install dev dependencies
	$(PYTHON) -m pip install -r requirements-dev.txt

test: setup ## Run pytest suite
	$(PYTHON) -m pytest tests/ -v

demo: ## Run both fixture analyses (writes results/table.csv in each example dir)
	cd examples/reproducible-paper && $(PYTHON) analysis.py
	cd examples/divergent-paper && $(PYTHON) analysis.py

ci: test demo ## Run all CI checks (pytest + fixture analyses)
