include .env
include alembic/Makefile

DOCKER_COMPOSE=docker compose
DOCKER_COMPOSE_RUN=$(DOCKER_COMPOSE) run --rm bot

build:
	env DOCKER_BUILDKIT=1 $(DOCKER_COMPOSE) build --parallel

up: build
	$(DOCKER_COMPOSE) up -d
	docker system prune -a --volumes --force

up_local: build
	$(DOCKER_COMPOSE) up

restart_bot:
	docker compose up -d --build bot

lint:
	uv run pre-commit run --all-files

format:
	uv run isort .
	uv run black .

flake:
	flake8 --per-file-ignores="__init__.py:F401" --ignore E203,E501,W503 src tests bot.py

mypy:
	uv run mypy src bot.py
