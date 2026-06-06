.PHONY: help deps run test docker-build compose-up

help:
	@echo "Targets: deps run test docker-build compose-up"

deps:
	@echo "Create virtualenv and install requirements (recommended)"
	python3 -m venv .venv
	. .venv/bin/activate && python -m pip install --upgrade pip && python -m pip install -r requirements.txt

run:
	@echo "Run the game using ./scripts/dev_run.sh"
	./scripts/dev_run.sh

test:
	@echo "Run the lightweight tests"
	python3 run_tests.py

docker-build:
	docker build -t ai-roguelike .

compose-up:
	@echo "Start docker-compose stack (ollama placeholder)"
	docker compose up --build
