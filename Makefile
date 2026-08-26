.PHONY: help test demo ci

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

test: ## Run pytest suite
	python -m pytest tests/ -v

demo: ## Run both fixture analyses (writes results/table.csv in each example dir)
	cd examples/reproducible-paper && python analysis.py
	cd examples/divergent-paper && python analysis.py

ci: test demo ## Run all CI checks (pytest + fixture analyses)
