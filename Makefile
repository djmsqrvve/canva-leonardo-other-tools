SHELL := /usr/bin/env bash

PYTHON := ./dj_msqrvve_brand_system/venv/bin/python
CLI_DIR := ./dj_msqrvve_brand_system
DASHBOARD_DIR := ./dashboard

.PHONY: status cli-help test test-verbose dashboard-lint health full-check

status:
	git status --short --branch

cli-help:
	cd $(CLI_DIR) && PYTHONPATH=src ./venv/bin/python src/main.py --help

test:
	$(PYTHON) -m pytest

test-verbose:
	$(PYTHON) -m pytest -vv

dashboard-lint:
	@if ! command -v npm >/dev/null 2>&1; then \
		echo "npm is required for dashboard lint (install Node.js 18+)."; \
		exit 1; \
	fi
	cd $(DASHBOARD_DIR) && npm run lint

health: status cli-help test
	@echo "Health checks passed."

full-check: health dashboard-lint
	@echo "Full checks passed."
