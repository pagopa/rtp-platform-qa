.PHONY: help install install-dev install-functional install-bdd install-ux install-performance install-contract \
	    test-functional test-bdd test-ux test-contract precommit

help:
	@echo "Targets:"
	@echo "  install               Install core"
	@echo "  install-dev           Install dev tools"
	@echo "  install-functional    Install functional test deps"
	@echo "  install-bdd           Install BDD test deps"
	@echo "  install-ux            Install UX test deps"
	@echo "  install-performance   Install performance test deps"
	@echo "  install-contract      Install contract test deps"
	@echo "  test-functional       Run functional tests"
	@echo "  test-bdd              Run BDD tests (behave)"
	@echo "  test-ux               Run UX tests (pytest + Playwright)"
	@echo "  test-contract         Run contract tests"
	@echo "  precommit             Run pre-commit on all files"

install:
	python -m pip install -U pip
	pip install -e .

install-dev:
	pip install -e .[dev]

install-functional:
	pip install -e .[functional-tests]

install-bdd:
	pip install -e .[bdd-tests]

install-ux:
	pip install -e .[ux-tests]
	python -m playwright install

install-performance:
	pip install -e .[performance-tests]

install-contract:
	pip install -e .[contract-tests]

test-functional:
	pytest functional-tests/tests/ -q

test-bdd:
	behave bdd-tests/features/

test-ux:
	pytest ux-tests/tests/ -q

test-contract:
	pytest contract-tests/ -q

precommit:
	pre-commit run --all-files

check-env:
	@test -f .env || (echo ".env not found. Copy .env.example to .env and fill values." && exit 1)