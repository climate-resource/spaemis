.DEFAULT_GOAL := help

VENV_DIR ?= venv


define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

.PHONY: help
help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

checks: $(VENV_DIR)  ## run all the checks
	@echo "=== bandit ==="; $(VENV_DIR)/bin/bandit -c .bandit.yml -r src || echo "--- bandit failed ---" >&2; \
``		echo "\n\n=== black ==="; $(VENV_DIR)/bin/black --check . || echo "--- black failed ---" >&2; \
``		echo "\n\n=== ruff ==="; $(VENV_DIR)/bin/ruff . || echo "--- ruff failed ---" >&2; \
		echo "\n\n=== tests ==="; $(VENV_DIR)/bin/pytest tests -r a --cov=spaemis --cov-report='' \
			&& $(VENV_DIR)/bin/coverage report --fail-under=95 || echo "--- tests failed ---" >&2; \
		echo

.PHONY: format
format: black ruff  ## re-format files

.PHONY: black
black: $(VENV_DIR)  ## apply black formatter to source and tests
	$(VENV_DIR)/bin/black .

.PHONY: ruff
ruff: $(VENV_DIR)  ## apply ruff fixes
	$(VENV_DIR)/bin/ruff --fix .

.PHONY: test
test:  $(VENV_DIR) ## run the full testsuite
	$(VENV_DIR)/bin/pytest tests --cov -rfsxEX --cov-report term-missing

.PHONY: virtual-environment
virtual-environment: $(VENV_DIR) ## update venv, create a new venv if it doesn't exist

$(VENV_DIR): setup.py setup.cfg pyproject.toml
	[ -d $(VENV_DIR) ] || python3 -m venv $(VENV_DIR)

	$(VENV_DIR)/bin/pip install --upgrade pip wheel
	$(VENV_DIR)/bin/pip install -e .[dev]
	$(VENV_DIR)/bin/jupyter nbextension enable --py widgetsnbextension

	touch $(VENV_DIR)

build: src/spaemis_glo
	$(MAKE) -c src/spaemis_glo build