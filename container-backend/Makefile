# Makefile for dad-pass container backend
# Commands for development, testing, and deployment

# Default values (can be overridden via environment variables)
CONTAINER_SERVICE_URL ?= http://localhost:5001
PORT ?= 5001
PYTHONPATH := $(shell pwd)/src:$(PYTHONPATH)

.EXPORT_ALL_VARIABLES:

.PHONY: help install test test-unit test-integration run clean

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make run              - Run the Flask development server"
	@echo "  make clean            - Clean up cache files"

install:
	pip install -r src/requirements.txt
	pip install -r tests/requirements.txt

test: test-unit

test-unit:
	PYTHONPATH=$(PYTHONPATH) pytest tests/unit/ -v

test-integration:
	CONTAINER_SERVICE_URL=$(CONTAINER_SERVICE_URL) pytest tests/integration/ -v

run:
	cd src && python app.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
